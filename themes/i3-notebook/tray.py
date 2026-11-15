"""StatusNotifier tray for Notebook, including applications without open windows.

XEmbed icons continue to use Polybar's tray. This host implements the D-Bus
StatusNotifier protocol used by AppIndicator, Steam and KDE Connect.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time

WATCHER = "org.kde.StatusNotifierWatcher"
WATCHER_PATH = "/StatusNotifierWatcher"
ITEM = "org.kde.StatusNotifierItem"
DBUSMENU = "com.canonical.dbusmenu"
DAEMON = "org.darfinos.NotebookTray"
ACCENT = "{{ .accent }}"
BUS_NAME = re.compile(r"(?::[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+|[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)+)\Z")
OBJECT_PATH = re.compile(r"/(?:[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*)?\Z")
WATCHER_XML = f"""<node><interface name="{WATCHER}">
  <method name="RegisterStatusNotifierItem"><arg type="s" direction="in"/></method>
  <method name="RegisterStatusNotifierHost"><arg type="s" direction="in"/></method>
  <property name="RegisteredStatusNotifierItems" type="as" access="read"/>
  <property name="IsStatusNotifierHostRegistered" type="b" access="read"/>
  <property name="ProtocolVersion" type="i" access="read"/>
  <signal name="StatusNotifierItemRegistered"><arg type="s"/></signal>
  <signal name="StatusNotifierItemUnregistered"><arg type="s"/></signal>
  <signal name="StatusNotifierHostRegistered"/>
  <signal name="StatusNotifierHostUnregistered"/>
</interface></node>"""


@dataclass(frozen=True)
class Address:
    service: str
    path: str

    @property
    def key(self):
        return self.service + self.path


def address(value, sender=None):
    if not isinstance(value, str) or len(value) > 2304:
        raise ValueError("Identificador de bandeja inválido.")
    if value.startswith("/"):
        service, path = sender, value
    else:
        service, separator, suffix = value.partition("/")
        path = "/" + suffix if separator else "/StatusNotifierItem"
    if (not isinstance(service, str) or len(service) > 255 or not BUS_NAME.fullmatch(service)
            or len(path) > 2048 or not OBJECT_PATH.fullmatch(path)):
        raise ValueError("Identificador de bandeja inválido.")
    return Address(service, path)


class Registry:
    """Registration and owner lifetime rules, independent of GTK or D-Bus."""
    def __init__(self):
        self.items = {}

    def register(self, value, sender, resolve):
        target = address(value, sender)
        owner = resolve(target.service)
        if not owner or owner != sender:
            raise ValueError("O aplicativo não é dono deste serviço.")
        fresh = target.key not in self.items
        self.items[target.key] = (target, owner)
        return target.key if fresh else None

    def owner_changed(self, name, old, new):
        if not old or old == new:
            return []
        removed = [key for key, (target, owner) in self.items.items()
                   if target.service == name or (name.startswith(":") and owner == old)]
        for key in removed:
            del self.items[key]
        return removed


def unpack(value):
    if hasattr(value, "unpack"):
        return unpack(value.unpack())
    if isinstance(value, dict):
        return {key: unpack(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [unpack(item) for item in value]
    return value


def plain(value, maximum=120):
    return " ".join("".join(c if c.isprintable() else " " for c in str(value)).split())[:maximum]


def menu_nodes(layout, depth=0, budget=None):
    """Keep DBusMenu hierarchy and state; discard invisible/malformed entries."""
    budget = [512] if budget is None else budget
    if depth > 8 or budget[0] <= 0 or not isinstance(layout, (tuple, list)) or len(layout) != 3:
        return None
    identifier, properties, children = layout
    if not isinstance(identifier, int) or not isinstance(properties, dict) or properties.get("visible", True) is False:
        return None
    budget[0] -= 1
    descendants = []
    for child in children if isinstance(children, (tuple, list)) else []:
        if node := menu_nodes(unpack(child), depth + 1, budget):
            descendants.append(node)
    return {"id": identifier, "label": plain(properties.get("label", "")),
            "separator": properties.get("type") == "separator",
            "enabled": properties.get("enabled", True) is not False,
            "submenu": properties.get("children-display") == "submenu",
            "toggle": properties.get("toggle-type") if properties.get("toggle-type") in ("checkmark", "radio") else None,
            "state": properties.get("toggle-state", 0), "children": descendants}


def icon_pixels(pixmaps, size=24):
    candidates = []
    for entry in pixmaps if isinstance(pixmaps, (tuple, list)) else []:
        if not isinstance(entry, (tuple, list)) or len(entry) != 3:
            continue
        width, height, data = entry
        if not isinstance(width, int) or not isinstance(height, int) or not (0 < width <= 256 and 0 < height <= 256):
            continue
        try:
            raw = bytes(data)
        except (TypeError, ValueError):
            continue
        if len(raw) != width * height * 4:
            continue
        candidates.append((abs(max(width, height) - size), width, height, raw))
    if not candidates:
        return None
    _, width, height, raw = min(candidates)
    rgba = bytearray(len(raw))
    for offset in range(0, len(raw), 4):
        rgba[offset:offset + 4] = raw[offset + 1:offset + 4] + raw[offset:offset + 1]
    return width, height, bytes(rgba)


def dbus():
    from gi.repository import Gio, GLib
    return Gio, GLib, Gio.bus_get_sync(Gio.BusType.SESSION, None)


def call(bus, service, path, interface, method, parameters=None, timeout=700):
    from gi.repository import Gio
    return unpack(bus.call_sync(service, path, interface, method, parameters, None,
                                Gio.DBusCallFlags.NONE, timeout, None))


def registered(bus):
    from gi.repository import GLib
    try:
        result = call(bus, WATCHER, WATCHER_PATH, "org.freedesktop.DBus.Properties", "Get",
                      GLib.Variant("(ss)", (WATCHER, "RegisteredStatusNotifierItems")))
        return [address(value) for value in result[0]][:64]
    except (GLib.Error, ValueError, TypeError, IndexError):
        return []


def item_properties(bus, target):
    from gi.repository import GLib
    try:
        result = call(bus, target.service, target.path, "org.freedesktop.DBus.Properties", "GetAll",
                      GLib.Variant("(s)", (ITEM,)))
        return result[0] if result and isinstance(result[0], dict) else None
    except GLib.Error:
        return None


def daemon():
    Gio, GLib, bus = dbus()
    # RequestName with DO_NOT_QUEUE keeps i3 restarts from creating new hosts.
    owned = call(bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                 "RequestName", GLib.Variant("(su)", (DAEMON, 4)))
    if owned[0] not in (1, 4):
        return 0
    registry = Registry()
    registration = None

    def owner(service):
        try:
            return call(bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                        "GetNameOwner", GLib.Variant("(s)", (service,)))[0]
        except GLib.Error:
            return None

    def emit(signal, key=None):
        if bus.is_closed():
            return
        bus.emit_signal(None, WATCHER_PATH, WATCHER, signal,
                        GLib.Variant("(s)", (key,)) if key is not None else None)
        if key is not None:
            bus.emit_signal(None, WATCHER_PATH, "org.freedesktop.DBus.Properties", "PropertiesChanged",
                            GLib.Variant("(sa{sv}as)", (WATCHER, {
                                "RegisteredStatusNotifierItems": GLib.Variant("as", list(registry.items))}, [])))

    def invoke(_conn, sender, path, interface, method, arguments, invocation):
        try:
            value = arguments.unpack()[0]
            if method == "RegisterStatusNotifierItem":
                if key := registry.register(value, sender, owner):
                    emit("StatusNotifierItemRegistered", key)
            elif method == "RegisterStatusNotifierHost":
                if not isinstance(value, str) or not BUS_NAME.fullmatch(value) or owner(value) != sender:
                    raise ValueError("Host de bandeja inválido.")
                emit("StatusNotifierHostRegistered")
            invocation.return_value(None)
        except ValueError as error:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.InvalidArgs", str(error))

    def property_value(_conn, sender, path, interface, name):
        if name == "RegisteredStatusNotifierItems":
            return GLib.Variant("as", list(registry.items))
        if name == "IsStatusNotifierHostRegistered":
            return GLib.Variant("b", True)
        return GLib.Variant("i", 0)

    def acquired(connection, name):
        nonlocal registration
        registration = connection.register_object(WATCHER_PATH, Gio.DBusNodeInfo.new_for_xml(WATCHER_XML).interfaces[0],
                                                   invoke, property_value, None)
        emit("StatusNotifierHostRegistered")

    def lost(connection, name):
        nonlocal registration
        if registration:
            if connection is not None and not connection.is_closed():
                connection.unregister_object(registration)
            registration = None
            registry.items.clear()
        if connection is None or connection.is_closed():
            return
        # Another desktop may already own the watcher. Register as a host,
        # leaving that service in control; queued ownership handles its exit.
        connection.call(WATCHER, WATCHER_PATH, WATCHER, "RegisterStatusNotifierHost",
                        GLib.Variant("(s)", (DAEMON,)), None, Gio.DBusCallFlags.NONE, 1500, None, None, None)

    def changed(_conn, sender, path, interface, signal, arguments):
        for key in registry.owner_changed(*arguments.unpack()):
            emit("StatusNotifierItemUnregistered", key)

    bus.signal_subscribe("org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
                         "/org/freedesktop/DBus", None, Gio.DBusSignalFlags.NONE, changed)
    Gio.bus_own_name_on_connection(bus, WATCHER, Gio.BusNameOwnerFlags.NONE, acquired, lost)
    loop = GLib.MainLoop()
    bus.connect("closed", lambda *_: loop.quit())
    stop, processes = threading.Event(), []

    def session_monitor():
        # A persistent user D-Bus outlives i3. Release the watcher on logout,
        # while reconnecting after an in-place WM restart.
        failures = 0
        while not stop.is_set():
            try:
                process = subprocess.Popen(["i3-msg", "-m", "-t", "subscribe", '["shutdown"]'],
                                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                processes[:] = [process]
                for line in process.stdout:
                    if stop.is_set():
                        return
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(event, dict) and event.get("change") == "exit":
                        GLib.idle_add(loop.quit)
                        return
                    # An established subscription or explicit restart resets
                    # the retry window. A terminated server cannot do either.
                    if (isinstance(event, dict) and event.get("change") == "restart"
                            or isinstance(event, list) and any(e.get("success") for e in event if isinstance(e, dict))):
                        failures = 0
                process.wait(timeout=1)
            except (OSError, subprocess.SubprocessError):
                pass
            failures += 1
            if failures >= 10:
                GLib.idle_add(loop.quit)
                return
            stop.wait(.5)

    monitor = None
    if shutil.which("i3-msg"):
        monitor = threading.Thread(target=session_monitor, daemon=True, name="Notebook i3 session")
        monitor.start()
    try:
        loop.run()
    finally:
        stop.set()
        if processes and processes[0].poll() is None:
            processes[0].terminate()
            try:
                processes[0].wait(timeout=1)
            except subprocess.TimeoutExpired:
                processes[0].kill()
        if monitor:
            monitor.join(timeout=1)
    return 0


def status(bus):
    entries = registered(bus)
    # Keep passive items available: they can be the only route back to a
    # running application's window after its close button was used.
    return f"󰍜 {len(entries)}"


def popup():
    Gio, GLib, bus = dbus()
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GdkPixbuf, Gtk
    from panel import popup_bounds, popup_position
    if not Gtk.init_check(None)[0]:
        return 1
    window = Gtk.Window(title="Aplicativos em segundo plano")
    window.set_wmclass("darfinos-notebook-tray", "DarfinOSNotebookTray")
    window.set_name("notebook-tray")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_skip_taskbar_hint(True)
    display = window.get_display()
    _, x, y = display.get_default_seat().get_pointer().get_position()
    monitor = display.get_monitor_at_point(x, y)
    area = popup_bounds(monitor.get_geometry(), monitor.get_workarea())
    window.set_default_size(min(410, max(1, area[2] - 16)), -1)
    css = Gtk.CssProvider()
    css.load_from_data(("#notebook-tray {background:#20242b;color:#f2f2f2;border:1px solid " + ACCENT + ";}"
                        "#notebook-tray .heading {font-size:16px;font-weight:bold;}"
                        "#notebook-tray .attention {color:" + ACCENT + ";}"
                        "#notebook-tray .hint {color:#a8adb7;font-size:12px;}").encode())
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=14)
    window.add(root)
    heading = Gtk.Box(spacing=8)
    title = Gtk.Label(label="Em segundo plano", xalign=0)
    title.get_style_context().add_class("heading")
    heading.pack_start(title, True, True, 0)
    close = Gtk.Button(label="Fechar")
    close.connect("clicked", lambda *_: window.destroy())
    heading.pack_end(close, False, False, 0)
    root.add(heading)
    hint = Gtk.Label(label="Acesse os apps que continuam rodando sem janela.", xalign=0, wrap=True)
    hint.get_style_context().add_class("hint")
    root.add(hint)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_propagate_natural_height(True)
    scroll.set_max_content_height(max(1, area[3] - 130))
    rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    scroll.add(rows)
    root.add(scroll)
    feedback = Gtk.Label(label="Carregando aplicativos…", xalign=0, wrap=True, max_width_chars=45)
    feedback.get_style_context().add_class("hint")
    root.add(feedback)
    refresh_button = Gtk.Button(label="Atualizar")
    root.add(refresh_button)
    worker = ThreadPoolExecutor(max_workers=2)
    alive = True
    current_menu = None
    loading = False
    pending_refresh = False

    def complete(future, done):
        def paint():
            if not alive:
                return False
            try:
                return done(future.result()) or False
            except Exception:
                feedback.set_text("O aplicativo não respondeu. Ele pode ter sido encerrado.")
                return False
        GLib.idle_add(paint)

    def submit(job, done=lambda _: None):
        future = worker.submit(job)
        future.add_done_callback(lambda f: complete(f, done))

    def invoke_item(target, method):
        submit(lambda: call(bus, target.service, target.path, ITEM, method,
                            GLib.Variant("(ii)", (x, y)), timeout=1500),
               lambda _: feedback.set_text("Ação enviada ao aplicativo."))

    def send_menu(target, menu_path, identifier):
        submit(lambda: call(bus, target.service, menu_path, DBUSMENU, "Event",
                            GLib.Variant("(isvu)", (identifier, "clicked", GLib.Variant("s", ""),
                                                     Gtk.get_current_event_time())), timeout=1500),
               lambda _: feedback.set_text("Ação enviada ao aplicativo."))

    def read_menu(target, menu_path, identifier):
        try:
            call(bus, target.service, menu_path, DBUSMENU, "AboutToShow", GLib.Variant("(i)", (identifier,)))
        except GLib.Error:
            pass
        result = call(bus, target.service, menu_path, DBUSMENU, "GetLayout",
                      GLib.Variant("(iias)", (identifier, -1, [])), timeout=1500)
        return menu_nodes(result[1])

    def build_menu(target, menu_path, nodes):
        menu = Gtk.Menu()
        menu._notebook_nodes = nodes
        for node in nodes:
            if node["separator"]:
                item = Gtk.SeparatorMenuItem()
            elif node["toggle"]:
                item = Gtk.CheckMenuItem.new_with_mnemonic(node["label"])
                item.set_draw_as_radio(node["toggle"] == "radio")
                item.set_active(node["state"] == 1)
                item.set_inconsistent(node["state"] == -1)
            else:
                item = Gtk.MenuItem.new_with_mnemonic(node["label"] or "Ação")
            item._notebook_item_id = node["id"]
            item.set_sensitive(node["enabled"])
            if node["children"] or node["submenu"]:
                submenu = build_menu(target, menu_path, node["children"])
                if not node["children"]:
                    loading_item = Gtk.MenuItem(label="Carregando…")
                    loading_item.set_sensitive(False)
                    submenu.append(loading_item)
                    loading_item.show()

                def update_submenu(widget, identifier=node["id"]):
                    def paint_submenu(result):
                        if not widget.get_mapped() or result is None:
                            return
                        children = result["children"]
                        # AboutToShow often returns the layout we already have.
                        # Rebuilding it would discard GTK's keyboard selection
                        # while the user is entering the submenu with Right.
                        if children == widget._notebook_nodes:
                            return
                        selected = widget.get_selected_item()
                        selected_id = getattr(selected, "_notebook_item_id", None)
                        for old in widget.get_children():
                            widget.remove(old)
                        updated = build_menu(target, menu_path, children)
                        widget._notebook_nodes = children
                        for child in updated.get_children():
                            updated.remove(child)
                            widget.append(child)
                        updated.destroy()
                        widget.show_all()
                        replacement = next((child for child in widget.get_children()
                                            if getattr(child, "_notebook_item_id", None) == selected_id
                                            and child.get_sensitive()), None)
                        if replacement is not None:
                            widget.select_item(replacement)
                        else:
                            widget.select_first(True)
                    submit(lambda: read_menu(target, menu_path, identifier), paint_submenu)
                    return False

                submenu.connect("map", update_submenu)
                item.set_submenu(submenu)
            elif not node["separator"]:
                item.connect("activate", lambda _item, i=node["id"]: send_menu(target, menu_path, i))
            menu.append(item)
        menu.show_all()
        return menu

    def menu_for(target, properties, button):
        menu_path = properties.get("Menu", "")
        if not isinstance(menu_path, str) or menu_path == "/" or not OBJECT_PATH.fullmatch(menu_path):
            invoke_item(target, "ContextMenu")
            return
        feedback.set_text("Carregando menu…")

        def opened(node):
            nonlocal current_menu
            if not node or not node["children"]:
                feedback.set_text("Este aplicativo não forneceu ações no menu.")
                return
            current_menu = build_menu(target, menu_path, node["children"])
            def closed(menu):
                # GTK emits deactivate before the chosen item's activate.
                # Destroying synchronously would swallow its D-Bus action.
                clear_menu()
                GLib.idle_add(lambda: menu.destroy() or False)
            current_menu.connect("deactivate", closed)
            feedback.set_text("")
            current_menu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

        submit(lambda: read_menu(target, menu_path, 0), opened)

    def clear_menu():
        nonlocal current_menu, pending_refresh
        current_menu = None
        if pending_refresh:
            pending_refresh = False
            refresh()

    def paint_items(entries):
        nonlocal loading
        loading = False
        refresh_button.set_sensitive(True)
        for child in rows.get_children():
            rows.remove(child)
        for target, properties in sorted(entries, key=lambda item: plain(item[1].get("Title") or item[1].get("Id") or item[0].service).casefold()):
            label = plain(properties.get("Title") or properties.get("Id") or target.service)
            row = Gtk.Box(spacing=8)
            attention = properties.get("Status") == "NeedsAttention"
            icon_name = properties.get("AttentionIconName" if attention else "IconName") or properties.get("IconName", "")
            icon_theme = Gtk.IconTheme.new()
            icon_theme.set_screen(Gdk.Screen.get_default())
            custom_path = properties.get("IconThemePath", "")
            if isinstance(custom_path, str) and Path(custom_path).is_absolute() and Path(custom_path).is_dir():
                icon_theme.prepend_search_path(custom_path)
            icon = None
            if isinstance(icon_name, str) and icon_name:
                if Path(icon_name).is_absolute() and Path(icon_name).is_file():
                    try:
                        icon = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_name, 24, 24, True))
                    except GLib.Error:
                        pass
                elif icon_theme.has_icon(icon_name):
                    try:
                        icon = Gtk.Image.new_from_pixbuf(icon_theme.load_icon(icon_name, 24, Gtk.IconLookupFlags.FORCE_SIZE))
                    except GLib.Error:
                        pass
            if icon is None and (pixels := icon_pixels(properties.get("AttentionIconPixmap" if attention else "IconPixmap")
                                                      or properties.get("IconPixmap"))):
                width, height, rgba = pixels
                pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(rgba), GdkPixbuf.Colorspace.RGB,
                                                       True, 8, width, height, width * 4)
                icon = Gtk.Image.new_from_pixbuf(pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.BILINEAR))
            if icon is None:
                icon = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.LARGE_TOOLBAR)
            row.pack_start(icon, False, False, 0)
            name = Gtk.Label(label=label, xalign=0, ellipsize=3)
            name.set_max_width_chars(22)
            name.set_hexpand(True)
            if properties.get("Status") == "NeedsAttention":
                name.get_style_context().add_class("attention")
            row.pack_start(name, True, True, 0)
            activate = Gtk.Button(label="Abrir")
            activate.get_accessible().set_name("Abrir " + label)
            menu = Gtk.Button(label="Menu")
            menu.get_accessible().set_name("Menu de " + label)
            if properties.get("ItemIsMenu", False):
                activate.connect("clicked", lambda b, t=target, p=properties: menu_for(t, p, b))
            else:
                activate.connect("clicked", lambda _b, t=target: invoke_item(t, "Activate"))
            activate.connect("button-press-event", lambda _b, event, t=target:
                             (invoke_item(t, "SecondaryActivate") or True) if event.button == 2 else False)
            menu.connect("clicked", lambda b, t=target, p=properties: menu_for(t, p, b))
            row.pack_end(menu, False, False, 0)
            row.pack_end(activate, False, False, 0)
            rows.add(row)
        rows.show_all()
        feedback.set_text("" if entries else "Nenhum aplicativo registrado. Ative o ícone de bandeja nas preferências do app. Alguns aplicativos exibem seu ícone diretamente na barra.")

    def refresh(*_):
        nonlocal loading, pending_refresh
        if current_menu is not None:
            pending_refresh = True
            return
        if loading or not alive:
            return
        loading = True
        refresh_button.set_sensitive(False)
        def load():
            return [(target, props) for target in registered(bus) if (props := item_properties(bus, target)) is not None]
        submit(load, paint_items)

    def destroyed(*_):
        nonlocal alive
        alive = False
        Gtk.main_quit()

    def align(*_):
        window.move(*popup_position(area, window.get_size()))
        return False

    window.connect("destroy", destroyed)
    window.connect("key-press-event", lambda w, e: (w.destroy() or True) if e.keyval == Gdk.KEY_Escape and current_menu is None else False)
    window.connect("focus-out-event", lambda *_: (window.destroy() or False) if current_menu is None else False)
    window.connect("size-allocate", lambda *_: GLib.idle_add(align))
    window.connect("map-event", lambda *_: window.get_window().set_cursor(Gdk.Cursor.new_from_name(display, "default")))
    refresh_button.connect("clicked", refresh)
    subscription = bus.signal_subscribe(None, WATCHER, None, WATCHER_PATH, None, Gio.DBusSignalFlags.NONE,
                                         lambda *_: GLib.idle_add(refresh))
    metadata_subscription = bus.signal_subscribe(None, ITEM, None, None, None, Gio.DBusSignalFlags.NONE,
                                                  lambda *_: GLib.idle_add(refresh))
    window.move(*popup_position(area, (400, 1)))
    window.show_all()
    window.present()
    close.grab_focus()
    refresh()
    Gtk.main()
    bus.signal_unsubscribe(subscription)
    bus.signal_unsubscribe(metadata_subscription)
    worker.shutdown(wait=False, cancel_futures=True)
    return 0


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments not in (["daemon"], ["watch"], ["status"], ["popup"]):
        return 2
    try:
        if arguments == ["daemon"]:
            return daemon()
        if arguments == ["popup"]:
            if runtime := os.environ.get("XDG_RUNTIME_DIR"):
                with (Path(runtime) / "darfinos-notebook-tray-popup.lock").open("w") as lock:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        return 0
                    return popup()
            return popup()
        _, _, bus = dbus()
        previous = None
        while True:
            text = status(bus)
            if text != previous:
                print(text, flush=True)
                previous = text
            if arguments == ["status"]:
                return 0
            time.sleep(2)
    except (ImportError, ValueError, OSError) as error:
        print(f"DarfinOS · Bandeja: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

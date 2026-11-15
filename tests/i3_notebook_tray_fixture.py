"""Disposable windowless SNI/DBusMenu app for the real X11/DBus smoke test.

Arguments: NAME EVENT_LOG READY_FILE [service|path]. No Steam or KDE Connect
installation is used and the fixture never accesses a user's application data.
"""
from pathlib import Path
import sys

from gi.repository import Gio, GLib

name, event_path, ready_path, *registration = sys.argv[1:]
events, ready = Path(event_path), Path(ready_path)
mode = registration[0] if registration else "service"
service = f"org.kde.StatusNotifierItem.DarfinOSTest{name}"
item_path = "/KDEConnect" if mode == "path" else "/StatusNotifierItem"
watcher = "org.kde.StatusNotifierWatcher"
watcher_path = "/StatusNotifierWatcher"
iface = "org.kde.StatusNotifierItem"
menu_iface = "com.canonical.dbusmenu"
loop = GLib.MainLoop()
connection = None
registered = False
toggled = True
submenu_ready = False

ITEM_XML = f"""<node><interface name="{iface}">
<method name="Activate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="SecondaryActivate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="ContextMenu"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<property name="Category" type="s" access="read"/>
<property name="Id" type="s" access="read"/>
<property name="Title" type="s" access="read"/>
<property name="Status" type="s" access="read"/>
<property name="IconName" type="s" access="read"/>
<property name="ItemIsMenu" type="b" access="read"/>
<property name="Menu" type="o" access="read"/>
<signal name="NewTitle"/>
<signal name="NewStatus"><arg type="s"/></signal>
</interface></node>"""
MENU_XML = f"""<node><interface name="{menu_iface}">
<method name="GetLayout"><arg type="i" direction="in"/><arg type="i" direction="in"/><arg type="as" direction="in"/>
<arg type="u" direction="out"/><arg type="(ia{{sv}}av)" direction="out"/></method>
<method name="AboutToShow"><arg type="i" direction="in"/><arg type="b" direction="out"/></method>
<method name="Event"><arg type="i" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="in"/><arg type="u" direction="in"/></method>
<property name="Version" type="u" access="read"/>
<property name="TextDirection" type="s" access="read"/>
<property name="Status" type="s" access="read"/>
<signal name="LayoutUpdated"><arg type="u"/><arg type="i"/></signal>
</interface></node>"""


def log(message):
    with events.open("a", encoding="utf-8") as stream:
        stream.write(f"{name} {message}\n")


def item_call(conn, sender, path, interface, method, args, invocation):
    log(method)
    invocation.return_value(None)


def item_read(conn, sender, path, interface, key):
    properties = {
        "Category": ("s", "ApplicationStatus"), "Id": ("s", name),
        "Title": ("s", "KDE Connect" if name == "Connect" else name),
        "Status": ("s", "Active"), "IconName": ("s", "kdeconnect" if name == "Connect" else "steam"),
        "ItemIsMenu": ("b", False), "Menu": ("o", "/Menu"),
    }
    if key in properties:
        kind, value = properties[key]
        return GLib.Variant(kind, value)
    return None


def properties(**values):
    return {key.replace("_", "-"): GLib.Variant("b" if isinstance(value, bool) else
                                              "i" if isinstance(value, int) else "s", value)
            for key, value in values.items()}


def node(identifier, values, children=()):
    return GLib.Variant("(ia{sv}av)", (identifier, values, list(children)))


def layout(identifier=0):
    child = node(6, properties(label="Téléphone de test", enabled=True, visible=True))
    submenu = node(5, properties(label="Dispositivos", enabled=True, visible=True,
                                 children_display="submenu"),
                   (child,) if name != "Connect" or submenu_ready else ())
    if identifier == 5:
        return submenu
    return node(0, {}, (
        node(1, properties(label="_Biblioteca", enabled=True, visible=True)),
        node(2, properties(type="separator")),
        node(3, properties(label="Disponível", enabled=True, visible=True,
                           toggle_type="checkmark", toggle_state=int(toggled))),
        node(4, properties(label="Indisponível", enabled=False, visible=True)),
        submenu,
        node(7, properties(label="Oculto", enabled=True, visible=False)),
    ))


def menu_call(conn, sender, path, interface, method, args, invocation):
    global toggled, submenu_ready
    if method == "GetLayout":
        requested = args.unpack()[0]
        log(f"GetLayout {requested}")
        invocation.return_value(GLib.Variant.new_tuple(GLib.Variant("u", 1), layout(requested)))
    elif method == "AboutToShow":
        identifier = args.unpack()[0]
        log(f"AboutToShow {identifier}")
        changed = identifier == 5 and not submenu_ready
        if identifier == 5:
            submenu_ready = True
        invocation.return_value(GLib.Variant("(b)", (changed,)))
    elif method == "Event":
        identifier, event, _, _ = args.unpack()
        log(f"Event {identifier} {event}")
        if identifier == 3 and event == "clicked":
            toggled = not toggled
        invocation.return_value(None)
    else:
        invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)


def menu_read(conn, sender, path, interface, key):
    if key == "Version":
        return GLib.Variant("u", 3)
    if key == "TextDirection":
        return GLib.Variant("s", "ltr")
    if key == "Status":
        return GLib.Variant("s", "normal")
    return None


def register():
    global registered
    if registered:
        return GLib.SOURCE_REMOVE
    if connection is None:
        return GLib.SOURCE_CONTINUE
    try:
        connection.call_sync(watcher, watcher_path, watcher, "RegisterStatusNotifierItem",
                             GLib.Variant("(s)", (item_path if mode == "path" else service,)),
                             None, Gio.DBusCallFlags.NONE, 700, None)
    except GLib.Error:
        return GLib.SOURCE_CONTINUE
    registered = True
    log("Registered")
    ready.write_text(service + "\n", encoding="utf-8")
    return GLib.SOURCE_REMOVE


def acquired(conn, bus_name):
    global connection
    connection = conn
    conn.register_object(item_path, Gio.DBusNodeInfo.new_for_xml(ITEM_XML).interfaces[0],
                         item_call, item_read, None)
    conn.register_object("/Menu", Gio.DBusNodeInfo.new_for_xml(MENU_XML).interfaces[0],
                         menu_call, menu_read, None)
    GLib.timeout_add(100, register)


def appeared(conn, bus_name, owner):
    global registered
    registered = False
    GLib.timeout_add(100, register)


Gio.bus_watch_name(Gio.BusType.SESSION, watcher, Gio.BusNameWatcherFlags.NONE, appeared, None)
Gio.bus_own_name(Gio.BusType.SESSION, service, Gio.BusNameOwnerFlags.NONE, acquired, None, None)
loop.run()

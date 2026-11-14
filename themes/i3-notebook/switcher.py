"""X11 Alt+Tab. A passive grab becomes a keyboard grab until Alt is released."""
import sys

from windows import ACCENT, activate, clean, lock, snapshot


def main():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
    from Xlib import X, XK, display, error

    if not Gtk.init_check(None)[0]:
        return 1
    conn = display.Display()
    root = conn.screen().root
    style = Gtk.CssProvider()
    style.load_from_data("""
        #switcher { background: #20242b; border: 1px solid @ACCENT@; }
        #switcher label { color: #f2f2f2; }
        #switcher .secondary { color: #c0c4cd; }
        #switcher .picked { background: #453e2b; border-left: 3px solid @ACCENT@; }
    """.replace("@ACCENT@", ACCENT).encode())
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    popup = Gtk.Window(type=Gtk.WindowType.POPUP, title="DarfinOS · Alt+Tab")
    popup.set_wmclass("darfinos-alt-tab", "DarfinOSAltTab")
    popup.set_name("switcher")
    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=12, spacing=5)
    popup.add(panel)

    keys = {}
    candidates = []
    index = 0
    active = False

    def keycode(name):
        return conn.keysym_to_keycode(XK.string_to_keysym(name))

    def setup():
        nonlocal keys
        root.ungrab_key(X.AnyKey, X.AnyModifier)
        keys = {k: keycode(k) for k in ("Tab", "ISO_Left_Tab", "Alt_L", "Alt_R",
                                        "Escape", "Return", "Up", "Down", "Caps_Lock",
                                        "Num_Lock", "Scroll_Lock")}
        mappings = list(conn.get_modifier_mapping())
        alt_codes = {keys["Alt_L"], keys["Alt_R"]} - {0}
        alt_masks = {1 << i for i, codes in enumerate(mappings) if alt_codes.intersection(codes)} or {X.Mod1Mask}
        lock_codes = {keys[k] for k in ("Caps_Lock", "Num_Lock", "Scroll_Lock")} - {0}
        optional = {0}
        for i, codes in enumerate(mappings):
            if lock_codes.intersection(codes) and (1 << i) not in alt_masks:
                optional |= {m | (1 << i) for m in optional}
        catch = error.CatchError(error.BadAccess)
        for key in {keys["Tab"], keys["ISO_Left_Tab"]} - {0}:
            for mask in {alt | locks | shift for alt in alt_masks for locks in optional for shift in (0, X.ShiftMask)}:
                root.grab_key(key, mask, False, X.GrabModeAsync, X.GrabModeAsync, onerror=catch)
        conn.sync()
        if catch.get_error():
            print("DarfinOS: atalho Alt+Tab já registrado na sessão.", file=sys.stderr)

    def draw():
        for child in panel.get_children():
            panel.remove(child)
        heading = Gtk.Label(label=f"Trocar de janela · {index + 1}/{len(candidates)}", xalign=0)
        panel.add(heading)
        start = min(max(0, index - 2), max(0, len(candidates) - 5))
        for i in range(start, min(len(candidates), start + 5)):
            w = candidates[i]
            row = Gtk.EventBox()
            row.get_style_context().add_class("picked" if i == index else "secondary")
            label = Gtk.Label(label=f"{w.icon}  {clean(w.title, 42)}", xalign=0, margin=8)
            row.add(label)
            panel.add(row)
        panel.add(Gtk.Label(label="Solte Alt para abrir · Esc para cancelar", xalign=0))
        panel.show_all()

    def start(reverse):
        nonlocal candidates, index, active
        # i3 already exposes a recursive focus stack, even across workspaces.
        # Replace the passive grab immediately so releasing Tab does not end it.
        if root.grab_keyboard(False, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime) != X.GrabSuccess:
            return
        candidates = snapshot()
        if len(candidates) < 2:
            if candidates and not candidates[0].focused:
                with lock("window-actions"):
                    activate(candidates[0])
            conn.ungrab_keyboard(X.CurrentTime)
            conn.flush()
            return
        selected = next((i for i, w in enumerate(candidates) if w.focused), None)
        index = ((selected + (-1 if reverse else 1)) % len(candidates) if selected is not None
                 else (len(candidates) - 1 if reverse else 0))
        active = True
        gdisplay = popup.get_display()
        _, x, y = gdisplay.get_default_seat().get_pointer().get_position()
        area = gdisplay.get_monitor_at_point(x, y).get_workarea()
        popup.resize(min(420, area.width), 1)
        draw()
        popup.show()
        popup.move(area.x + (area.width - popup.get_size()[0]) // 2,
                   area.y + max(0, (area.height - popup.get_size()[1]) // 2))
        # A very fast Alt+Tab may already have released Alt while we got the tree.
        pressed = conn.query_keymap()
        alt_codes = {keys["Alt_L"], keys["Alt_R"]} - {0}
        if not any(pressed[k // 8] & (1 << (k % 8)) for k in alt_codes):
            finish(True)

    def finish(commit):
        nonlocal active
        active = False
        popup.hide()
        conn.ungrab_keyboard(X.CurrentTime)
        conn.flush()
        if commit:
            with lock("window-actions"):
                wanted = candidates[index].id
                if chosen := next((w for w in snapshot() if w.id == wanted), None):
                    activate(chosen)

    def input_event(_fd, condition):
        nonlocal index
        if condition & (GLib.IO_HUP | GLib.IO_ERR):
            Gtk.main_quit()
            return False
        while conn.pending_events():
            event = conn.next_event()
            if event.type == X.MappingNotify:
                if event.request == X.MappingKeyboard:
                    conn.refresh_keyboard_mapping(event)
                if active:
                    finish(False)
                setup()
            elif event.type == X.KeyRelease and active and event.detail in {keys["Alt_L"], keys["Alt_R"]}:
                finish(True)
            elif event.type == X.KeyPress:
                tab = event.detail in {keys["Tab"], keys["ISO_Left_Tab"]}
                reverse = bool(event.state & X.ShiftMask) or event.detail == keys["ISO_Left_Tab"]
                if not active:
                    if tab:
                        start(reverse)
                elif event.detail in (keys["Escape"], keys["Return"]):
                    finish(event.detail == keys["Return"])
                elif tab or event.detail in (keys["Up"], keys["Down"]):
                    index = (index + (-1 if reverse or event.detail == keys["Up"] else 1)) % len(candidates)
                    draw()
        return True

    with lock("alt-tab", blocking=False) as acquired:
        if not acquired:
            return 0
        setup()
        GLib.io_add_watch(conn.fileno(), GLib.PRIORITY_DEFAULT, GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR, input_event)
        # Xlib can buffer input during a synchronous request, making its socket
        # temporarily unreadable even though events are queued.
        GLib.timeout_add(150, lambda: input_event(None, 0))
        try:
            Gtk.main()
        finally:
            conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

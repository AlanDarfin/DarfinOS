"""Handle right-click on empty X11 desktop space, without taking app clicks."""
import subprocess
import sys

from windows import PROFILE, lock


def main():
    from Xlib import X, XK, display, error

    with lock("desktop-mouse", blocking=False) as acquired:
        if not acquired:
            return 0
        connection = display.Display()
        root = connection.screen().root
        try:
            # Synchronous grab lets us check the target before handing the
            # original event back to X11. Replay skips this grab, preserving
            # application menus, i3 mouse shortcuts and Polybar right-clicks.
            lock_codes = {connection.keysym_to_keycode(XK.string_to_keysym(name))
                          for name in ("Caps_Lock", "Num_Lock", "Scroll_Lock")} - {0}
            masks = {0}
            for index, codes in enumerate(connection.get_modifier_mapping()):
                if lock_codes.intersection(codes):
                    masks |= {mask | (1 << index) for mask in masks}
            rejected = error.CatchError(error.BadAccess)
            for mask in masks:
                root.grab_button(3, mask, False, X.ButtonPressMask | X.ButtonReleaseMask,
                                 X.GrabModeSync, X.GrabModeAsync, X.NONE, X.NONE, onerror=rejected)
            connection.sync()
            if rejected.get_error():
                print("DarfinOS: clique de contexto já registrado na sessão X11.", file=sys.stderr)
                return 1
            pending = None
            while True:
                event = connection.next_event()
                if event.type == X.ButtonPress:
                    if event.child:
                        pending = None
                        connection.allow_events(X.ReplayPointer, event.time)
                    else:
                        pending = (event.root_x, event.root_y)
                        connection.allow_events(X.AsyncPointer, event.time)
                    connection.flush()
                elif event.type == X.ButtonRelease and pending:
                    x, y = pending
                    pending = None
                    # Dragging off the desktop shouldn't open the menu.
                    if event.child or abs(event.root_x - x) > 8 or abs(event.root_y - y) > 8:
                        continue
                    subprocess.Popen(["sh", str(PROFILE / "session.sh"), "desktop-menu", str(x), str(y)],
                                     stdin=subprocess.DEVNULL)
        except (OSError, error.ConnectionClosedError):
            return 0
        finally:
            connection.close()


if __name__ == "__main__":
    sys.exit(main())

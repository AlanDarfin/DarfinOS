#!/usr/bin/env bash
# Sourced by integration_i3_notebook.sh after i3/DBus/X11 are ready.
# Fixtures expose the actual StatusNotifierItem/DBusMenu protocols, no app windows.
tray_count_is() {
  python - "$1" <<'COUNT'
from gi.repository import Gio, GLib
import sys
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
reply = bus.call_sync("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher",
                      "org.freedesktop.DBus.Properties", "Get",
                      GLib.Variant("(ss)", ("org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems")),
                      None, Gio.DBusCallFlags.NONE, 1000, None)
assert len(reply.unpack()[0]) == int(sys.argv[1]), reply.unpack()
COUNT
}
tray_daemon_owner() {
  python - <<'OWNER'
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
print(bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                    "GetNameOwner", GLib.Variant("(s)", ("org.darfinos.NotebookTray",)),
                    None, Gio.DBusCallFlags.NONE, 1000, None).unpack()[0])
OWNER
}
tray_popup_visible() { xdotool search --onlyvisible --class '^DarfinOSNotebookTray$' >/dev/null 2>&1; }
tray_popup_closed() { ! tray_popup_visible; }
tray_launch_popup() {
  if ! tray_popup_visible; then
    # An in-place WM restart can briefly swallow the first key press while
    # the old dock is still mapped. Retry until the binding is ready.
    xdotool key super+F8
    sleep .15
  fi
  tray_popup_visible
}
tray_open() {
  await_result tray_launch_popup
  tray_window=$(xdotool search --onlyvisible --class '^DarfinOSNotebookTray$' | head -1)
  [[ "$(xdotool getwindowname "$tray_window")" == 'Aplicativos em segundo plano' ]]
}
tray_menu_loaded() { [[ "$(grep -Fc "$1 GetLayout" "$tmp/tray-events" || :)" -gt "$tray_menu_previous" ]]; }
tray_open_menu() {
  tray_menu_previous=$(grep -Fc "$1 GetLayout" "$tmp/tray-events" || :)
  tray_open
  # The title's Close button starts focused, followed by the first row's
  # Open and Menu controls. KDE Connect sorts before Steam.
  xdotool key Tab Tab Return
  await_result tray_menu_loaded "$1"
  # D-Bus replies precede the Gtk idle callback which maps the actual menu.
  sleep .3
}

await_result tray_count_is 0
tray_owner=$(tray_daemon_owner)
# A second start is a no-op; restarts must not create a competing watcher.
timeout 5 python "$profile/tray.py" daemon
[[ "$(tray_daemon_owner)" == "$tray_owner" ]]
python tests/i3_notebook_tray_fixture.py Steam "$tmp/tray-events" "$tmp/tray-steam-ready" service >"$tmp/tray-steam.log" 2>&1 &
tray_steam_pid=$!
python tests/i3_notebook_tray_fixture.py Connect "$tmp/tray-events" "$tmp/tray-connect-ready" path >"$tmp/tray-connect.log" 2>&1 &
tray_connect_pid=$!
await_result test -s "$tmp/tray-steam-ready"
await_result test -s "$tmp/tray-connect-ready"
await_result tray_count_is 2
# There are no ordinary Steam/KDE Connect windows to focus in the window dock.
i3-msg -t get_tree | python -c 'import json,sys

def nodes(n):
    yield n
    for c in n.get("nodes", [])+n.get("floating_nodes", []): yield from nodes(c)
assert not any(n.get("window") and n.get("name") in ("Steam", "KDE Connect") for n in nodes(json.load(sys.stdin)))'
xdotool key super+shift+c
await_result bar_mapped
await_result tray_count_is 2
[[ "$(tray_daemon_owner)" == "$tray_owner" ]]
tray_open
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window "$tray_window" "$DARFINOS_PREVIEW_DIR/background-apps-720p.png"
fi
# Activate a windowless KDE Connect item through its real D-Bus method.
xdotool key Tab Return
await_result grep -Fq 'Connect Activate' "$tmp/tray-events"
xdotool key Escape
await_result tray_popup_closed

tray_open_menu Connect
xdotool key Home Return
await_result grep -Fq 'Connect Event 1 clicked' "$tmp/tray-events"
xdotool key Escape
await_result tray_popup_closed
# Separators and disabled entries must be skipped by keyboard navigation.
tray_open_menu Connect
xdotool key Home Down Return
await_result grep -Fq 'Connect Event 3 clicked' "$tmp/tray-events"
xdotool key Escape
await_result tray_popup_closed
# A submenu still forwards the remote child ID, not its visible row index.
tray_open_menu Connect
xdotool key Home Down Down Right
# The submenu fetches its own layout. Wait for that response and GTK's idle
# update before activating it, as a real user would after seeing its entries.
await_result grep -Fq 'Connect GetLayout 5' "$tmp/tray-events"
sleep .15
xdotool key Home Return
await_result grep -Fq 'Connect Event 6 clicked' "$tmp/tray-events"
! grep -Eq 'Event (2|4|7) clicked' "$tmp/tray-events"
xdotool key Escape
await_result tray_popup_closed

# Vanishing owners are removed from the watcher instead of leaving stale apps.
kill "$tray_connect_pid"
wait "$tray_connect_pid" || :
tray_connect_pid=
await_result tray_count_is 1
tray_open
xdotool key Tab Return
await_result grep -Fq 'Steam Activate' "$tmp/tray-events"
xdotool key Escape
await_result tray_popup_closed
tray_open_menu Steam
xdotool key Home Return
await_result grep -Fq 'Steam Event 1 clicked' "$tmp/tray-events"
xdotool key Escape
await_result tray_popup_closed
# Steam provides its children immediately, whereas Connect populated the
# submenu lazily above. Refreshing an unchanged layout must retain selection.
tray_open_menu Steam
xdotool key Home Down Down Right
await_result grep -Fq 'Steam GetLayout 5' "$tmp/tray-events"
sleep .15
xdotool key Home Return
await_result grep -Fq 'Steam Event 6 clicked' "$tmp/tray-events"
xdotool key Escape
await_result tray_popup_closed
kill "$tray_steam_pid"
wait "$tray_steam_pid" || :
tray_steam_pid=
await_result tray_count_is 0
tray_open
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window "$tray_window" "$DARFINOS_PREVIEW_DIR/background-apps-empty-720p.png"
fi
xdotool key Escape
await_result tray_popup_closed
printf '%s\n' 'StatusNotifierItem: windowless Steam/KDE Connect registration, activation, nested DBusMenus, owner cleanup and singleton restart verified.'

# A persistent user D-Bus must not keep the Notebook host alive after logout.
# The WM may close its IPC socket before i3-msg receives the reply.
i3-msg exit >/dev/null || :
tray_daemon_gone() {
  python - <<'OWNER_GONE'
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
assert not bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                         "NameHasOwner", GLib.Variant("(s)", ("org.darfinos.NotebookTray",)),
                         None, Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
OWNER_GONE
}
await_result tray_daemon_gone
printf '%s\n' 'Notebook tray daemon exits with i3 while session D-Bus remains available.'

#!/usr/bin/env bash
# Headless X11 test. Run only in a disposable environment with the profile packages.
set -euo pipefail
if [[ "${1:-}" != "--dbus" ]]; then
  exec dbus-run-session -- bash "$0" --dbus
fi
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
export HOME="$tmp/home" XDG_RUNTIME_DIR="$tmp/run"
export XDG_CONFIG_HOME="$HOME/.config" XDG_DATA_HOME="$HOME/.local/share"
export XDG_CURRENT_DESKTOP=i3 TERMINAL=xterm
unset BROWSER
export NO_AT_BRIDGE=1
# Exercise the real controls with a simulated backend. Never change host audio.
mkdir -p "$tmp/bin"
export PATH="$tmp/bin:$PATH" DARFINOS_TEST_AUDIO="$tmp"
printf '0.55\n' > "$tmp/sink"
printf '0.35\n' > "$tmp/source"
cat > "$tmp/bin/wpctl" <<'AUDIO'
#!/bin/sh
case " $* " in
  *" @DEFAULT_AUDIO_SINK@ "*) device=sink ;;
  *" @DEFAULT_AUDIO_SOURCE@ "*) device=source ;;
  *) exit 1 ;;
esac
state="$DARFINOS_TEST_AUDIO/$device"
case "$1" in
  get-volume)
    printf 'Volume: %s' "$(cat "$state")"
    if [ -e "$state.mute" ]; then printf ' [MUTED]'; fi
    printf '\n' ;;
  set-volume) awk -v level="${5%%%}" 'BEGIN {printf "%.2f\n", level / 100}' > "$state" ;;
  set-mute) if [ -e "$state.mute" ]; then rm "$state.mute"; else touch "$state.mute"; fi ;;
  *) exit 1 ;;
esac
AUDIO
# No Bluetooth adapter or real power changes are needed for the smoke test.
cat > "$tmp/bin/systemctl" <<'SYSTEMCTL'
#!/bin/sh
case "$*" in
  'is-active bluetooth.service')
    if [ -f "$DARFINOS_TEST_AUDIO/bt-enabled" ]; then echo active; else echo inactive; exit 3; fi ;;
  'start bluetooth.service') touch "$DARFINOS_TEST_AUDIO/bt-enabled" ;;
  reboot|poweroff|suspend) printf '%s\n' "$1" > "$DARFINOS_TEST_AUDIO/power-event" ;;
  *) exit 1 ;;
esac
SYSTEMCTL
cat > "$tmp/bin/bluetoothctl" <<'BLUEZ'
#!/bin/sh
[ "$1" = show ] || exit 1
printf 'Controller TEST\n\tPowered: no\n'
BLUEZ
chmod +x "$tmp/bin/systemctl" "$tmp/bin/bluetoothctl"
chmod +x "$tmp/bin/wpctl"
mkdir -m 700 "$HOME" "$XDG_RUNTIME_DIR"
mkdir -p "$XDG_CONFIG_HOME" "$HOME/.icons/Bibata-NotebookTest/cursors"
cp /usr/share/icons/Adwaita/cursors/left_ptr "$HOME/.icons/Bibata-NotebookTest/cursors/left_ptr"
printf "[Mouse]\ncursorTheme=Bibata-NotebookTest\ncursorSize=32\n" >"$XDG_CONFIG_HOME/kcminputrc"
x_pid= i3_pid= status_pid= mpris_pid=
cleanup() {
  local status=$?
  if (( status )); then
    tail -n 80 "$tmp/i3.log" "$tmp/xvfb.log" "$tmp/polybar.log" >&2 || :
  fi
  [[ -z "$mpris_pid" ]] || kill "$mpris_pid" 2>/dev/null || :
  [[ -z "$status_pid" ]] || kill "$status_pid" 2>/dev/null || :
  [[ -z "$i3_pid" ]] || kill "$i3_pid" 2>/dev/null || :
  [[ -z "$x_pid" ]] || kill "$x_pid" 2>/dev/null || :
  wait || :
  rm -rf "$tmp"
}
trap cleanup EXIT
await_result() {
  for ((i = 0; i < 50; i++)); do
    if "$@"; then return 0; fi
    sleep 0.1
  done
  printf 'Timed out: %s\n' "$*" >&2
  return 1
}

python darfinos_control.py style i3-notebook --apply --all-files
profile="$XDG_CONFIG_HOME/darfinos/i3-notebook"
i3 -C -c "$XDG_CONFIG_HOME/i3/config"
rofi -no-config -rasi-validate "$profile/rofi.rasi"

Xvfb -displayfd 3 -screen 0 1280x720x24 -nolisten tcp 3>"$tmp/display" >"$tmp/xvfb.log" 2>&1 &
x_pid=$!
await_result test -s "$tmp/display"
export DISPLAY=":$(cat "$tmp/display")"
i3 -c "$XDG_CONFIG_HOME/i3/config" >"$tmp/i3.log" 2>&1 &
i3_pid=$!
wm_ready() { i3-msg -t get_workspaces >/dev/null 2>&1; }
await_result wm_ready
xrandr --current | grep -F '1280x720'
bar_mapped() { xdotool search --onlyvisible --name '^darfinos-notebook-bar$' >/dev/null 2>&1; }
bar_hidden() { ! bar_mapped; }
await_result bar_mapped
bar_window=$(xdotool search --onlyvisible --name '^darfinos-notebook-bar$')
bar_pid=$(xdotool getwindowpid "$bar_window")
xwininfo -id "$bar_window" > "$tmp/bar-geometry"
grep -Eq 'Absolute upper-left Y:[[:space:]]+0$' "$tmp/bar-geometry"
grep -Eq 'Width:[[:space:]]+1280$' "$tmp/bar-geometry"
grep -Eq 'Height:[[:space:]]+28$' "$tmp/bar-geometry"
xprop -id "$bar_window" _NET_WM_WINDOW_TYPE | grep -Fq _NET_WM_WINDOW_TYPE_DOCK
[[ "$(i3-msg -t get_bar_config notebook | python -c 'import json, sys; print(json.load(sys.stdin)["mode"])')" == invisible ]]
cursor_loaded() { xrdb -query | grep -q 'Xcursor.theme:.*Bibata-NotebookTest'; }
await_result cursor_loaded

# Default wallpaper is applied at login, before any user image is selected.
wallpaper_loaded() { xprop -root _XROOTPMAP_ID | grep -q 'pixmap id #'; }
await_result wallpaper_loaded
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  mkdir -p "$DARFINOS_PREVIEW_DIR"
  magick import -window root "$DARFINOS_PREVIEW_DIR/desktop-720p.png"
fi

# Check the actual Polybar payload, including loaded i3, fonts and launchers.
status_ready() {
  grep -Fq 'session.sh" shortcuts' "$tmp/polybar.log" && grep -Fq 'Área de trabalho' "$tmp/polybar.log" &&
    grep -Fq '󰕾 55%' "$tmp/polybar.log" && grep -Fq '󰍬 35%' "$tmp/polybar.log"
}
polybar -l info -s -c "$profile/polybar.ini" notebook >"$tmp/polybar.log" 2>&1 &
status_pid=$!
await_result status_ready
for action in apps window-list shortcuts wallpaper; do
  grep -Fq "session.sh\" $action:" "$tmp/polybar.log"
done
for font in 'JetBrainsMono Nerd Font Mono' PowerlineSymbols; do
  grep -F "Loaded font" "$tmp/i3.log" | grep -Fq "$font"
done
if grep -Eq 'Ignoring unmatched character|Unrecognized tag|Unclosed action' "$tmp/i3.log"; then
  cat "$tmp/i3.log" >&2
  exit 1
fi
! grep -Fq 'media play-pause' "$tmp/polybar.log"
printf 'Playing' > "$tmp/player-state"
python tests/i3_notebook_mpris_fixture.py "$tmp/player-state" "$tmp/media-event" &
mpris_pid=$!
media_playing() { grep -Fq 'media play-pause darfinos.test:} 󰏤' "$tmp/polybar.log"; }
await_result media_playing
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/media-720p.png"
fi
sh "$profile/session.sh" media next darfinos.test
[[ "$(cat "$tmp/media-event")" == Next ]]
sh "$profile/session.sh" media previous darfinos.test
[[ "$(cat "$tmp/media-event")" == Previous ]]
sh "$profile/session.sh" media play-pause darfinos.test
media_paused() { grep -Fq 'media play-pause darfinos.test:} 󰐊' "$tmp/polybar.log"; }
await_result media_paused
[[ "$(cat "$tmp/media-event")" == PlayPause ]]
kill "$mpris_pid"
wait "$mpris_pid" || :
mpris_pid=
media_hidden() {
  local line
  line=$(grep -F '%{l}' "$tmp/polybar.log" | tail -1)
  [[ -n "$line" && "$line" != *'media play-pause'* ]]
}
await_result media_hidden
kill "$status_pid"
wait "$status_pid" || :
status_pid=

# Click the Apps label, then close the actual Rofi launcher.
xdotool mousemove 35 14 click 1
rofi_visible() { xdotool search --onlyvisible --class rofi >/dev/null 2>&1; }
await_result rofi_visible
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/rofi-720p.png"
fi
xdotool key Escape
rofi_closed() { ! rofi_visible; }
await_result rofi_closed

popup_visible() { xdotool search --onlyvisible --class '^DarfinOSNotebookPopup$' >/dev/null 2>&1; }
popup_closed() { ! popup_visible; }
popup_y() {
  local window
  window=$(xdotool search --onlyvisible --class '^DarfinOSNotebookPopup$') || return 1
  xwininfo -id "$window" | grep -Eq 'Absolute upper-left Y:[[:space:]]+2[89]$'
}
xdotool key super+F3
await_result popup_visible
await_result popup_y
# The first available slider gets keyboard focus after the audio backend responds.
# End moves it to 100%; tab to the mic and use Home to verify independence.
audio_output_changed() {
  xdotool key End
  [[ "$(cat "$tmp/sink")" == 1.00 ]]
}
await_result audio_output_changed
[[ "$(cat "$tmp/source")" == 0.35 ]]
xdotool key Tab Tab Home
audio_input_changed() { [[ "$(cat "$tmp/source")" == 0.00 ]]; }
await_result audio_input_changed
[[ "$(cat "$tmp/sink")" == 1.00 ]]
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/audio-720p.png"
fi
xdotool key Escape
await_result popup_closed
xdotool key super+F5
await_result popup_visible
calendar_title() { [[ "$(xdotool getwindowname "$(xdotool search --onlyvisible --class '^DarfinOSNotebookPopup$')")" == Calendário ]]; }
await_result calendar_title
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/calendar-720p.png"
fi
xdotool key Escape
await_result popup_closed
# The power icon is the last module on the right.
xdotool mousemove 1266 14 click 1
await_result popup_visible
session_title() {
  local window
  window=$(xdotool search --onlyvisible --class '^DarfinOSNotebookPopup$') || return 1
  [[ "$(xdotool getwindowname "$window")" == Sessão ]]
}
await_result session_title
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/session-720p.png"
fi
# Navigate from Fechar to Desligar. Cancel first, then explicitly confirm.
xdotool key Tab Tab Tab Return
[[ ! -e "$tmp/power-event" ]]
xdotool key Return
[[ ! -e "$tmp/power-event" ]]
xdotool key Escape
await_result popup_closed
xdotool key super+F6
await_result session_title
xdotool key Tab Tab Tab Return
[[ ! -e "$tmp/power-event" ]]
xdotool key Shift+Tab Return
await_result test -s "$tmp/power-event"
[[ "$(cat "$tmp/power-event")" == poweroff ]]
await_result popup_closed
# Verify the real Bluetooth module is clickable even with its service disabled.
# No backlight in Xvfb, so bronze on the bar uniquely identifies Bluetooth.
find_bluetooth() {
  bluetooth_x=$(magick import -window root -crop 1280x1+0+3 -depth 8 txt:- |
    awk 'toupper($0) ~ /#BC9859/ {split($1, p, ","); total+=p[1]; count++} END {if (count) print int(total/count); else exit 1}')
}
await_result find_bluetooth
xdotool mousemove "$bluetooth_x" 14 click 1
bluetooth_title() {
  local window
  window=$(xdotool search --onlyvisible --class '^DarfinOSNotebookPopup$') || return 1
  [[ "$(xdotool getwindowname "$window")" == Bluetooth ]]
}
await_result bluetooth_title
bluetooth_contained() {
  local window
  window=$(xdotool search --onlyvisible --class '^DarfinOSNotebookPopup$') || return 1
  xwininfo -id "$window" | awk '
    /Absolute upper-left X:/ {x=$NF}
    /Absolute upper-left Y:/ {y=$NF}
    /Width:/ {w=$NF}
    /Height:/ {h=$NF}
    END {exit !(x >= 0 && y >= 28 && w > 0 && w <= 370 && x+w <= 1280 && h > 0 && y+h <= 720)}
  '
}
await_result bluetooth_contained
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/bluetooth-off-720p.png"
fi
xdotool key Tab Return
await_result test -f "$tmp/bt-enabled"
await_result bluetooth_contained
xdotool key Escape
await_result popup_closed

fastfetch_output=$(sh "$profile/session.sh" fastfetch --pipe)
[[ "$fastfetch_output" == *Fastfetch* && "$fastfetch_output" == *SYSTEM* ]]
[[ -s "$profile/logo.png" && -s "$XDG_CONFIG_HOME/fastfetch/logo.png" ]]
xdotool key super+F4
fastfetch_visible() { xdotool search --onlyvisible --name '^DarfinOS · Fastfetch$' >/dev/null 2>&1; }
await_result fastfetch_visible
xdotool key super+q
fastfetch_closed() { ! fastfetch_visible; }
await_result fastfetch_closed

# Exercise the real XDG/GTK launch path with two disposable desktop entries.
mkdir -p "$XDG_DATA_HOME/applications"
cat > "$XDG_CONFIG_HOME/mimeapps.list" <<'MIME'
[Default Applications]
x-scheme-handler/http=darfinos-test-browser.desktop;
x-scheme-handler/https=darfinos-test-browser.desktop;
inode/directory=darfinos-test-files.desktop;
MIME
cat > "$XDG_DATA_HOME/applications/darfinos-test-browser.desktop" <<'BROWSER_APP'
[Desktop Entry]
Type=Application
Name=DarfinOS Test Browser
Exec=touch browser-started
Path=/
NoDisplay=true
MimeType=x-scheme-handler/http;x-scheme-handler/https;
BROWSER_APP
cat > "$XDG_DATA_HOME/applications/darfinos-test-files.desktop" <<'FILES_APP'
[Desktop Entry]
Type=Application
Name=DarfinOS Test File Manager
Exec=touch files-started
Path=/
NoDisplay=true
MimeType=inode/directory;
FILES_APP
sed -i "s|^Path=/$|Path=$HOME|" "$XDG_DATA_HOME"/applications/*.desktop
xdotool key super+b
await_result test -f "$HOME/browser-started"
sh "$profile/session.sh" files
await_result test -f "$HOME/files-started"
xdotool key super+e
thunar_visible() { xdotool search --onlyvisible --class '^Thunar$' >/dev/null 2>&1; }
await_result thunar_visible
thunar_window=$(xdotool search --onlyvisible --class '^Thunar$' | head -1)
thunar_pid=$(xdotool getwindowpid "$thunar_window")
tr '\0' '\n' <"/proc/$thunar_pid/environ" | grep -Fx 'GTK_THEME=DarfinOS-Notebook'
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/files-720p.png"
fi
i3-msg '[class="^Thunar$"] kill' >/dev/null
bar_mapped

terminal_visible() { xdotool search --onlyvisible --class '^XTerm$' >/dev/null 2>&1; }
xdotool key super+Return
await_result terminal_visible
xdotool key super+shift+0
xdotool key super+0
workspace_focused() {
  i3-msg -t get_workspaces | python -c 'import json, sys; assert any(w["focused"] and w["num"] == int(sys.argv[1]) for w in json.load(sys.stdin))' "$1" 2>/dev/null
}
await_result workspace_focused 10
await_result terminal_visible
xdotool key super+ctrl+Tab
await_result workspace_focused 1
xdotool key super+ctrl+Tab
await_result workspace_focused 10
xdotool key super+shift+q
xdotool key super+1
await_result workspace_focused 1

# Verify task actions and Alt+Tab using separate, ordinary i3 windows.
xterm -T 'Teste A' -name task-a -e sleep 50 &
xterm -T 'Teste B' -name task-b -e sleep 50 &
focused_title() { [[ "$(xdotool getactivewindow getwindowname)" == "$1" ]]; }
task_state() {
  python - "$profile" "$@" <<'STATE'
import sys
sys.path.insert(0, sys.argv[1])
from windows import snapshot
title, key, value = sys.argv[2:]
assert any(w.title == title and bool(getattr(w, key)) == (value == "yes") for w in snapshot())
STATE
}
await_result task_state 'Teste A' hidden no
await_result task_state 'Teste B' hidden no
i3-msg '[instance="^task-a$"] focus' >/dev/null
await_result focused_title 'Teste A'
xdotool keydown Alt_L key Tab
switcher_visible() { xdotool search --onlyvisible --class '^DarfinOSAltTab$' >/dev/null 2>&1; }
await_result switcher_visible
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/alt-tab-720p.png"
fi
xdotool keyup Alt_L
await_result focused_title 'Teste B'
xdotool keydown Alt_L key Tab
await_result switcher_visible
xdotool key Escape keyup Alt_L
await_result focused_title 'Teste B'
xdotool keydown Alt_L key Tab key Shift+Tab keyup Alt_L
await_result focused_title 'Teste B'
xdotool key super+m
await_result task_state 'Teste B' hidden yes
await_result focused_title 'Teste A'
xdotool key super+shift+m
await_result task_state 'Teste B' hidden no
await_result task_state 'Teste B' floating no
await_result focused_title 'Teste B'
xdotool key super+ctrl+m
await_result task_state 'Teste B' maximized yes
await_result task_state 'Teste B' floating yes
bar_mapped
xdotool key super+ctrl+m
await_result task_state 'Teste B' maximized no
await_result task_state 'Teste B' floating no
xdotool key super+shift+space
await_result task_state 'Teste B' floating yes
xdotool key super+m
await_result task_state 'Teste B' hidden yes
xdotool key super+shift+m
await_result task_state 'Teste B' hidden no
await_result task_state 'Teste B' floating yes

# The streamed module exposes only IDs, no titles or shell code from apps.
task_dock_ready() {
  grep -Fq 'session.sh" window-focus ' "$tmp/tasks.log" &&
    grep -Fq 'session.sh" window-list-minimized:' "$tmp/tasks.log"
}
sh "$profile/session.sh" window-dock > "$tmp/tasks.log" &
status_pid=$!
xdotool key super+m
await_result task_dock_ready
i3-msg '[instance="^task-(a|b)$"] kill' >/dev/null
kill "$status_pid"
wait "$status_pid" || :
status_pid=

xdotool key super+F7
settings_visible() { xdotool search --onlyvisible --class '^DarfinOSNotebookSettings$' >/dev/null 2>&1; }
await_result settings_visible
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window root "$DARFINOS_PREVIEW_DIR/settings-720p.png"
fi
xdotool key Escape
python - "$profile" <<'PREFERENCES'
import sys
sys.path.insert(0, sys.argv[1])
from settings import DEFAULTS, OVERRIDES, render, write_preferences
data = render(dict(DEFAULTS, inner=12, mouse=False))
write_preferences(data)
assert OVERRIDES.read_text() == data
PREFERENCES
i3 -C -c "$XDG_CONFIG_HOME/i3/config"

# Toggle via the configured keybinding, and verify that a hidden bar can return.
xdotool key super+shift+b
await_result bar_hidden
xdotool key super+shift+b
await_result bar_mapped
[[ "$(xdotool getwindowpid "$(xdotool search --onlyvisible --name '^darfinos-notebook-bar$')")" == "$bar_pid" ]]

python - "$profile" <<'WALLPAPER'
import base64
import json
from pathlib import Path
import sys
profile = Path(sys.argv[1])
image = profile / "test wallpaper.png"
image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jXioAAAAASUVORK5CYII="))
(profile / "desktop.json").write_text(json.dumps({"wallpaper": str(image)}))
WALLPAPER
python "$profile/desktop.py" desktop-start
xprop -root _XROOTPMAP_ID | grep -q 'pixmap id #'

bar_has_height() {
  local window
  window=$(xdotool search --onlyvisible --name '^darfinos-notebook-bar$') || return 1
  [[ "$window" != *$'\n'* ]] && xwininfo -id "$window" 2>/dev/null | grep -Eq "Height:[[:space:]]+$1$"
}
# X11 can reuse a window ID on restart. Change a visible setting to prove the
# config was actually read again, and ensure a second dock was not created.
sed -i 's/^height = 28px$/height = 32px/' "$profile/polybar.ini"
xdotool key super+shift+c
await_result bar_has_height 32
sed -i 's/^height = 32px$/height = 28px/' "$profile/polybar.ini"
xdotool key super+shift+c
await_result bar_has_height 28

pocket_visible() {
  i3-msg -t get_tree | python -c '
import json, sys
def check(node, workspace=""):
    if node["type"] == "workspace":
        workspace = node["name"]
    if "darfinos-pocket" in node.get("marks", []):
        return workspace != "__i3_scratch"
    return any(check(child, workspace) for child in node["nodes"] + node["floating_nodes"])
sys.exit(check(json.load(sys.stdin)) != (sys.argv[1] == "yes"))
' "$1"
}
sh "$profile/session.sh" pocket
await_result pocket_visible yes
sh "$profile/session.sh" pocket
await_result pocket_visible no
sh "$profile/session.sh" pocket
await_result pocket_visible yes

dunst_ready() { [[ "$(dunstctl is-paused 2>/dev/null)" == false ]]; }
await_result dunst_ready
dunstify -a DarfinOS "DarfinOS" "Notificações prontas"
notification_visible() { [[ "$(dunstctl count displayed)" == 1 ]]; }
await_result notification_visible
dunstctl close-all
dunstctl history-pop
await_result notification_visible
dunstctl close-all
dunstctl set-paused true
[[ "$(dunstctl is-paused)" == true ]]
dunstctl set-paused false
echo 'i3 Notebook: X11 720p, Polybar geometry and toggling, cursor, wallpaper, Rofi click, audio sliders, calendar, session, Fastfetch, XDG launchers, workspace keys, Alt+Tab, media dock, themed Thunar, contained Bluetooth popup, window dock, minimize/maximize, graphical preferences, scratchpad and Dunst verified.'

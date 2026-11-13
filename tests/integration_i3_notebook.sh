#!/usr/bin/env bash
# Headless X11 test. Run only in a disposable environment with the profile packages.
set -euo pipefail
if [[ "${1:-}" != "--dbus" ]]; then
  exec dbus-run-session -- bash "$0" --dbus
fi
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
export HOME="$tmp/home" XDG_RUNTIME_DIR="$tmp/run"
export XDG_CONFIG_HOME="$HOME/.config"
mkdir -m 700 "$HOME" "$XDG_RUNTIME_DIR"
mkdir -p "$XDG_CONFIG_HOME" "$HOME/.icons/Bibata-NotebookTest/cursors"
cp /usr/share/icons/Adwaita/cursors/left_ptr "$HOME/.icons/Bibata-NotebookTest/cursors/left_ptr"
printf "[Mouse]\ncursorTheme=Bibata-NotebookTest\ncursorSize=32\n" >"$XDG_CONFIG_HOME/kcminputrc"
x_pid= i3_pid=
cleanup() {
  local status=$?
  if (( status )); then
    tail -80 "$tmp/i3.log" "$tmp/xvfb.log" >&2 || :
  fi
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
bar_is_top() {
  i3-msg -t get_bar_config notebook | python -c 'import json, sys; assert json.load(sys.stdin)["position"] == "top"'
}
await_result bar_is_top
cursor_loaded() { xrdb -query | grep -q 'Xcursor.theme:.*Bibata-NotebookTest'; }
await_result cursor_loaded

# Verify clickable launcher blocks are emitted by the real status process.
python - "$profile/status.toml" <<'STATUS'
import json
import os
import subprocess
import sys
from time import monotonic
with subprocess.Popen(["i3status-rs", sys.argv[1]], stdin=subprocess.DEVNULL,
                      stdout=subprocess.PIPE, text=True, env=dict(os.environ, SHELL="/bin/sh")) as status:
    try:
        header = json.loads(status.stdout.readline())
        assert header["click_events"]
        assert status.stdout.readline().strip() == "["
        wanted = {"Apps", "Janelas", "Atalhos", "Fundo"}
        deadline = monotonic() + 8
        for line in status.stdout:
            blocks = json.loads(line.strip().strip(","))
            if wanted <= {b["full_text"].strip() for b in blocks}:
                break
            if monotonic() >= deadline:
                raise AssertionError(f"Launcher blocks missing: {blocks}")
        else:
            raise AssertionError("i3status-rs ended before publishing the launcher")
    finally:
        status.terminate()
STATUS

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
sh "$profile/session.sh" desktop-start
xprop -root _XROOTPMAP_ID | grep -q 'pixmap id #'

bar_has_mode() { i3-msg -t get_bar_config notebook | python -c 'import json, sys; assert json.load(sys.stdin)["mode"] == sys.argv[1]' "$1" 2>/dev/null; }
i3-msg 'bar mode toggle notebook' >/dev/null
await_result bar_has_mode hide
i3-msg 'bar mode toggle notebook' >/dev/null
await_result bar_has_mode dock

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
dunstify --app-name DarfinOS "DarfinOS" "Notificações prontas"
notification_visible() { [[ "$(dunstctl count displayed)" == 1 ]]; }
await_result notification_visible
dunstctl close-all
dunstctl history-pop
await_result notification_visible
dunstctl close-all
dunstctl set-paused true
[[ "$(dunstctl is-paused)" == true ]]
dunstctl set-paused false
echo 'i3 Notebook: X11 720p, cursor, wallpaper, top bar, launchers, scratchpad, Rofi and Dunst verified.'

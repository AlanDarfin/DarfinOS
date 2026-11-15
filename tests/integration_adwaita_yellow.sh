#!/usr/bin/env bash
# Explicit, isolated global-theme smoke. Downloads only with --download.
# Requires GTK3/4 GI, Xvfb, xdotool, chezmoi, Papirus and ImageMagick.
set -euo pipefail
if [[ "${1:-}" != --dbus ]]; then
  exec dbus-run-session -- bash "$0" --dbus "$@"
fi
shift
cd "$(dirname "$0")/.."
case "${1:-}" in
  --archive) [[ $# == 2 ]] || exit 2; archive=$(realpath "$2") ;;
  --download) [[ $# == 1 ]] || exit 2; archive= ;;
  *) echo "Usage: bash tests/integration_adwaita_yellow.sh --archive PINNED_TARBALL | --download" >&2; exit 2 ;;
esac
source_root=$PWD
tmp=$(mktemp -d)
export HOME="$tmp/home" XDG_CONFIG_HOME="$tmp/home/.config" XDG_DATA_HOME="$tmp/home/.local/share" XDG_CACHE_HOME="$tmp/home/.cache" XDG_RUNTIME_DIR="$tmp/run"
mkdir -m 700 "$HOME" "$XDG_RUNTIME_DIR"
unset GTK_THEME GTK2_RC_FILES
export XDG_CURRENT_DESKTOP=DarfinOSTest NO_AT_BRIDGE=1
x_pid= widget_pid=
cleanup() {
  local status=$?
  [[ -z "$widget_pid" ]] || kill "$widget_pid" 2>/dev/null || :
  [[ -z "$x_pid" ]] || kill "$x_pid" 2>/dev/null || :
  if (( status )); then
    for log in "$tmp"/*.log; do [[ ! -f "$log" ]] || tail -n 60 "$log" >&2; done
  fi
  rm -rf "$tmp"
}
trap cleanup EXIT
if [[ -n "$archive" ]]; then
  python3 scripts/adwaita_yellow.py --archive "$archive"
else
  python3 scripts/adwaita_yellow.py
fi
# Install assets only, without borrowing personal desktop configuration.
python3 - <<'PY'
import importlib.util
import os
from pathlib import Path
spec=importlib.util.spec_from_file_location('papirus', 'scripts/papirus_yellow.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
source=Path(os.environ.get('DARFINOS_TEST_ICONS_ROOT','/usr/share/icons'))
module.install_theme(Path.home()/'.icons', source)
PY
mkdir -p "$XDG_CONFIG_HOME/gtk-3.0" "$XDG_CONFIG_HOME/gtk-4.0"
for gtk in 3 4; do
  printf '.personal-style-fixture { padding: 2px; }\n' > "$XDG_CONFIG_HOME/gtk-$gtk.0/gtk.css"
done
python3 darfinos_control.py style adwaita-yellow --apply --all-files
grep -Fq personal-style-fixture "$XDG_CONFIG_HOME/gtk-3.0/gtk.css"
grep -Fq personal-style-fixture "$XDG_CONFIG_HOME/gtk-4.0/gtk.css"
Xvfb -displayfd 3 -screen 0 1280x720x24 -nolisten tcp 3>"$tmp/display" >"$tmp/xvfb.log" 2>&1 &
x_pid=$!
for ((n=0;n<50;n++)); do [[ ! -s "$tmp/display" ]] || break; sleep .1; done
export DISPLAY=":$(cat "$tmp/display")"
for gtk in 3 4; do
  timeout 15 python - "$gtk" <<'PY'
import gi
from pathlib import Path
import sys
major=int(sys.argv[1])
gi.require_version('Gtk',f'{major}.0');gi.require_version('Gdk',f'{major}.0')
from gi.repository import Gtk,Gdk
Gtk.init() if major==4 else Gtk.init([])
window=Gtk.Window()
settings=Gtk.Settings.get_default()
assert settings.get_property('gtk-theme-name')==('Adwaita-yellow-dark' if major==3 else 'Adwaita')
assert settings.get_property('gtk-font-name')=='DejaVu Sans 10'
assert settings.get_property('gtk-icon-theme-name')=='Papirus-Yellow'
assert settings.get_property('gtk-application-prefer-dark-theme') is True
if major==3:
 valid,color=window.get_style_context().lookup_color('theme_selected_bg_color')
 assert valid and tuple(round(x*255) for x in (color.red,color.green,color.blue))==(255,203,46)
 path=Gtk.IconTheme.get_default().lookup_icon('folder',48,Gtk.IconLookupFlags(0)).get_filename()
else:
 path=Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).lookup_icon('folder',None,48,1,Gtk.TextDirection.NONE,Gtk.IconLookupFlags(0)).get_file().get_path()
assert Path(path).resolve().name=='folder-yellow.svg',path
window.destroy()
print(f'Global GTK{major}: theme, Sans10, Papirus-Yellow, dark and icon resolution PASS')
PY
  python tests/i3_notebook_theme_fixture.py "$gtk" >"$tmp/gtk-$gtk.log" 2>&1 &
  widget_pid=$!
  window=
  for ((n=0;n<50;n++)); do
    window=$(xdotool search --onlyvisible --name "^Notebook GTK$gtk swatches$" 2>/dev/null | head -1) || :
    [[ -z "$window" ]] || break
    sleep .1
  done
  [[ -n "$window" ]]
  ready=0
  for ((n=0;n<30;n++)); do
    magick import -window "$window" -depth 8 -format %c histogram:info:- >"$tmp/gtk-$gtk.hist"
    if python tests/i3_notebook_color_fixture.py "$tmp/gtk-$gtk.hist" 1500 0; then ready=1; break; fi
    sleep .1
  done
  [[ "$ready" == 1 ]]
  if grep -F 'Theme parsing error' "$tmp/gtk-$gtk.log"; then exit 1; fi
  if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
    mkdir -p "$DARFINOS_PREVIEW_DIR"
    magick import -window "$window" "$DARFINOS_PREVIEW_DIR/global-adwaita-yellow-gtk$gtk.png"
  fi
  kill "$widget_pid"
  wait "$widget_pid" || :
  widget_pid=
done
# The whole test intentionally runs without GTK_THEME or an XSettings daemon.
echo 'Global Adwaita Yellow: GTK3 upstream plus GTK4 compatibility, settings, font, icons, actual gold widgets and zero blue PASS.'

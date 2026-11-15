#!/usr/bin/env bash
# Sourced by the isolated X11 smoke test. Uses only this session's Dunst.
notification_center_visible() { xdotool search --onlyvisible --name '^Notificações$' >/dev/null 2>&1; }
notification_center_closed() { ! notification_center_visible; }
notification_center_open() {
  xdotool key super+F9
  await_result notification_center_visible
  notification_window=$(xdotool search --onlyvisible --name '^Notificações$' | head -1)
  # The center loads history in a worker; let its controls become sensitive.
  sleep .5
}
notification_count_is() { [[ "$(dunstctl count "$1")" == "$2" ]]; }
notification_paused_is() { [[ "$(dunstctl is-paused)" == "$1" ]]; }

dunstctl set-paused false
dunstctl close-all
dunstify -a DarfinOS 'Histórico do Notebook' 'Uma notificação descartada continua acessível no centro.'
await_result notification_count_is displayed 1
dunstctl close-all
await_result notification_count_is displayed 0
python - "$profile" <<'HISTORY'
import sys
sys.path.insert(0, sys.argv[1])
from panel import command, notification_history
history = notification_history(command("dunstctl", "history"))
assert any(entry["summary"] == "Histórico do Notebook" for entry in history), history
HISTORY
notification_center_open
notification_center_contained() {
  xwininfo -id "$notification_window" | awk '
    /Absolute upper-left X:/ {x=$NF}
    /Absolute upper-left Y:/ {y=$NF}
    /Width:/ {w=$NF}
    /Height:/ {h=$NF}
    END {exit !(x>=0 && y>=28 && x+w<=1280 && y+h<=720)}'
}
await_result notification_center_contained
if [[ -n "${DARFINOS_PREVIEW_DIR:-}" ]]; then
  magick import -window "$notification_window" "$DARFINOS_PREVIEW_DIR/notifications-720p.png"
fi
# The first control after Close toggles Do Not Disturb using the actual daemon.
xdotool key Tab Return
await_result notification_paused_is true
sh "$profile/session.sh" notifications-status | grep -Fq '󰂛'
dunstify -a DarfinOS 'Aguardando no Notebook' 'Recebida durante o Não perturbe.'
await_result notification_count_is waiting 1
xdotool key Escape
await_result notification_center_closed
notification_center_open
xdotool key Tab Return
await_result notification_paused_is false
await_result notification_count_is displayed 1
sh "$profile/session.sh" notifications-status | grep -Fq '󰂚'
xdotool key Escape
await_result notification_center_closed
dunstctl close-all
await_result notification_count_is displayed 0
notification_center_open
# Disabled Dismiss is skipped, so the second tab reaches Restore History.
xdotool key Tab Tab Return
await_result notification_count_is displayed 1
xdotool key Escape
await_result notification_center_closed
dunstctl close-all
printf '%s\n' 'Notifications: real Dunst history, F9 center, DND queue/resume, bounded geometry and history restore verified.'

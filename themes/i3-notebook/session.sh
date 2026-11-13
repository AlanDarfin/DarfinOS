#!/bin/sh
# Started only by the i3 Notebook configuration, never by the installer.
set -eu
profile_dir="$HOME/.config/darfinos/i3-notebook"

# Look up only the named Notebook dock on this X display, never broadcast IPC.
bar_pid() {
    command -v xdotool >/dev/null || return 1
    window=$(xdotool search --name '^darfinos-notebook-bar$' 2>/dev/null | head -n 1)
    [ -n "$window" ] || return 1
    pid=$(xdotool getwindowpid "$window" 2>/dev/null) || return 1
    case "$pid" in ''|*[!0-9]*) return 1 ;; esac
    printf '%s\n' "$pid"
}

case "${1:-}" in
    desktop-start)
        python3 "$profile_dir/desktop.py" "$@"
        exec sh "$0" bar-start
        ;;
    display|wallpaper|window-title)
        exec python3 "$profile_dir/desktop.py" "$@"
        ;;
    bar-start)
        if command -v polybar >/dev/null && command -v polybar-msg >/dev/null &&
           command -v xdotool >/dev/null && [ -r "$profile_dir/polybar.ini" ]; then
            if pid=$(bar_pid); then
                exec polybar-msg -p "$pid" cmd restart
            fi
            # Only this profile uses the discovered laptop battery; no BAT0 assumption.
            for supply in /sys/class/power_supply/*; do
                if [ -r "$supply/type" ] && [ "$(cat "$supply/type")" = Battery ]; then
                    export DARFINOS_BAR_BATTERY="${supply##*/}"
                    break
                fi
            done
            # A clean exit (including logout) shouldn't start a new bar.
            polybar -c "$profile_dir/polybar.ini" notebook && exit 0
        fi
        exec i3-msg 'bar mode dock notebook'
        ;;
    bar-toggle)
        if command -v polybar-msg >/dev/null && pid=$(bar_pid); then
            exec polybar-msg -p "$pid" cmd toggle
        fi
        exec i3-msg 'bar mode toggle notebook'
        ;;
    start)
        # Don't take the D-Bus name from a notification daemon already in use.
        if command -v dunst >/dev/null; then
            dunst -conf "$profile_dir/dunstrc" &
        fi
        exec xss-lock --transfer-sleep-lock -- i3lock --nofork -c 171a1f
        ;;
    apps|windows|shortcuts)
        if command -v rofi >/dev/null; then
            case "$1" in
                apps) mode=drun ;;
                windows) mode=window ;;
                shortcuts) mode='Atalhos do i3' ;;
            esac
            shortcut_mode='Atalhos do i3:sh -c '"'"'exec sh "$HOME/.config/darfinos/i3-notebook/session.sh" shortcuts-list "$@"'"'"' sh'
            exec rofi -no-config -theme "$profile_dir/rofi.rasi" -show-icons \
                -display-drun Apps -display-window Janelas \
                -modes "drun,window,$shortcut_mode" -show "$mode"
        elif [ "$1" = apps ]; then
            exec dmenu_run
        elif [ "$1" = shortcuts ]; then
            sh "$0" shortcuts-list | tail -n +2 | dmenu -l 12 -p 'Atalhos do i3' >/dev/null
        fi
        ;;
    shortcuts-list)
        [ "$#" -eq 1 ] || exit 0
        printf '\000no-custom\037true\n'
        printf '%s\n' \
            'Super+D · Aplicativos' \
            'Super+Tab · Trocar de janela' \
            'Super+Shift+P · Escolher papel de parede' \
            'Super+F2 · Ver resolução e modo 720p' \
            'Super+Enter · Terminal' \
            'Super+Shift+Enter / Super+Grave · Terminal de bolso' \
            'Super+1/2/3 · Áreas 1 / Web / Escrita' \
            'Super+setas · Focar outra janela' \
            'Super+Shift+setas · Mover janela' \
            'Super+R · Redimensionar com as setas (Esc para sair)' \
            'Super+B · Mostrar ou ocultar a barra' \
            'Super+N · Recuperar última notificação' \
            'Super+Shift+N · Silenciar/reativar notificações' \
            'Super+Ctrl+N · Dispensar notificações' \
            'Super+L · Bloquear tela' \
            'Print · Capturar uma área' \
            'Super+Shift+C · Recarregar configuração'
        ;;
    pocket)
        # Serialize the first launch so quick presses can't create two terminals.
        if [ -n "${XDG_RUNTIME_DIR:-}" ]; then
            exec 9>"$XDG_RUNTIME_DIR/darfinos-i3-pocket.lock"
            flock -n 9 || exit 0
        fi
        if i3-msg -t get_marks | grep -Fq '"darfinos-pocket"'; then
            exec i3-msg '[con_mark="^darfinos-pocket$"] scratchpad show'
        fi
        xterm -name darfinos-pocket -title 'DarfinOS · Terminal de bolso' \
            -bg '#171a1f' -fg '#f2f2f2' -fa 'JetBrains Mono' -fs 11 9>&- &
        if [ -n "${XDG_RUNTIME_DIR:-}" ]; then
            for tick in 1 2 3 4 5 6 7 8 9 10; do
                i3-msg -t get_marks | grep -Fq '"darfinos-pocket"' && break
                sleep .1
            done
        fi
        ;;
    status)
        if command -v i3status-rs >/dev/null && [ -r "$profile_dir/status.toml" ]; then
            SHELL=/bin/sh exec i3status-rs "$profile_dir/status.toml"
        fi
        exec i3status
        ;;
    volume-up|volume-down|volume-mute|mic-mute)
        if command -v wpctl >/dev/null; then
            case "$1" in
                volume-up) wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+ && exit 0 ;;
                volume-down) wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%- && exit 0 ;;
                volume-mute) wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle && exit 0 ;;
                mic-mute) wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle && exit 0 ;;
            esac
        fi
        command -v pactl >/dev/null || exit 1
        case "$1" in
            volume-up) exec pactl set-sink-volume @DEFAULT_SINK@ +5% ;;
            volume-down) exec pactl set-sink-volume @DEFAULT_SINK@ -5% ;;
            volume-mute) exec pactl set-sink-mute @DEFAULT_SINK@ toggle ;;
            mic-mute) exec pactl set-source-mute @DEFAULT_SOURCE@ toggle ;;
        esac
        ;;
    *) exit 2 ;;
esac

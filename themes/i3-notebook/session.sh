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

# Desktop IDs are arguments, not shell commands. Launch without a start-page URL.
launch_desktop() {
    case "$1" in
        -*|*/*) return 1 ;;
        *.desktop) gtk-launch -- "$@" ;;
        *) return 1 ;;
    esac
}

shortcut_notice() {
    if command -v notify-send >/dev/null; then
        notify-send 'DarfinOS · Atalhos' "$1"
    else
        printf '%s\n' "$1" >&2
    fi
}

notebook_notice() {
    if command -v notify-send >/dev/null; then
        notify-send 'DarfinOS · i3 Notebook' "$1"
    else
        printf '%s\n' "$1" >&2
    fi
}

notebook_terminal() {
    # Configure only this terminal invocation. Do not edit the user's Xresources or shell.
    instance=$1 title=$2
    shift 2
    exec xterm -name "$instance" -title "$title" -bg '#171a1f' -fg '#f2f2f2' \
        -fa 'JetBrainsMono Nerd Font Mono' -fs 11 "$@"
}

network_running() {
    [ "$(LC_ALL=C timeout 1 nmcli -t -f RUNNING general 2>/dev/null)" = running ]
}

case "${1:-}" in
    reload)
        i3-msg reload >/dev/null
        exec sh "$0" desktop-start
        ;;
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
        if [ -x /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 ]; then
            /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
        fi
        if command -v nm-applet >/dev/null; then nm-applet & fi
        if command -v blueman-applet >/dev/null; then blueman-applet & fi
        # Don't take the D-Bus name from a notification daemon already in use.
        if command -v dunst >/dev/null; then
            dunst -conf "$profile_dir/dunstrc" &
        fi
        exec xss-lock --transfer-sleep-lock -- i3lock --nofork -c 171a1f
        ;;
    audio|calendar|system|network|sink|source)
        exec /usr/bin/python3 "$profile_dir/panel.py" "$1"
        ;;
    mixer)
        exec pavucontrol
        ;;
    network-terminal)
        if network_running; then
            notebook_terminal darfinos-network 'DarfinOS · Wi-Fi e rede' -geometry 70x20 -e nmtui
        fi
        notebook_notice 'NetworkManager não está ativo. A configuração de rede existente foi preservada.'
        ;;
    network-editor)
        exec nm-connection-editor
        ;;
    network-status)
        if ! network_running; then
            printf '󰖪 Rede\n'
        else
            devices=$(LC_ALL=C timeout 1 nmcli -t -f TYPE,STATE device status 2>/dev/null) || devices=
            if printf '%s\n' "$devices" | grep -qx 'wifi:connected'; then
                printf '󰖩 Wi-Fi\n'
            elif printf '%s\n' "$devices" | grep -qx 'ethernet:connected'; then
                printf '󰈀 Rede\n'
            elif [ "$(LC_ALL=C timeout 1 nmcli radio wifi 2>/dev/null)" = enabled ]; then
                printf '󰖪 Wi-Fi\n'
            else
                printf '󰖪 Off\n'
            fi
        fi
        ;;
    bluetooth)
        if [ "$(systemctl is-active bluetooth.service 2>/dev/null)" != active ]; then
            notebook_notice 'Se houver adaptador Bluetooth, habilite o serviço pela etapa Bluetooth do DarfinOS.'
        fi
        exec blueman-manager
        ;;
    bluetooth-status)
        case "$(LC_ALL=C timeout 1 bluetoothctl show 2>/dev/null)" in
            *'Powered: yes'*) printf '󰂯 BT\n' ;;
            *'Powered: no'*) printf '󰂲 Off\n' ;;
            *) printf '󰂲 —\n' ;;
        esac
        ;;
    terminal)
        notebook_terminal darfinos-terminal 'DarfinOS · Terminal'
        ;;
    fastfetch-window)
        notebook_terminal darfinos-fastfetch 'DarfinOS · Fastfetch' -hold -geometry 87x26 -e sh "$0" fastfetch
        ;;
    fastfetch)
        shift
        exec fastfetch --config "$profile_dir/fastfetch.jsonc" --logo "$profile_dir/logo.png" --logo-type chafa "$@"
        ;;
    dnd)
        exec dunstctl set-paused toggle
        ;;
    lock)
        exec i3lock -c 171a1f
        ;;
    power)
        menu() {
            rofi -no-config -theme "$profile_dir/rofi.rasi" -dmenu -no-custom -p "$1"
        }
        choice=$(printf '%s\n' 'Suspender' 'Sair da sessão' 'Reiniciar' 'Desligar' | menu Sessão) || exit 0
        confirm=$(printf '%s\n' 'Cancelar' "$choice" | menu 'Confirmar ação') || exit 0
        [ "$confirm" = "$choice" ] || exit 0
        case "$choice" in
            Suspender) exec systemctl suspend ;;
            'Sair da sessão') exec i3-msg exit ;;
            Reiniciar) exec systemctl reboot ;;
            Desligar) exec systemctl poweroff ;;
        esac
        ;;
    browser)
        app=$(xdg-settings get default-web-browser 2>/dev/null) || app=
        if [ -z "$app" ]; then
            app=$(xdg-mime query default x-scheme-handler/https 2>/dev/null) || app=
        fi
        launch_desktop "$app" || shortcut_notice 'Defina um navegador padrão nos aplicativos do sistema.'
        ;;
    files)
        app=$(xdg-mime query default inode/directory 2>/dev/null) || app=
        launch_desktop "$app" "$HOME" || shortcut_notice 'Defina um gerenciador de arquivos padrão para abrir pastas.'
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
            'Super+Enter · Terminal' \
            'Super+B · Navegador padrão' \
            'Super+E · Pasta pessoal no gerenciador padrão' \
            'Super+D · Aplicativos' \
            'Super+Tab · Trocar de janela' \
            'Super+Shift+Enter / Super+Grave · Terminal de bolso' \
            'Super+1–9 / Super+0 · Ir para áreas 1–10' \
            'Super+Shift+1–9 / Super+Shift+0 · Mover janela para áreas 1–10' \
            'Super+Ctrl+Tab · Voltar à área anterior' \
            'Super+setas · Focar outra janela' \
            'Super+Shift+setas · Mover janela' \
            'Super+Shift+Q · Fechar janela' \
            'Super+F · Tela cheia' \
            'Super+Shift+Espaço · Alternar janela flutuante' \
            'Super+H / Super+V · Dividir na horizontal / vertical' \
            'Super+W / Super+S · Abas / pilha' \
            'Super+Ctrl+E · Alternar divisão horizontal / vertical' \
            'Super+R · Redimensionar com as setas (Esc para sair)' \
            'Super+F2 · Ver resolução e modo 720p' \
            'Super+F3 · Controles de áudio e microfone' \
            'Super+F4 · Fastfetch do DarfinOS' \
            'Super+F5 · Calendário' \
            'Super+F6 · Menu de sessão' \
            'Super+Shift+P · Escolher papel de parede' \
            'Super+Shift+B · Mostrar ou ocultar a barra' \
            'Super+N · Recuperar última notificação' \
            'Super+Shift+N · Silenciar/reativar notificações' \
            'Super+Ctrl+N · Dispensar notificações' \
            'Print / Super+Shift+S · Capturar uma área' \
            'Shift+Print · Copiar tela inteira' \
            'Super+L · Bloquear tela' \
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
            -bg '#171a1f' -fg '#f2f2f2' -fa 'JetBrainsMono Nerd Font Mono' -fs 11 9>&- &
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
            volume-up)
                current=$(LC_ALL=C pactl get-sink-volume @DEFAULT_SINK@ | awk -F/ 'NR == 1 {gsub(/[^0-9]/, "", $2); print $2}')
                case "$current" in ''|*[!0-9]*) exit 1 ;; esac
                if [ "$current" -ge 95 ]; then
                    exec pactl set-sink-volume @DEFAULT_SINK@ 100%
                fi
                exec pactl set-sink-volume @DEFAULT_SINK@ +5%
                ;;
            volume-down) exec pactl set-sink-volume @DEFAULT_SINK@ -5% ;;
            volume-mute) exec pactl set-sink-mute @DEFAULT_SINK@ toggle ;;
            mic-mute) exec pactl set-source-mute @DEFAULT_SOURCE@ toggle ;;
        esac
        ;;
    *) exit 2 ;;
esac

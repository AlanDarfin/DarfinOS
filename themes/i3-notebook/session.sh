#!/bin/sh
# Started only by the i3 Notebook configuration, never by the installer.
set -eu
profile_dir="$HOME/.config/darfinos/i3-notebook"

# Polybar calls itself on IPC restart, so rediscover the mapped dock.
set_bar_cursor() {
    expected_pid=${1:-}
    attempts=0
    while [ "$attempts" -lt 50 ]; do
        win=$(xdotool search --onlyvisible --name '^darfinos-notebook-bar$' 2>/dev/null | head -n 1)
        if [ -n "$win" ]; then
            got=$(xdotool getwindowpid "$win" 2>/dev/null) || got=
            if [ -z "$expected_pid" ] || [ "$got" = "$expected_pid" ]; then
                /usr/bin/python3 "$profile_dir/desktop.py" bar-cursor "$win"
                return
            fi
        fi
        attempts=$((attempts + 1))
        sleep 0.1
    done
}

# Scoped to the Notebook launcher tree (Rofi, terminal, dock and shortcuts).
# Do not publish these variables to systemd or the session D-Bus.
theme_dir="$HOME/.themes/DarfinOS-Notebook"
appearance_dir="$profile_dir/appearance"
if [ -r "$theme_dir/gtk-3.0/gtk.css" ]; then
    export GTK_THEME=DarfinOS-Notebook
fi
if [ -r "$theme_dir/gtk-2.0/gtkrc" ]; then
    export GTK2_RC_FILES="$theme_dir/gtk-2.0/gtkrc"
fi
if [ -r "$appearance_dir/share/color-schemes/DarfinOSNotebook.colors" ]; then
    case ":${XDG_DATA_DIRS:-/usr/local/share:/usr/share}:" in
        *":$appearance_dir/share:"*) ;;
        *) export XDG_DATA_DIRS="$appearance_dir/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" ;;
    esac
fi
# Flatpak desktop copies are visible only to Notebook launchers. The original
# exported entries and persistent Flatpak overrides remain unchanged.
flatpak_data_dir="$profile_dir/flatpak/share"
if [ -d "$flatpak_data_dir/applications" ]; then
    case ":${XDG_DATA_DIRS:-/usr/local/share:/usr/share}:" in
        *":$flatpak_data_dir:"*) ;;
        *) export XDG_DATA_DIRS="$flatpak_data_dir:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" ;;
    esac
fi
if [ -d "$appearance_dir" ]; then
    # Share colors, fonts and icons without changing application config homes.
    case ":${XDG_CONFIG_DIRS:-/etc/xdg}:" in
        *":$appearance_dir:"*) ;;
        *) export XDG_CONFIG_DIRS="$appearance_dir:${XDG_CONFIG_DIRS:-/etc/xdg}" ;;
    esac
    if [ -r /usr/lib/qt6/plugins/styles/libkvantum.so ] ||
       [ -r /usr/lib/qt/plugins/styles/libkvantum.so ]; then
        export QT_STYLE_OVERRIDE=kvantum
        export QT_QPA_PLATFORMTHEME=gtk3
    fi
fi

# XSETTINGS and Xresources name the theme. LibXcursor also has to be able to
# find cursors installed by Labs in XDG_DATA_HOME/icons, including in pop-ups.
# Only graphical launchers need this, not the bar's periodic status commands.
case "${1:-}" in
    desktop-start|start|bar-start|audio|brightness|calendar|network|bluetooth|system|desktop-menu|settings|display|wallpaper|monitors|appearance|screenshot|mixer|network-terminal|network-editor|terminal|fastfetch-window|browser|notebook-files|dolphin|qt4|qt-themed|themed|files|apps|windows|shortcuts|pocket)
        if [ -r "$profile_dir/desktop.py" ] &&
            cursor=$(/usr/bin/python3 "$profile_dir/desktop.py" cursor-env) && [ -n "$cursor" ]; then
            {
                IFS= read -r XCURSOR_THEME
                IFS= read -r XCURSOR_SIZE
                IFS= read -r XCURSOR_PATH
            } <<CURSOR
$cursor
CURSOR
            export XCURSOR_THEME XCURSOR_SIZE XCURSOR_PATH
        fi
        ;;
esac

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
        *.desktop)
            if [ -r "$profile_dir/flatpak.py" ] &&
               [ -r "$flatpak_data_dir/applications/$1" ]; then
                /usr/bin/python3 "$profile_dir/flatpak.py" desktop "$@"
            else
                gtk-launch -- "$@"
            fi
            ;;
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
        # i3 caches its frame cursor. Prepare Xresources before restarting the
        # WM so GTK windows inherit the same cursor as the root and Qt apps.
        # Restart keeps applications open and reruns exec_always desktop-start.
        python3 "$profile_dir/desktop.py" desktop-start
        exec i3-msg restart
        ;;
    desktop-start)
        before_cursor=
        if command -v xrdb >/dev/null; then
            before_cursor=$(xrdb -query 2>/dev/null | sed -n '/^Xcursor\.\(theme\|size\):/p')
        fi
        python3 "$profile_dir/desktop.py" "$@"
        if command -v xrdb >/dev/null; then
            after_cursor=$(xrdb -query 2>/dev/null | sed -n '/^Xcursor\.\(theme\|size\):/p')
            if [ -n "$after_cursor" ] && [ "$before_cursor" != "$after_cursor" ]; then
                # Initial login also needs one restart after a cursor change.
                # The next run sees the same resources and starts the helpers.
                exec i3-msg restart
            fi
        fi
        if command -v flatpak >/dev/null && [ -r "$profile_dir/flatpak.py" ]; then
            /usr/bin/python3 "$profile_dir/flatpak.py" refresh || :
        fi
        # Existing switcher instances retain the X11 grabs across i3 reloads.
        /usr/bin/python3 "$profile_dir/switcher.py" &
        /usr/bin/python3 "$profile_dir/mouse.py" &
        exec sh "$0" bar-start
        ;;
    display|wallpaper|window-title)
        exec python3 "$profile_dir/desktop.py" "$@"
        ;;
    bar-start)
        if command -v polybar >/dev/null && command -v polybar-msg >/dev/null &&
           command -v xdotool >/dev/null && [ -r "$profile_dir/polybar.ini" ]; then
            if pid=$(bar_pid); then
                polybar-msg -p "$pid" cmd restart || exit $?
                sleep 0.5
                set_bar_cursor
                exit 0
            fi
            # Only this profile uses the discovered laptop battery; no BAT0 assumption.
            for supply in /sys/class/power_supply/*; do
                if [ -r "$supply/type" ] && [ "$(cat "$supply/type")" = Battery ]; then
                    export DARFINOS_BAR_BATTERY="${supply##*/}"
                    break
                fi
            done
            # A clean exit (including logout) shouldn't start a new bar.
            polybar -c "$profile_dir/polybar.ini" notebook &
            pid=$!
            set_bar_cursor "$pid" &
            wait "$pid" && exit 0
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
    audio|brightness|calendar|system|network|bluetooth|sink|source|desktop-menu|brightness-status)
        exec /usr/bin/python3 "$profile_dir/panel.py" "$@"
        ;;
    window-*)
        action=${1#window-}
        shift
        exec /usr/bin/python3 "$profile_dir/windows.py" "$action" "$@"
        ;;
    settings)
        exec /usr/bin/python3 "$profile_dir/settings.py"
        ;;
    monitors|appearance)
        if [ "$1" = monitors ]; then app=arandr; else app=lxappearance; fi
        if command -v "$app" >/dev/null; then exec "$app"; fi
        notebook_notice 'Atualize o i3 Notebook nos Labs para instalar esta ferramenta.'
        ;;
    screenshot)
        shift
        exec flameshot "$@"
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
    bluetooth-status)
        exec /usr/bin/python3 "$profile_dir/panel.py" bluetooth-status
        ;;
    media)
        shift
        exec /usr/bin/python3 "$profile_dir/media.py" "$@"
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
        exec sh "$0" system
        ;;
    power-action)
        case "${2:-}" in
            suspend|reboot|poweroff) exec systemctl "$2" ;;
            logout) exec i3-msg exit ;;
            *) exit 2 ;;
        esac
        ;;
    browser)
        app=$(xdg-settings get default-web-browser 2>/dev/null) || app=
        if [ -z "$app" ]; then
            app=$(xdg-mime query default x-scheme-handler/https 2>/dev/null) || app=
        fi
        launch_desktop "$app" || shortcut_notice 'Defina um navegador padrão nos aplicativos do sistema.'
        ;;
    notebook-files)
        if command -v thunar >/dev/null; then
            GTK_THEME="${GTK_THEME:-Adwaita:dark}" exec thunar --window "$HOME"
        fi
        exec sh "$0" files
        ;;
    dolphin)
        shift
        exec dolphin --new-window "$@"
        ;;
    qt4|qt-themed)
        mode=$1
        shift
        [ "$#" -gt 0 ] || exit 2
        # The Workshop changes only Kvantum's theme key with undo support.
        # Keep the application's real configuration directory and saved state.
        if [ "$mode" = qt4 ]; then
            unset QT_STYLE_OVERRIDE QT_QPA_PLATFORMTHEME
        fi
        exec "$@"
        ;;
    flatpak)
        shift
        exec /usr/bin/python3 "$profile_dir/flatpak.py" "$@"
        ;;
    themed)
        shift
        [ "$#" -gt 0 ] || exit 2
        exec "$@"
        ;;
    files)
        app=$(xdg-mime query default inode/directory 2>/dev/null) || app=
        case "$app" in
            org.kde.dolphin.desktop|dolphin.desktop)
                if command -v dolphin >/dev/null; then exec dolphin --new-window "$HOME"; fi
                ;;
        esac
        launch_desktop "$app" "$HOME" || shortcut_notice 'Defina um gerenciador de arquivos padrão para abrir pastas.'
        ;;
    apps|windows|shortcuts)
        if [ "$1" = apps ] && command -v flatpak >/dev/null && [ -r "$profile_dir/flatpak.py" ]; then
            /usr/bin/python3 "$profile_dir/flatpak.py" refresh >/dev/null || :
            # This process was started before a first refresh created the path.
            case ":${XDG_DATA_DIRS:-/usr/local/share:/usr/share}:" in
                *":$flatpak_data_dir:"*) ;;
                *) export XDG_DATA_DIRS="$flatpak_data_dir:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" ;;
            esac
        fi
        if command -v rofi >/dev/null; then
            case "$1" in
                apps) mode=drun ;;
                windows) mode=window ;;
                shortcuts) mode='Atalhos do i3' ;;
            esac
            shortcut_mode='Atalhos do i3:sh -c '"'"'exec sh "$HOME/.config/darfinos/i3-notebook/session.sh" shortcuts-list "$@"'"'"' sh'
            icons=Adwaita
            if [ -r "$HOME/.icons/Papirus-Yellow/index.theme" ]; then icons=Papirus-Yellow; fi
            if [ -r "$profile_dir/flatpak.py" ]; then
                run_command=$(/usr/bin/python3 "$profile_dir/flatpak.py" rofi-command)
            else
                run_command='{cmd}'
            fi
            exec rofi -no-config -theme "$profile_dir/rofi.rasi" -show-icons -icon-theme "$icons" \
                -run-command "$run_command" -theme-str 'configuration { drun { gio-launch: false; } }' \
                -display-drun Apps -display-window Janelas \
                -drun-reload-desktop-cache -modes "drun,window,$shortcut_mode" -show "$mode"
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
            'Super+E · Explorador de arquivos (Thunar)' \
            'Super+D · Aplicativos' \
            'Alt+Tab / Alt+Shift+Tab · Percorrer janelas; solte Alt para abrir' \
            'Super+Tab · Buscar janela no Rofi' \
            'Super+Shift+Enter / Super+Grave · Terminal de bolso' \
            'Super+1–9 / Super+0 · Ir para áreas 1–10' \
            'Super+Shift+1–9 / Super+Shift+0 · Mover janela para áreas 1–10' \
            'Super+Ctrl+Tab · Voltar à área anterior' \
            'Super+setas · Focar outra janela' \
            'Super+Shift+setas · Mover janela' \
            'Super+Q · Fechar janela' \
            'Super+F · Tela cheia' \
            'Super+M / Super+Shift+M · Minimizar / Restaurar última janela' \
            'Super+Ctrl+M · Maximizar ou restaurar sem esconder a barra' \
            'Super+Shift+Espaço · Alternar janela flutuante' \
            'Super+H / Super+V · Dividir na horizontal / vertical' \
            'Super+W / Super+S · Abas / pilha' \
            'Super+Ctrl+E · Alternar divisão horizontal / vertical' \
            'Super+R · Redimensionar com as setas (Esc para sair)' \
            'Super+F2 · Ver resolução e modo 720p' \
            'Super+F3 · Controles de áudio e microfone' \
            'Super+F4 · Fastfetch do DarfinOS' \
            'Super+F5 · Calendário' \
            'Super+F6 · Encerrar sessão, suspender, reiniciar e desligar' \
            'Super+F7 · Preferências gráficas do i3' \
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
    brightness-up|brightness-down)
        case "$1" in brightness-up) step=5%+ ;; *) step=5%- ;; esac
        exec brightnessctl --class=backlight --min-value=1 set "$step"
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

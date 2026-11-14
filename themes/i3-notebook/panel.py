"""Small GTK3 popups for the Notebook bar. Only the GUI needs PyGObject."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import re
import subprocess
import sys

PROFILE = Path(__file__).resolve().parent
ACCENT = "{{ .accent }}"
TARGETS = {
    "sink": ("@DEFAULT_AUDIO_SINK@", "@DEFAULT_SINK@"),
    "source": ("@DEFAULT_AUDIO_SOURCE@", "@DEFAULT_SOURCE@"),
}


@dataclass(frozen=True)
class Audio:
    backend: str
    volume: int
    muted: bool


def command(*args, timeout=0.8):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "LC_ALL": "C"})
        return result.stdout if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def audio_state(kind):
    wire, pulse = TARGETS[kind]
    wp = command("wpctl", "get-volume", wire) or ""
    if match := re.fullmatch(r"Volume:\s+(\d+(?:\.\d+)?)(\s+\[MUTED\])?\s*", wp):
        return Audio("wire", min(100, round(float(match[1]) * 100)), bool(match[2]))
    volume = command("pactl", f"get-{kind}-volume", pulse) or ""
    mute = (command("pactl", f"get-{kind}-mute", pulse) or "").strip()
    levels = re.findall(r"\b(\d+)%", volume)
    if levels and mute in ("Mute: yes", "Mute: no"):
        return Audio("pulse", min(100, round(sum(map(int, levels)) / len(levels))), mute.endswith("yes"))
    return None


def audio_change(kind, backend, volume=None):
    wire, pulse = TARGETS[kind]
    if volume is not None:
        value = f"{max(0, min(100, int(volume)))}%"
        if backend == "wire":
            return command("wpctl", "set-volume", "-l", "1", wire, value) is not None
        return command("pactl", f"set-{kind}-volume", pulse, value) is not None
    if backend == "wire":
        return command("wpctl", "set-mute", wire, "toggle") is not None
    return command("pactl", f"set-{kind}-mute", pulse, "toggle") is not None


def audio_label(kind):
    state = audio_state(kind)
    on, off = {"sink": ("󰕾", "󰖁"), "source": ("󰍬", "󰍭")}[kind]
    if state is None:
        return f"{off} —"
    return f"{off if state.muted else on} {'Mudo' if state.muted else str(state.volume) + '%'}"


def bluetooth_state():
    if (command("systemctl", "is-active", "bluetooth.service") or "").strip() != "active":
        return "inactive"
    adapter = command("bluetoothctl", "show", timeout=1.5)
    if adapter is None or not re.search(r"^Controller ", adapter, re.M):
        return "no-adapter"
    if re.search(r"^\s+Powered: yes\s*$", adapter, re.M):
        return "on"
    if re.search(r"^\s+Powered: no\s*$", adapter, re.M):
        return "off"
    return "unknown"


def power_controls(Gtk, container, button, request):
    confirmation = Gtk.Box(spacing=8)
    confirm = button("Confirmar", lambda: request(pending), confirmation)
    cancel = button("Cancelar", lambda: choose(None), confirmation)
    description = Gtk.Label(xalign=0, wrap=True, max_width_chars=40)
    pending = None
    names = {"logout": "Encerrar sessão", "reboot": "Reiniciar",
             "poweroff": "Desligar", "suspend": "Suspender"}

    def choose(action):
        nonlocal pending
        pending = action
        description.set_text(f"{names[action]} agora?" if action else "")
        description.set_visible(action is not None)
        confirmation.set_visible(action is not None)
        if action:
            # Pressing Enter twice on an action should not commit immediately.
            cancel.grab_focus()

    actions = Gtk.Box(spacing=6, homogeneous=True)
    for action, name in names.items():
        button(name, lambda a=action: choose(a), actions)
    confirmation.set_no_show_all(True)
    description.set_no_show_all(True)
    confirm.show()
    cancel.show()
    container.add(actions)
    container.add(description)
    container.add(confirmation)


def brightness_level():
    # Machine-readable output avoids localized percentages and keyboard LEDs.
    output = command("brightnessctl", "--class=backlight", "--machine-readable", "info") or ""
    match = re.search(r",([0-9]{1,3})%,", output.splitlines()[0]) if output else None
    if match and 0 <= int(match[1]) <= 100:
        return int(match[1])
    return None


def popup_position(area, size, anchor=None):
    left, top, available_width, available_height = area
    width, height = size
    right = left + max(0, available_width - width)
    bottom = top + max(0, available_height - height)
    if anchor is None:
        return max(left, right - 8), top
    x, y = anchor
    return min(max(left, x), right), min(max(top, y), bottom)


def popup_bounds(monitor, workarea):
    """GDK can report a work area shared by all outputs. Intersect it first."""
    x = max(monitor.x, workarea.x)
    y = max(monitor.y + 28, workarea.y)
    right = min(monitor.x + monitor.width, workarea.x + workarea.width)
    bottom = min(monitor.y + monitor.height, workarea.y + workarea.height)
    if right <= x or bottom <= y:
        return monitor.x, monitor.y + 28, monitor.width, max(1, monitor.height - 28)
    return x, y, right - x, bottom - y


def popup(page, anchor=None):
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError):
        command("notify-send", "DarfinOS", "Atualize as dependências do i3 Notebook nos Labs.")
        return 1

    ok, _ = Gtk.init_check(None)
    if not ok:
        return 1
    settings = Gtk.Settings.get_default()
    # Set before creating windows so popup cursors agree with the X11 root,
    # even when another toolkit initialized before XSETTINGS was ready.
    if theme := os.environ.get("XCURSOR_THEME"):
        settings.set_property("gtk-cursor-theme-name", theme)
    if (size := os.environ.get("XCURSOR_SIZE", "")).isdecimal():
        settings.set_property("gtk-cursor-theme-size", int(size))
    style = Gtk.CssProvider()
    style.load_from_data("""
        #notebook-popup { background: #20242b; color: #f2f2f2; border: 1px solid @ACCENT@; }
        #notebook-popup label { color: #f2f2f2; }
        #notebook-popup .heading { font-size: 16px; font-weight: bold; }
        #notebook-popup .hint { color: #c0c4cd; font-size: 12px; }
        #notebook-popup button { background: #2c313a; color: #f2f2f2; border-color: #454a54;
                                 background-image: none; box-shadow: none; text-shadow: none; }
        #notebook-popup button:hover { background: #454a54; }
        #notebook-popup scale trough { background: #454a54; min-height: 5px; }
        #notebook-popup scale highlight { background: @ACCENT@; }
        #notebook-popup scale slider { background: @ACCENT@; }
        #notebook-popup calendar { color: #f2f2f2; background: #252930; }
        #notebook-popup calendar:selected { color: #171a1f; background: @ACCENT@; }
    """.replace("@ACCENT@", ACCENT).encode())
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    window = Gtk.Window(title={"audio": "Áudio", "brightness": "Brilho", "desktop-menu": "Área de trabalho", "calendar": "Calendário",
                               "network": "Wi-Fi e rede", "bluetooth": "Bluetooth", "system": "Sessão"}[page])
    window.set_name("notebook-popup")
    window.set_wmclass("darfinos-notebook-popup", "DarfinOSNotebookPopup")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_skip_taskbar_hint(True)
    window.connect("destroy", lambda *_: Gtk.main_quit())

    def keypress(_window, event):
        if event.keyval == Gdk.KEY_Escape:
            window.destroy()
            return True
        return False

    window.connect("key-press-event", keypress)
    display = window.get_display()
    _, x, y = display.get_default_seat().get_pointer().get_position()
    monitor = display.get_monitor_at_point(*(anchor or (x, y)))
    area = popup_bounds(monitor.get_geometry(), monitor.get_workarea())
    _, _, available_width, available_height = area
    width_limit = min(360 if page == "bluetooth" else 330, max(1, available_width - 16))
    window.set_default_size(width_limit, -1)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=14)
    if page in ("bluetooth", "desktop-menu"):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_propagate_natural_height(True)
        scroll.set_max_content_height(max(1, available_height - 8))
        scroll.add(box)
        window.add(scroll)
    else:
        window.add(box)
    heading = Gtk.Box(spacing=8)
    box.add(heading)
    title = Gtk.Label(label=window.get_title(), xalign=0)
    title.get_style_context().add_class("heading")
    heading.pack_start(title, True, True, 0)
    close = Gtk.Button(label="Fechar")
    close.connect("clicked", lambda *_: window.destroy())
    heading.pack_end(close, False, False, 0)
    worker = None

    def launch(*args):
        window.destroy()
        try:
            subprocess.Popen(args, stdin=subprocess.DEVNULL)
        except OSError:
            command("notify-send", "DarfinOS", "Não consegui abrir o aplicativo. Confira as dependências nos Labs.")

    def button(label, callback, parent=box):
        control = Gtk.Button(label=label)
        control.connect("clicked", lambda *_: callback())
        parent.add(control)
        return control

    if page == "desktop-menu":
        for label, action in (("Aplicativos", "apps"), ("Terminal", "terminal"),
                              ("Arquivos", "notebook-files"), ("Papel de parede", "wallpaper"),
                              ("Tela e resolução", "display"), ("Preferências do i3", "settings")):
            button(label, lambda a=action: launch("sh", str(PROFILE / "session.sh"), a))
    elif page == "brightness":
        value = brightness_level()
        if value is None:
            box.add(Gtk.Label(label="Nenhum controle de brilho de tela disponível.", xalign=0))
        else:
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
            scale.get_accessible().set_name("Brilho da tela")
            scale.set_value(max(1, value))
            box.add(scale)
            feedback = Gtk.Label(xalign=0)
            box.add(feedback)
            pending = 0
            worker = ThreadPoolExecutor(max_workers=1)

            def changed(widget):
                nonlocal pending
                if pending:
                    GLib.source_remove(pending)
                level = round(widget.get_value())

                def commit():
                    nonlocal pending
                    pending = 0
                    job = worker.submit(command, "brightnessctl", "--class=backlight",
                                        "--min-value=1", "set", f"{level}%")

                    def update():
                        if job.result() is None:
                            feedback.set_text("Não foi possível ajustar o brilho.")
                        return False

                    job.add_done_callback(lambda _: GLib.idle_add(update))
                    return False

                pending = GLib.timeout_add(75, commit)

            scale.connect("value-changed", changed)
            window.connect("show", lambda *_: scale.grab_focus())
    elif page == "calendar":
        calendar = Gtk.Calendar()
        calendar.set_display_options(Gtk.CalendarDisplayOptions.SHOW_HEADING |
                                     Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES)
        box.add(calendar)

        def today():
            from datetime import date
            now = date.today()
            calendar.select_month(now.month - 1, now.year)
            calendar.select_day(now.day)

        button("Hoje", today)
    elif page == "audio":
        rows = {}
        worker = ThreadPoolExecutor(max_workers=1)
        hint = Gtk.Label(xalign=0)
        hint.get_style_context().add_class("hint")
        busy = False
        initial_focus = True

        def paint(states):
            nonlocal busy, initial_focus
            busy = False
            for kind, state in states.items():
                row = rows[kind]
                if row["pending"]:
                    continue
                row["state"] = state
                row["scale"].set_sensitive(state is not None)
                row["mute"].set_sensitive(state is not None)
                row["mute"].set_label("Reativar" if state and state.muted else "Silenciar")
                if state:
                    row["scale"].handler_block(row["handler"])
                    row["scale"].set_value(state.volume)
                    row["scale"].handler_unblock(row["handler"])
                row["level"].set_text(f"{state.volume}%" if state else "—")
            if initial_focus:
                initial_focus = False
                first = next((rows[kind]["scale"] for kind, state in states.items() if state), None)
                if first is not None and window.get_focus() in (None, close):
                    first.grab_focus()
            hint.set_text("Sem áudio disponível. Confira PipeWire ou PulseAudio."
                          if not any(states.values()) else "Dispositivos padrão da sessão.")
            return False

        def refresh():
            nonlocal busy
            if not busy and not any(row["pending"] or row["writing"] for row in rows.values()):
                busy = True
                future = worker.submit(lambda: {kind: audio_state(kind) for kind in rows})
                future.add_done_callback(lambda f: GLib.idle_add(paint, f.result()))
            return True

        def write(kind, volume=None):
            row = rows[kind]
            state = row["state"]
            if state:
                row["writing"] += 1

                def done(future):
                    row["writing"] -= 1
                    if not future.result():
                        hint.set_text("Não foi possível ajustar este dispositivo.")
                    refresh()
                    return False

                future = worker.submit(audio_change, kind, state.backend, volume)
                future.add_done_callback(lambda f: GLib.idle_add(done, f))

        def slide(scale, kind):
            row = rows[kind]
            if not row["state"]:
                return
            value = round(scale.get_value())
            row["level"].set_text(f"{value}%")
            if row["pending"]:
                GLib.source_remove(row["pending"])

            def apply():
                row["pending"] = 0
                write(kind, value)
                return False

            row["pending"] = GLib.timeout_add(80, apply)

        for kind, label in (("sink", "Saída do sistema"), ("source", "Microfone")):
            line = Gtk.Box(spacing=8)
            line.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
            level = Gtk.Label(label="—", width_chars=4)
            line.pack_start(level, False, False, 0)
            mute = button("Silenciar", lambda k=kind: write(k), line)
            mute.set_sensitive(False)
            box.add(line)
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            scale.get_accessible().set_name(label)
            scale.set_draw_value(False)
            scale.set_sensitive(False)
            handler = scale.connect("value-changed", slide, kind)
            rows[kind] = dict(level=level, scale=scale, mute=mute, handler=handler,
                              state=None, pending=0, writing=0)
            box.add(scale)
        box.add(hint)
        button("Mixer e dispositivos…", lambda: launch("pavucontrol"))
        refresh()
        GLib.timeout_add_seconds(1, refresh)
    elif page == "network":
        status = Gtk.Label(xalign=0, wrap=True, max_width_chars=39)
        box.add(status)
        worker = ThreadPoolExecutor(max_workers=1)

        def load():
            running = (command("nmcli", "-t", "-f", "RUNNING", "general") or "").strip() == "running"
            if not running:
                return None, None
            radio = (command("nmcli", "radio", "wifi") or "").strip()
            devices = (command("nmcli", "-t", "-f", "TYPE,STATE", "device", "status") or "").splitlines()
            return radio, devices

        current_radio = None

        def paint_network(result, failed=False):
            nonlocal current_radio
            radio, devices = result
            current_radio = radio
            if devices is None:
                status.set_text("NetworkManager não está ativo. Sua configuração de rede foi mantida.")
            elif failed:
                status.set_text("Não foi possível alterar o Wi-Fi. Confira as permissões e o bloqueio do adaptador.")
            elif "wifi:connected" in devices:
                status.set_text("Conectado por Wi-Fi.")
            elif "ethernet:connected" in devices:
                status.set_text("Conectado por cabo.")
            else:
                status.set_text("Nenhuma conexão Wi-Fi ou cabeada ativa.")
            toggle.set_label("Desligar Wi-Fi" if radio == "enabled" else "Ligar Wi-Fi")
            toggle.set_sensitive(radio in ("enabled", "disabled") and any(d.startswith("wifi:") for d in devices or []))
            connect.set_sensitive(devices is not None)
            editor.set_sensitive(devices is not None)
            return False

        def refresh_network(action=None):
            toggle.set_sensitive(False)

            def apply():
                failed = action is not None and command("nmcli", "radio", "wifi", action) is None
                return load(), failed

            future = worker.submit(apply)
            future.add_done_callback(lambda f: GLib.idle_add(paint_network, *f.result()))

        toggle = button("Ligar Wi-Fi", lambda: refresh_network(
            "off" if current_radio == "enabled" else "on"))
        connect = button("Escolher e conectar a uma rede…", lambda: launch(
            "sh", str(PROFILE / "session.sh"), "network-terminal"))
        editor = button("Editar conexões…", lambda: launch("nm-connection-editor"))
        connect.set_sensitive(False)
        editor.set_sensitive(False)
        status.set_text("Verificando a rede…")
        refresh_network()
    elif page == "bluetooth":
        from gi.repository import Pango
        status = Gtk.Label(label="Verificando o Bluetooth…", xalign=0, wrap=True,
                           wrap_mode=Pango.WrapMode.WORD_CHAR, width_chars=1, max_width_chars=30)
        box.add(status)
        worker = ThreadPoolExecutor(max_workers=1)
        state = None
        messages = {
            "inactive": "Serviço Bluetooth (BlueZ) parado. Inicie o serviço para procurar adaptadores.",
            "no-adapter": "Nenhum adaptador Bluetooth detectado. Confira o modo avião, o bloqueio físico ou o adaptador USB.",
            "off": "Adaptador encontrado. Bluetooth desligado.",
            "on": "Bluetooth ligado. Abra os dispositivos para conectar ou parear.",
            "unknown": "Adaptador encontrado, mas não consegui ler se ele está ligado. Tente o gerenciador.",
        }

        def paint(result, failure):
            nonlocal state
            state = result
            status.set_text(failure or messages[state])
            toggle.set_label({"inactive": "Iniciar serviço Bluetooth", "on": "Desligar Bluetooth"}.get(
                state, "Ligar Bluetooth"))
            toggle.set_sensitive(state in ("inactive", "on", "off"))
            manager.set_sensitive(state in ("on", "off", "unknown"))
            refresh.set_sensitive(True)
            return False

        def probe(action=None):
            for control in (toggle, manager, refresh):
                control.set_sensitive(False)

            def apply():
                failure = None
                if action == "inactive":
                    if command("systemctl", "start", "bluetooth.service", timeout=25) is None:
                        failure = "Não consegui iniciar o BlueZ. Confira a permissão ou rode a etapa Bluetooth do DarfinOS."
                elif action in ("on", "off"):
                    power = "off" if action == "on" else "on"
                    if command("bluetoothctl", "power", power, timeout=3) is None:
                        failure = "Não consegui mudar o estado do Bluetooth. Confira o modo avião ou um bloqueio (rfkill)."
                return bluetooth_state(), failure

            future = worker.submit(apply)
            future.add_done_callback(lambda f: GLib.idle_add(paint, *f.result()))

        def open_manager():
            try:
                proc = subprocess.Popen(["blueman-manager"], stdin=subprocess.DEVNULL)
            except OSError:
                status.set_text("Blueman não encontrado. Rode Labs → i3 Notebook para instalar.")
                return

            def opened():
                code = proc.poll()
                if code is None or code == 0:
                    window.destroy()
                else:
                    status.set_text("O Blueman não abriu. Verifique o adaptador e tente de novo.")
                return False

            GLib.timeout_add(650, opened)

        toggle = button("Iniciar serviço Bluetooth", lambda: probe(state))
        manager = button("Abrir dispositivos · Blueman", open_manager)
        refresh = button("Verificar novamente", probe)
        probe()
    else:
        def request_power(action):
            if action is None:
                return
            window.destroy()
            try:
                result = subprocess.run(["sh", str(PROFILE / "session.sh"), "power-action", action],
                                        capture_output=True, text=True, timeout=30)
                if not result.returncode:
                    return
            except (OSError, subprocess.TimeoutExpired):
                pass
            command("notify-send", "DarfinOS · Sessão", "Não foi possível executar a ação. Confira a sessão e as permissões.")

        power_controls(Gtk, box, button, request_power)
        box.add(Gtk.Separator())
        for label, action in (("Bloquear tela", "lock"), ("Não perturbe · alternar", "dnd"),
                              ("Wi-Fi e rede", "network"), ("Dispositivos Bluetooth", "bluetooth"),
                              ("Tela e resolução", "display"), ("Papel de parede", "wallpaper"),
                              ("Preferências do i3", "settings"), ("Sobre o sistema · Fastfetch", "fastfetch-window")):
            button(label, lambda a=action: launch("sh", str(PROFILE / "session.sh"), a))

    window.connect("focus-out-event", lambda *_: window.destroy() or False)
    def align(*_):
        # Use the negotiated bounds rather than the requested GTK width.
        position = popup_position(area, window.get_size(), anchor)
        if window.get_position() != position:
            window.move(*position)
        return False

    def mapped(*_):
        GLib.idle_add(align)
        return False

    window.connect("map-event", mapped)
    window.connect("size-allocate", mapped)
    window.move(*popup_position(area, (width_limit, 1), anchor))
    window.show_all()
    window.present()
    Gtk.main()
    if worker:
        worker.shutdown(wait=False, cancel_futures=True)
    return 0


def main():
    action = sys.argv[1] if len(sys.argv) >= 2 else ""
    anchor = None
    if action == "desktop-menu" and len(sys.argv) == 4:
        try:
            anchor = tuple(map(int, sys.argv[2:]))
        except ValueError:
            return 2
    elif len(sys.argv) != 2:
        return 2
    if action in ("sink", "source"):
        print(audio_label(action))
        return 0
    if action == "bluetooth-status":
        state = bluetooth_state()
        print({"on": "󰂯 BT", "off": "󰂲 Off"}.get(state, "󰂲 —"))
        return 0
    if action == "brightness-status":
        if (level := brightness_level()) is not None:
            print(f"󰃠 {level}%")
        return 0
    if action not in ("audio", "brightness", "calendar", "network", "bluetooth", "system", "desktop-menu"):
        return 2
    if runtime := os.environ.get("XDG_RUNTIME_DIR"):
        display = re.sub(r"[^A-Za-z0-9_.-]", "_", os.environ.get("DISPLAY", ""))
        with (Path(runtime) / f"darfinos-i3-popup-{display}-{action}.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return 0
            return popup(action, anchor)
    return popup(action, anchor)


if __name__ == "__main__":
    sys.exit(main())

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


def command(*args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=0.8,
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


def popup(page):
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError):
        command("notify-send", "DarfinOS", "Atualize as dependências do i3 Notebook nos Labs.")
        return 1

    ok, _ = Gtk.init_check(None)
    if not ok:
        return 1
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
    window = Gtk.Window(title={"audio": "Áudio", "calendar": "Calendário",
                               "network": "Wi-Fi e rede", "system": "Sessão"}[page])
    window.set_name("notebook-popup")
    window.set_wmclass("darfinos-notebook-popup", "DarfinOSNotebookPopup")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_skip_taskbar_hint(True)
    window.set_default_size(330, -1)
    window.connect("destroy", lambda *_: Gtk.main_quit())

    def keypress(_window, event):
        if event.keyval == Gdk.KEY_Escape:
            window.destroy()
            return True
        return False

    window.connect("key-press-event", keypress)
    display = window.get_display()
    _, x, y = display.get_default_seat().get_pointer().get_position()
    monitor = display.get_monitor_at_point(x, y)
    bounds = monitor.get_geometry()
    area = monitor.get_workarea()

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=14)
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

    if page == "calendar":
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

        def paint(states):
            nonlocal busy
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
    else:
        for label, action in (("Wi-Fi e rede", "network"), ("Dispositivos Bluetooth", "bluetooth"),
                              ("Sobre o sistema · Fastfetch", "fastfetch-window"),
                              ("Tela e resolução", "display"), ("Papel de parede", "wallpaper"),
                              ("Não perturbe · alternar", "dnd"), ("Bloquear tela", "lock")):
            button(label, lambda a=action: launch("sh", str(PROFILE / "session.sh"), a))

        # Confirmation happens in a separate themed menu, so focus-out still works here.
        button("Suspender, sair ou desligar…", lambda: launch("sh", str(PROFILE / "session.sh"), "power"))

    window.connect("focus-out-event", lambda *_: window.destroy() or False)
    window.show_all()
    # i3 respects client movement for floating windows. Keep the popup on the
    # monitor where it was opened and clear both the Polybar and the fallback bar.
    width, _ = window.get_size()
    window.move(area.x + max(0, area.width - width - 8), max(area.y, bounds.y + 28))
    window.present()
    Gtk.main()
    if worker:
        worker.shutdown(wait=False, cancel_futures=True)
    return 0


def main():
    action = sys.argv[1] if len(sys.argv) == 2 else ""
    if action in ("sink", "source"):
        print(audio_label(action))
        return 0
    if action not in ("audio", "calendar", "network", "system"):
        return 2
    if runtime := os.environ.get("XDG_RUNTIME_DIR"):
        display = re.sub(r"[^A-Za-z0-9_.-]", "_", os.environ.get("DISPLAY", ""))
        with (Path(runtime) / f"darfinos-i3-popup-{display}.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return 0
            return popup(action)
    return popup(action)


if __name__ == "__main__":
    sys.exit(main())

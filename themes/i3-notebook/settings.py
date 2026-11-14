"""Graphical, profile-only settings. The Workshop never replaces the overrides."""
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

from windows import PROFILE

CONFIG = Path.home() / ".config/i3/config"
OVERRIDES = PROFILE / "preferences.conf"
INCLUDE = 'include "$HOME/.config/darfinos/i3-notebook/preferences.conf"'
DEFAULTS = {"inner": 8, "outer": 2, "mouse": True, "smart": True, "layout": "default"}
LAYOUTS = {"default": "Lado a lado", "tabbed": "Abas", "stacking": "Pilha"}


def preferences(data):
    result = DEFAULTS.copy()
    patterns = {
        "inner": r"gaps inner (\d+)", "outer": r"gaps outer (\d+)",
        "mouse": r"focus_follows_mouse (yes|no)", "smart": r"smart_gaps (on|off)",
        "layout": r"workspace_layout (default|tabbed|stacking)",
    }
    for line in data.splitlines():
        for key, pattern in patterns.items():
            if match := re.fullmatch(pattern, line.strip()):
                value = match[1]
                if key in ("inner", "outer"):
                    result[key] = min(int(value), 32)
                elif key in ("mouse", "smart"):
                    result[key] = value in ("yes", "on")
                else:
                    result[key] = value
    return result


def render(values):
    return ("# Gerenciado pelas Preferências do i3 Notebook.\n"
            f"gaps inner {values['inner']}\n"
            f"gaps outer {values['outer']}\n"
            f"focus_follows_mouse {'yes' if values['mouse'] else 'no'}\n"
            f"smart_gaps {'on' if values['smart'] else 'off'}\n"
            f"workspace_layout {values['layout']}\n")


def write_preferences(data):
    original = CONFIG.read_text()
    if INCLUDE not in original.splitlines():
        raise ValueError("Aplique o perfil i3 Notebook atualizado pela Oficina primeiro.")
    # Check the proposed config without editing the real one. Use the same
    # directories for relative includes, and no shell interpolation.
    paths = []
    try:
        with tempfile.NamedTemporaryFile("w", dir=PROFILE, prefix=".prefs-", delete=False) as prefs:
            paths.append(Path(prefs.name))
            prefs.write(data)
        with tempfile.NamedTemporaryFile("w", dir=CONFIG.parent, prefix=".notebook-check-", delete=False) as cfg:
            paths.append(Path(cfg.name))
            cfg.write(original.replace(INCLUDE, f"include {shlex.quote(prefs.name)}"))
        check = subprocess.run(["i3", "-C", "-c", cfg.name], text=True, capture_output=True, timeout=12)
        if check.returncode:
            raise ValueError("O i3 rejeitou a configuração. Nenhuma preferência foi gravada.")
        os.replace(prefs.name, OVERRIDES)
    finally:
        for path in paths:
            path.unlink(missing_ok=True)


def main():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk

    if not Gtk.init_check(None)[0]:
        return 1
    window = Gtk.Window(title="Preferências do i3 Notebook")
    window.set_wmclass("darfinos-notebook-settings", "DarfinOSNotebookSettings")
    window.set_default_size(438, -1)
    window.set_position(Gtk.WindowPosition.CENTER)
    window.connect("destroy", lambda *_: Gtk.main_quit())
    window.connect("key-press-event", lambda w, e: (w.destroy() or True) if e.keyval == Gdk.KEY_Escape else False)
    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=16)
    window.add(root)
    grid = Gtk.Grid(column_spacing=18, row_spacing=8)
    root.add(grid)

    def spin():
        return Gtk.SpinButton.new_with_range(0, 32, 1)

    controls = {"inner": spin(), "outer": spin(), "mouse": Gtk.Switch(halign=Gtk.Align.START),
                "smart": Gtk.Switch(halign=Gtk.Align.START), "layout": Gtk.ComboBoxText()}
    for key, text in LAYOUTS.items():
        controls["layout"].append(key, text)
    for i, (key, title) in enumerate((("inner", "Espaço entre janelas (px)"),
                                     ("outer", "Margem externa (px)"),
                                     ("mouse", "Foco segue o mouse"),
                                     ("smart", "Sem margens com uma janela"),
                                     ("layout", "Layout de novas áreas"))):
        label = Gtk.Label.new_with_mnemonic(title)
        label.set_xalign(0)
        label.set_hexpand(True)
        label.set_mnemonic_widget(controls[key])
        grid.attach(label, 0, i, 1, 1)
        grid.attach(controls[key], 1, i, 1, 1)

    def fill(values):
        for key, widget in controls.items():
            if key in ("inner", "outer"):
                widget.set_value(values[key])
            elif key == "layout":
                widget.set_active_id(values[key])
            else:
                widget.set_active(values[key])

    def note(text):
        feedback.set_text(text)

    def save(*_):
        current = {"inner": controls["inner"].get_value_as_int(), "outer": controls["outer"].get_value_as_int(),
                   "mouse": controls["mouse"].get_active(), "smart": controls["smart"].get_active(),
                   "layout": controls["layout"].get_active_id()}
        try:
            write_preferences(render(current))
            proc = subprocess.run(["i3-msg", "reload"], capture_output=True, timeout=4)
            note("Preferências aplicadas." if proc.returncode == 0
                 else "Preferências salvas. Recarregue o i3 para aplicar.")
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            note(str(exc))

    def button(container, label, callback):
        item = Gtk.Button(label=label)
        item.connect("clicked", callback)
        container.add(item)

    def helper(action):
        subprocess.Popen(["sh", str(PROFILE / "session.sh"), action], stdin=subprocess.DEVNULL)

    common = Gtk.Box(spacing=8, homogeneous=True)
    button(common, "Monitores · ARandR", lambda *_: helper("monitors"))
    button(common, "Aparência GTK", lambda *_: helper("appearance"))
    root.add(common)
    tools = Gtk.Box(spacing=8, homogeneous=True)
    button(tools, "Papel de parede", lambda *_: helper("wallpaper"))
    button(tools, "Lista de atalhos", lambda *_: helper("shortcuts"))
    root.add(tools)
    bottom = Gtk.Box(spacing=8, homogeneous=True)
    button(bottom, "Preencher padrões", lambda *_: fill(DEFAULTS))
    button(bottom, "Aplicar", save)
    root.add(bottom)
    feedback = Gtk.Label(xalign=0, wrap=True, max_width_chars=45)
    root.add(feedback)
    try:
        fill(preferences(OVERRIDES.read_text()) if OVERRIDES.exists() else DEFAULTS)
    except (OSError, ValueError) as exc:
        fill(DEFAULTS)
        note(str(exc))
    window.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

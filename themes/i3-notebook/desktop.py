#!/usr/bin/env python3
"""Notebook-only desktop preferences. Never source user paths as shell code."""
from __future__ import annotations

import configparser
import ctypes
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
PROFILE = HOME / ".config/darfinos/i3-notebook"
SETTINGS = PROFILE / "desktop.json"
MODE_720P = "1280x720"


def run(*args, **kwargs):
    return subprocess.run(args, text=True, check=False, **kwargs)


def read_settings():
    try:
        data = json.loads(SETTINGS.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(**changes):
    data = read_settings()
    data.update(changes)
    fd, temp = tempfile.mkstemp(dir=PROFILE)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp, SETTINGS)
    finally:
        Path(temp).unlink(missing_ok=True)


def notify(message):
    if shutil.which("notify-send"):
        run("notify-send", "DarfinOS · i3 Notebook", message)
    else:
        print(message, file=sys.stderr)


def load_background(path):
    if not isinstance(path, str) or not path or not Path(path).is_file() or not shutil.which("feh"):
        return False
    return run("feh", "--no-fehbg", "--bg-fill", "--", str(Path(path).absolute()),
               capture_output=True).returncode == 0


def apply_background(path):
    if load_background(path):
        return
    default = PROFILE / "wallpaper.svg"
    if default.is_file() and shutil.which("rsvg-convert"):
        with tempfile.TemporaryDirectory(prefix="darfinos-wallpaper-") as folder:
            image = Path(folder) / "wallpaper.png"
            rendered = run("rsvg-convert", "-o", str(image), str(default), capture_output=True)
            if rendered.returncode == 0 and load_background(str(image)):
                return
    if shutil.which("xsetroot"):
        run("xsetroot", "-solid", "#252930")


def wallpaper_picker():
    if not shutil.which("zenity") or not shutil.which("feh"):
        notify("Instale as dependências atualizadas de i3 Notebook nos Labs.")
        return
    pictures = HOME / "Imagens"
    if not pictures.is_dir():
        pictures = HOME / "Pictures"
    if not pictures.is_dir():
        pictures = HOME
    if shutil.which("rofi"):
        result = run("rofi", "-no-config", "-theme", str(PROFILE / "rofi.rasi"),
                     "-dmenu", "-no-custom", "-p", "Fundo",
                     input="Escolher imagem…\nRestaurar fundo DarfinOS\n", capture_output=True)
        if result.returncode:
            return
        if result.stdout.strip() == "Restaurar fundo DarfinOS":
            apply_background(None)
            save_settings(wallpaper=None)
            return
        if result.stdout.strip() != "Escolher imagem…":
            return
    result = run("zenity", "--file-selection", "--title=Escolher papel de parede",
                 "--filename=" + str(pictures) + "/",
                 "--file-filter=Imagens | *.png *.jpg *.jpeg *.webp *.bmp *.gif *.PNG *.JPG *.JPEG *.WEBP",
                 "--file-filter=Todos os arquivos | *", capture_output=True)
    if result.returncode:
        return
    path = result.stdout.removesuffix("\n")
    if load_background(path):
        save_settings(wallpaper=path)
    else:
        notify("Não consegui abrir a imagem. Escolha outro arquivo.")


def cursor_search_path():
    data_home = Path(os.environ.get("XDG_DATA_HOME") or HOME / ".local/share")
    default = "~/.icons:~/.local/share/icons:/usr/local/share/icons:/usr/share/icons:/usr/share/pixmaps"
    paths = [str(data_home / "icons"), str(HOME / ".icons")]
    paths += [str(Path(path).expanduser()) for path in (os.environ.get("XCURSOR_PATH") or default).split(":") if path]
    return os.pathsep.join(dict.fromkeys(paths))


def print_cursor_env():
    if preference := cursor_preference():
        theme, size, _ = preference
        print(theme, size, cursor_search_path(), sep="\n")


def cursor_preference():
    config = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        config.read(Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config") / "kcminputrc")
        theme = config.get("Mouse", "cursorTheme", fallback="")
        size = config.getint("Mouse", "cursorSize", fallback=24)
    except (configparser.Error, UnicodeError, ValueError):
        theme, size = "", 24
    size = size if 8 <= size <= 128 else 24
    roots = [Path(directory) for directory in cursor_search_path().split(os.pathsep)]
    # Prefer the exact SonicDE selection, then an installed Bibata variant.
    def pointer(directory):
        for name in ("left_ptr", "default", "arrow"):
            path = directory / "cursors" / name
            if path.is_file():
                return path
        return None
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._+-]*", theme):
        for root in roots:
            if path := pointer(root / theme):
                return theme, size, path
    for root in roots:
        for directory in sorted(root.glob("Bibata-*")):
            if not re.fullmatch(r"Bibata-[A-Za-z0-9 ._+-]+", directory.name):
                continue
            if path := pointer(directory):
                return directory.name, size, path
    return None


def set_window_pointer(window_id):
    # i3 gives its window frames an explicit cursor. Setting the actual dock
    # window avoids inheriting the frame cursor i3 cached before login setup.
    preference = cursor_preference()
    if not preference:
        return
    _, size, pointer = preference
    try:
        x11 = ctypes.CDLL("libX11.so.6")
        xcursor = ctypes.CDLL("libXcursor.so.1")
    except OSError:
        return

    dpy, xid = ctypes.c_void_p, ctypes.c_ulong
    x11.XOpenDisplay.argtypes = (ctypes.c_char_p,)
    x11.XOpenDisplay.restype = dpy
    x11.XDefineCursor.argtypes = (dpy, xid, xid)
    x11.XFreeCursor.argtypes = (dpy, xid)
    x11.XCloseDisplay.argtypes = (dpy,)
    xcursor.XcursorFilenameLoadImages.argtypes = (ctypes.c_char_p, ctypes.c_int)
    xcursor.XcursorFilenameLoadImages.restype = ctypes.c_void_p
    xcursor.XcursorImagesLoadCursor.argtypes = (dpy, ctypes.c_void_p)
    xcursor.XcursorImagesLoadCursor.restype = xid
    xcursor.XcursorImagesDestroy.argtypes = (ctypes.c_void_p,)
    if not (connection := x11.XOpenDisplay(None)):
        return
    try:
        if images := xcursor.XcursorFilenameLoadImages(os.fsencode(pointer), size):
            try:
                if cursor := xcursor.XcursorImagesLoadCursor(connection, images):
                    # The bar can exit between discovery and setting the cursor.
                    handler_type = ctypes.CFUNCTYPE(ctypes.c_int, dpy, ctypes.c_void_p)
                    ignore_error = handler_type(lambda *_: 0)
                    x11.XSetErrorHandler.argtypes = (handler_type,)
                    x11.XSetErrorHandler.restype = ctypes.c_void_p
                    x11.XSetErrorHandler(ignore_error)
                    x11.XDefineCursor(connection, window_id, cursor)
                    x11.XFreeCursor(connection, cursor)
                    x11.XCloseDisplay(connection)
                    connection = None
            finally:
                xcursor.XcursorImagesDestroy(images)
    finally:
        if connection:
            x11.XCloseDisplay(connection)


def apply_cursor():
    preference = cursor_preference()
    if preference:
        theme, size, path = preference
        if shutil.which("xrdb"):
            run("xrdb", "-nocpp", "-merge", input=f"Xcursor.theme: {theme}\nXcursor.size: {size}\n")
        if shutil.which("xsetroot"):
            run("xsetroot", "-xcf", str(path), str(size))
    # GTK can read XSETTINGS instead of Xresources. Reload our own provider,
    # but never replace the provider belonging to another desktop.
    theme_installed = (HOME / ".themes/DarfinOS-Notebook/gtk-3.0/gtk.css").is_file()
    if (theme_installed or preference) and shutil.which("xsettingsd") and shutil.which("dump_xsettings"):
        config = PROFILE / "cursor.xsettings"
        pid_file = PROFILE / "cursor.xsettings.pid"
        own_pid = None
        try:
            pid = int(pid_file.read_text())
            argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            if (pid > 1 and len(argv) >= 3 and Path(os.fsdecode(argv[0])).name == "xsettingsd"
                    and argv[1:3] == [b"-c", os.fsencode(config)]):
                own_pid = pid
        except (OSError, ValueError):
            pass
        if own_pid is None and run("dump_xsettings", capture_output=True).returncode == 0:
            return
        with tempfile.NamedTemporaryFile(mode="w", dir=PROFILE, prefix=".cursor-", delete=False) as temp:
            if theme_installed:
                icons = "Papirus-Yellow" if (HOME / ".icons/Papirus-Yellow/index.theme").is_file() else "Adwaita"
                temp.write(f'Net/ThemeName "DarfinOS-Notebook"\nNet/IconThemeName "{icons}"\n')
            if preference:
                temp.write(f'Gtk/CursorThemeName "{theme}"\nGtk/CursorThemeSize {size}\n')
        # xsettingsd reads this file at startup; keep it until the session ends or the next run.
        try:
            os.replace(temp.name, config)
            if own_pid is not None:
                try:
                    os.kill(own_pid, signal.SIGHUP)
                except ProcessLookupError:
                    pass  # The next reload can start a new provider.
            else:
                process = subprocess.Popen(["xsettingsd", "-c", str(config)], stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pid_file.write_text(str(process.pid))
        finally:
            Path(temp.name).unlink(missing_ok=True)


@dataclass
class Output:
    name: str
    modes: set[str] = field(default_factory=set)
    current: str = ""
    rate: str = ""
    geometry: str = ""

    @property
    def internal(self):
        return self.name.startswith(("eDP", "LVDS", "DSI"))


def parse_outputs(query):
    outputs = []
    output = None
    for line in query.splitlines():
        if match := re.match(r"^(\S+) connected\b(.*)", line):
            geometry = re.search(r"\b(\d+x\d+)[+-]\d+[+-]\d+", match[2])
            output = Output(match[1], geometry=geometry[1] if geometry else "")
            outputs.append(output)
        elif not line.startswith((" ", "\t")):
            output = None
        elif output and (match := re.match(r"^\s+(\d+x\d+\S*)\s+(.+)", line)):
            output.modes.add(match[1])
            if current := re.search(r"(\d+(?:\.\d+)?)\*", match[2]):
                output.current, output.rate = match[1], current[1]
    return outputs


def read_outputs():
    if not shutil.which("xrandr"):
        return []
    result = run("xrandr", "--current", capture_output=True)
    return parse_outputs(result.stdout) if result.returncode == 0 else []


def panel_for_720p(outputs):
    panels = [o for o in outputs if o.internal and o.current]
    if len(panels) == 1 and MODE_720P in panels[0].modes:
        return panels[0]
    return None


def panel_transform(output):
    """Capture the existing transform before testing 720p with a 1:1 pixel scale."""
    query = run("xrandr", "--current", "--verbose", capture_output=True)
    if query.returncode:
        return None
    active = False
    lines = query.stdout.splitlines()
    for index, line in enumerate(lines):
        if line and not line[0].isspace():
            active = line.startswith(output.name + " connected")
        if active and "Transform:" in line:
            matrix = " ".join([line.split("Transform:", 1)[1], *lines[index + 1:index + 3]]).split()
            if len(matrix) != 9 or not all(re.fullmatch(r"-?\d+(?:\.\d+)?", value) for value in matrix):
                return None
            return ",".join(matrix)
    return None


def set_mode(output, mode, rate="", *, transform=None):
    cmd = ["xrandr", "--output", output.name, "--mode", mode]
    if rate:
        cmd += ["--rate", rate]
    if transform is not None:
        cmd += ["--transform", transform]
    return run(*cmd, capture_output=True).returncode == 0


def desktop_start():
    data = read_settings()
    if data.get("mode_720p") is True:
        panel = panel_for_720p(read_outputs())
        if panel and (panel.current != MODE_720P or panel.geometry != MODE_720P):
            set_mode(panel, MODE_720P, transform="none")
    apply_background(data.get("wallpaper"))
    apply_cursor()


def display_picker():
    outputs = read_outputs()
    lines = []
    for output in outputs:
        if output.current:
            line = f"{output.name}   {output.current} @ {output.rate} Hz"
            if output.geometry and output.geometry != output.current:
                line += f"  ·  área X11 {output.geometry}"
            lines.append(line)
    panel = panel_for_720p(outputs)
    if not panel:
        lines.append("720p indisponível: a tela interna ativa precisa oferecer 1280×720 no X11.")
    summary = "\n".join(lines)
    options = ["Manter como está"]
    if panel:
        options.append("Usar 1280×720 na tela interna")
    if read_settings().get("mode_720p") is True:
        options.append("Parar de reaplicar 720p ao entrar")
    if not shutil.which("rofi"):
        notify(summary or "Sem informação de tela X11. Rode xrandr --current na sessão i3.")
        return
    result = run("rofi", "-no-config", "-theme", str(PROFILE / "rofi.rasi"),
                 "-dmenu", "-no-custom", "-p", "Tela",
                 "-mesg", summary or "Nenhuma saída X11 ativa detectada.",
                 input="\n".join(options) + "\n", capture_output=True)
    if result.returncode:
        return
    choice = result.stdout.strip()
    if choice == "Parar de reaplicar 720p ao entrar":
        save_settings(mode_720p=False)
    elif choice == "Usar 1280×720 na tela interna" and panel:
        if panel.current == MODE_720P and panel.geometry == MODE_720P:
            save_settings(mode_720p=True)
            return
        if not shutil.which("zenity"):
            notify("Instale as dependências atualizadas do i3 Notebook para testar o modo com confirmação.")
            return
        transform = panel_transform(panel)
        if transform is None:
            notify("Não consegui ler a escala atual. A resolução foi mantida.")
            return
        if not set_mode(panel, MODE_720P, transform="none"):
            set_mode(panel, panel.current, panel.rate, transform=transform)
            notify("O X11 não aceitou o modo 1280×720 nesta tela.")
            return
        try:
            keep = run("zenity", "--question", "--title=Confirmar resolução",
                       "--text=Manter 1280×720 sem escala? Se não confirmar, o modo anterior volta em 15 segundos.",
                       "--timeout=15", capture_output=True, timeout=18).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            keep = False
        if keep:
            save_settings(mode_720p=True)
        elif not set_mode(panel, panel.current, panel.rate, transform=transform):
            notify("Não consegui restaurar o modo anterior da tela.")
        apply_background(read_settings().get("wallpaper"))


def focused_title(node):
    if node.get("focused") and node.get("window"):
        return node.get("name") or ""
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        if title := focused_title(child):
            return title
    return ""


def clean_title(title):
    # Window titles come from applications. Never let them become Polybar formatting/actions.
    title = " ".join("".join(c if c.isprintable() else " " for c in title).split())
    title = title.replace("%{", "％{")
    return (title[:27] + "…" if len(title) > 28 else title) or "Área de trabalho"


def window_title():
    def show():
        try:
            tree = json.loads(run("i3-msg", "-t", "get_tree", capture_output=True).stdout)
            print(clean_title(focused_title(tree)), flush=True)
        except (OSError, ValueError):
            print("Área de trabalho", flush=True)

    with subprocess.Popen(["i3-msg", "-m", "-t", "subscribe", '["window", "workspace"]'],
                          stdout=subprocess.PIPE, text=True) as watcher:
        try:
            show()
            for line in watcher.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict) and event.get("change") in {"focus", "title", "close", "new"}:
                    show()
        finally:
            watcher.terminate()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "bar-cursor":
        if not sys.argv[2].isdecimal():
            sys.exit(2)
        set_window_pointer(int(sys.argv[2]))
        sys.exit(0)
    actions = {"desktop-start": desktop_start, "display": display_picker,
               "wallpaper": wallpaper_picker, "window-title": window_title, "cursor-env": print_cursor_env}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        sys.exit(2)
    actions[sys.argv[1]]()

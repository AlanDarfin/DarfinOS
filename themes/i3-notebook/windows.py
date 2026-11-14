"""Window actions and a compact live task list for i3 Notebook."""
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

PROFILE = Path(__file__).resolve().parent
ACCENT = "{{ .accent }}"
MIN = "darfinos-min-"
MAX = "darfinos-max-"
EXCLUDED = {"darfinos-pocket", "darfinos-notebook-popup", "darfinos-notebook-settings"}
ICONS = (
    (("firefox", "librewolf", "floorp"), "󰈹"),
    (("chromium", "chrome", "brave", "vivaldi"), "󰊯"),
    (("xterm", "alacritty", "kitty", "konsole", "terminal", "wezterm", "ghostty"), "󰆍"),
    (("obsidian", "libreoffice", "kate", "mousepad"), "󰈙"),
    (("dolphin", "thunar", "nautilus", "pcmanfm"), "󰉋"),
    (("steam", "lutris", "heroic"), "󰓓"),
    (("code", "codium", "zed", "jetbrains"), "󰨞"),
    (("vlc", "mpv", "spotify"), "󰎆"),
    (("discord", "telegram", "signal"), "󰍩"),
)


def ipc(*args):
    try:
        proc = subprocess.run(["i3-msg", *args], text=True, capture_output=True, timeout=2, check=True)
        return json.loads(proc.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def send(command):
    result = ipc(command)
    return isinstance(result, list) and bool(result) and all(part.get("success") for part in result)


@contextmanager
def lock(name, *, blocking=True):
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        yield True
        return
    display = re.sub(r"[^a-zA-Z0-9_.-]", "_", os.environ.get("DISPLAY", ""))
    with (Path(runtime) / f"darfinos-notebook-{name}-{display}.lock").open("a") as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            yield False
        else:
            yield True


def clean(text, limit=54):
    text = " ".join("".join(c if c.isprintable() else " " for c in text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


@dataclass
class Window:
    id: int
    title: str
    app: str
    workspace: str
    area: dict
    rect: dict
    floating: bool
    fullscreen: bool
    focused: bool
    marks: list

    @property
    def minimized(self):
        return next((m for m in self.marks if re.fullmatch(MIN + r"[01]-\d+", m)), None)

    @property
    def maximized(self):
        return next((m for m in self.marks if re.fullmatch(MAX + r"(?:[01])(?:_-?\d+){4}", m)), None)

    @property
    def hidden(self):
        return self.workspace == "__i3_scratch"

    @property
    def icon(self):
        return next((icon for names, icon in ICONS if any(n in self.app.casefold() for n in names)), "󰖯")


def windows(tree):
    def walk(node, ws="", area=None, floating_rect=None):
        if node.get("type") == "workspace":
            ws, area = node["name"], node.get("rect", {})
        if node.get("type") == "floating_con":
            floating_rect = node.get("rect") or {}
        if node.get("window") and ws:
            props = node.get("window_properties") or {}
            instance = props.get("instance") or ""
            marks = node.get("marks", [])
            managed_hidden = ws == "__i3_scratch" and any(m.startswith(MIN) for m in marks)
            if instance not in EXCLUDED and (not ws.startswith("__i3") or managed_hidden):
                app = props.get("class") or instance or "Janela"
                yield Window(int(node["id"]), clean(node.get("name") or app), clean(app, 24), ws, area,
                             floating_rect or node.get("rect", {}), floating_rect is not None, bool(node.get("fullscreen_mode")),
                             bool(node.get("focused")), marks)
        children = node.get("nodes", []) + node.get("floating_nodes", [])
        order = {id_: index for index, id_ in enumerate(node.get("focus", []))}
        for child in sorted(children, key=lambda c: order.get(c["id"], len(order))):
            yield from walk(child, ws, area, floating_rect)

    return list(walk(tree or {}))


def snapshot():
    return windows(ipc("-t", "get_tree"))


def criteria(window):
    return f"[con_id={window.id}]"


def unmaximize(window):
    mark = window.maximized
    original, x, y, width, height = map(int, mark[len(MAX):].split("_"))
    if original:
        return f"resize set {width} px {height} px, move absolute position {x} px {y} px, unmark {mark}"
    return f"floating disable, unmark {mark}"


def maximize(window):
    c = criteria(window)
    if window.maximized:
        commands = unmaximize(window)
    else:
        a, r = window.area, window.rect
        if not all(k in a and k in r for k in ("x", "y", "width", "height")):
            return False
        x, y, width, height = (r[key] for key in ("x", "y", "width", "height"))
        mark = f"{MAX}{int(window.floating)}_{x}_{y}_{width}_{height}"
        commands = (f"mark --add {mark}, floating enable, "
                    f"resize set {max(1, a['width'] - 8)} px {max(1, a['height'] - 8)} px, "
                    f"move absolute position {a['x'] + 4} px {a['y'] + 4} px")
    leave_fullscreen = "fullscreen disable, " if window.fullscreen else ""
    return send(f"{c} {leave_fullscreen}{commands}")


def minimize(window):
    c = criteria(window)
    restore = f"{unmaximize(window)}, " if window.maximized else ""
    original = int(window.maximized[len(MAX)] if window.maximized else window.floating)
    return send(f"{c} {restore}mark --add {MIN}{original}-{time.monotonic_ns()}, move scratchpad")


def activate(window):
    c = criteria(window)
    if window.hidden and window.minimized:
        # i3 temporarily floats a scratchpad item. Tile it again if that was its
        # original state. Cycle float once to detach originally floating windows
        # from scratchpad toggling, reusing their restored dimensions.
        floating = window.minimized[len(MIN)] == "1"
        if not send(f"{c} scratchpad show"):
            return False
        if floating:
            restored = next((w for w in snapshot() if w.id == window.id and not w.hidden), None)
            if not restored:
                return False
            x, y, width, height = (restored.rect[k] for k in ("x", "y", "width", "height"))
            geometry = f", resize set {width} px {height} px, move absolute position {x} px {y} px"
            return send(f"{c} floating disable, floating enable{geometry}, unmark {window.minimized}, focus")
        return send(f"{c} floating disable, unmark {window.minimized}, focus")
    return send(f"{c} focus")


def active_workspace(items):
    focused = next((w for w in items if w.focused), None)
    if focused:
        return focused.workspace
    return next((ws["name"] for ws in ipc("-t", "get_workspaces") or [] if ws["focused"]), "")


def dock(items, workspace):
    local = [w for w in items if not w.hidden and w.workspace == workspace]
    # Keep event ordering out of the visual position. Clicking should not move an icon.
    local.sort(key=lambda w: w.id)
    visible = local[:5]
    focused = next((w for w in local[5:] if w.focused), None)
    if focused:
        visible[-1] = focused
    output = []
    command = 'sh "$HOME/.config/darfinos/i3-notebook/session.sh"'
    def click(action, label):
        return "%{A1:" + command + " " + action + ":}" + label + "%{A}"

    for w in visible:
        on = ("%{F" + ACCENT + "}%{u" + ACCENT + "}%{+u}") if w.focused else "%{F#c0c4cd}"
        off = "%{-u}%{F-}" if w.focused else "%{F-}"
        output.append(click(f"window-focus {w.id}", f"{on} {w.icon} {off}"))
    if hidden := sum(w.hidden and bool(w.minimized) for w in items):
        output.append(click("window-list-minimized", "%{F#efd799} 󰁌 " + str(min(hidden, 99)) + " %{F-}"))
    if len(local) > len(visible):
        output.append(click("window-list", f" +{min(99, len(local) - len(visible))} "))
    return "".join(output)


def watch_dock():
    def update():
        items = snapshot()
        print(dock(items, active_workspace(items)), flush=True)

    with subprocess.Popen(["i3-msg", "-m", "-t", "subscribe", '["window","workspace"]'],
                          stdout=subprocess.PIPE, text=True) as watcher:
        try:
            for line in watcher.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict) and (event.get("success") or event.get("change") in {
                    "focus", "close", "new", "move", "mark", "init", "empty", "rename", "reload"
                }):
                    update()
        finally:
            if watcher.poll() is None:
                watcher.terminate()


def window_menu(minimized_only):
    items = [w for w in snapshot() if (w.hidden and w.minimized) or (not minimized_only and not w.hidden)]
    if not items:
        subprocess.run(["notify-send", "DarfinOS · Janelas",
                        "Nenhuma janela minimizada." if minimized_only else "Nenhuma janela aberta."], check=False)
        return 0
    rows = [f"{w.icon}  {w.title} · {('Minimizada' if w.hidden else clean(w.workspace, 18))}" for w in items]
    result = subprocess.run(["rofi", "-no-config", "-theme", str(PROFILE / "rofi.rasi"),
                             "-dmenu", "-no-custom", "-format", "i", "-p", "Minimizadas" if minimized_only else "Janelas abertas"],
                            input="\n".join(rows) + "\n", text=True, capture_output=True)
    if result.returncode == 0 and result.stdout.strip().isdigit():
        index = int(result.stdout)
        if index < len(items):
            with lock("window-actions"):
                # Refresh first in case the window was closed while the picker was up.
                chosen = next((w for w in snapshot() if w.id == items[index].id), None)
                if chosen:
                    return int(not activate(chosen))
    return 0


def main():
    action, *args = sys.argv[1:]
    if action == "dock":
        return watch_dock()
    if action in ("list", "list-minimized"):
        return window_menu(action == "list-minimized")
    with lock("window-actions"):
        items = snapshot()
        if action == "focus" and args and args[0].isdigit():
            w = next((w for w in items if w.id == int(args[0])), None)
        elif action == "restore":
            w = max((w for w in items if w.hidden and w.minimized),
                    key=lambda w: int(w.minimized.rsplit("-", 1)[-1]), default=None)
        else:
            w = next((w for w in items if w.focused), None)
        if w is None:
            return 0
        if action in ("focus", "restore"):
            return int(not activate(w))
        if action == "minimize":
            return int(not minimize(w))
        if action == "maximize":
            return int(not maximize(w))
        return 2


if __name__ == "__main__":
    sys.exit(main() if len(sys.argv) > 1 else 2)

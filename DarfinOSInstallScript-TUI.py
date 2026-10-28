#!/usr/bin/env python3
"""DarfinOS TUI+ — frontend curses sem dependências externas.

A lógica de instalação permanece no DarfinOSInstallScript.sh oficial.
Execute --help para opções e teclas disponíveis.
"""
from __future__ import annotations

import argparse
import curses
import hashlib
import difflib
import select
import signal
import pty
import fcntl
import termios
import struct
import collections
import json
import locale
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

NAME = "DarfinOSInstallScript.sh"
RAW = "https://raw.githubusercontent.com/AlanDarfin/DarfinOS/main/" + NAME
CACHE = Path.home() / ".cache/darfinos-tui"
CONFIG = Path.home() / ".config/darfinos-tui"
LOCAL = Path(__file__).resolve().parent / NAME
C = {"pink": 1, "green": 2, "red": 3, "yellow": 4, "muted": 5, "blue": 6}

@dataclass
class Step:
    name: str
    desc: str
    group: str
    deps: list[str] = field(default_factory=list)


def block(source: str, key: str) -> str:
    pattern = rf"^\s*(?:(?:declare|typeset)\s+-[a-zA-Z]+\s+)?{re.escape(key)}=\(\s*\n(.*?)^\s*\)\s*$"
    match = re.search(pattern, source, re.M | re.S)
    if not match:
        raise ValueError(f"Bloco {key} não encontrado no script. O formato pode ter mudado.")
    return match.group(1)


def parse_script(path: Path) -> list[Step]:
    source = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    pair = re.compile(r'^\s*\[([\w-]+)\]\s*=\s*["\'](.*)["\']\s*(?:#.*)?$', re.M)
    desc = dict(pair.findall(block(source, "STEP_DESC")))
    deps = {k: v.split() for k, v in pair.findall(block(source, "STEP_DEPS"))}
    result: list[Step] = []
    group = "GERAL"
    for raw in block(source, "STEPS").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            group = line.lstrip("# ").strip() or group
            continue
        for name in line.split("#", 1)[0].split():
            if not re.fullmatch(r"[\w-]+", name):
                raise ValueError(f"Nome de etapa inesperado: {name}")
            result.append(Step(name, desc.get(name, "Sem descrição"), group, deps.get(name, [])))
    if not result or len({s.name for s in result}) != len(result):
        raise ValueError("Lista de etapas vazia ou com nomes duplicados.")
    return result


def fetch_script() -> tuple[Path, str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / NAME
    try:
        request = urllib.request.Request(RAW, headers={"User-Agent": "DarfinOS-TUI/2.0", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(request, timeout=18) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000 or not data.lstrip().startswith(b"#!"):
            raise ValueError("Resposta inesperada do GitHub")
        with tempfile.NamedTemporaryFile(dir=CACHE, delete=False) as tmp:
            tmp.write(data)
            pending = Path(tmp.name)
        try:
            parse_script(pending)  # Não substituir cache válido por formato incompatível.
            pending.replace(target)
        finally:
            pending.unlink(missing_ok=True)
        return target, "GitHub/main"
    except Exception as exc:
        if target.exists():
            parse_script(target)
            return target, f"CACHE (offline: {exc})"
        raise RuntimeError(f"Falha ao baixar o instalador: {exc}") from exc


@dataclass
class State:
    steps: list[Step]
    source: str
    selected: set[str] = field(default_factory=set)
    cursor: int = 0
    search: str = ""
    yes: bool = False
    show_selected: bool = False
    message: str = ""
    statuses: dict[str, str] = field(default_factory=dict)
    profile_name: str = "default"

    @property
    def lookup(self):
        return {s.name: s for s in self.steps}

    def missing(self) -> dict[str, list[str]]:
        return {s.name: [d for d in s.deps if d not in self.selected]
                for s in self.steps if s.name in self.selected and any(d not in self.selected for d in s.deps)}

    def add_deps(self):
        known = self.lookup
        stack = list(self.selected)
        while stack:
            for dep in known[stack.pop()].deps:
                if dep in known and dep not in self.selected:
                    self.selected.add(dep)
                    stack.append(dep)
        self.message = "Dependências conhecidas incluídas na seleção."

    def filtered(self):
        term = self.search.casefold()
        return [i for i, s in enumerate(self.steps) if
                (not self.show_selected or s.name in self.selected) and
                (not term or term in (s.name + " " + s.desc + " " + s.group).casefold())]


def command(path: Path, state: State) -> list[str]:
    ordered = [s.name for s in state.steps if s.name in state.selected]
    if not ordered:
        raise ValueError("Nenhuma etapa selecionada")
    # Sempre enviar --only: evita executar tudo se o conjunto estiver vazio.
    result = ["bash", str(path), "--only", ",".join(ordered)]
    if state.yes:
        result.append("-y")
    return result


def save_profile(state: State):
    CONFIG.mkdir(parents=True, exist_ok=True)
    target = CONFIG / "profile.json"
    target.write_text(json.dumps({"selected": sorted(state.selected), "yes": state.yes}, indent=2), encoding="utf-8")
    state.message = f"Perfil salvo em {target}"


def load_profile(state: State):
    target = CONFIG / "profile.json"
    if not target.exists():
        state.message = "Nenhum perfil salvo ainda (tecla S para salvar)."
        return
    data = json.loads(target.read_text(encoding="utf-8"))
    state.selected = set(data.get("selected", [])) & set(state.lookup)
    state.yes = bool(data.get("yes", False))
    state.message = "Perfil restaurado."


def colors(name: str) -> int:
    return curses.color_pair(C[name]) if curses.has_colors() else 0


def put(win, y: int, x: int, value: str, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w - 1 or x < 0:
        return
    try:
        win.addnstr(y, x, value, max(0, w - x - 1), attr)
    except curses.error:
        pass


def line(win, y, ch="─"):
    put(win, y, 0, ch * max(0, win.getmaxyx()[1] - 1), colors("muted"))


def prompt(win, title: str, initial: str = "") -> str | None:
    h, w = win.getmaxyx()
    if h < 12 or w < 45:
        return None
    box_w = min(w - 6, 70)
    box = curses.newwin(5, box_w, (h - 5) // 2, (w - box_w) // 2)
    box.keypad(True)
    box.bkgd(" ", colors("blue"))
    box.box()
    put(box, 1, 2, title, curses.A_BOLD)
    put(box, 3, 2, "Enter confirma · Esc cancela", curses.A_DIM)
    text = initial
    curses.curs_set(1)
    try:
        while True:
            put(box, 2, 2, " " * (box_w - 4))
            put(box, 2, 2, text[-(box_w - 5):])
            box.move(2, min(box_w - 3, 2 + len(text)))
            box.refresh()
            key = box.get_wch()
            if key in ("\n", "\r"):
                return text
            if key == "\x1b":
                return None
            if key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                text = text[:-1]
            elif isinstance(key, str) and key.isprintable() and len(text) < 160:
                text += key
    finally:
        curses.curs_set(0)


def draw(win, st: State, visible: list[int], current: int, top: int, mode: str, review_scroll: int = 0):
    h, w = win.getmaxyx()
    win.erase()
    if h < 17 or w < 60:
        put(win, 1, 2, "Aumente o terminal (mínimo 60x17). Pressione Q para sair.", colors("yellow"))
        win.refresh()
        return
    put(win, 0, 2, "◆  DARFINOS", curses.A_BOLD | colors("pink"))
    put(win, 0, 17, "SETUP CENTER", curses.A_BOLD)
    put(win, 0, max(20, w - 24), f"{len(st.selected):02d}/{len(st.steps):02d} etapas", colors("green"))
    line(win, 1)
    put(win, 2, 2, "ORIGEM", colors("muted"))
    put(win, 2, 11, st.source[:max(0, w - 15)])
    put(win, 3, 2, "FILTRO", colors("muted"))
    put(win, 3, 11, (st.search or "Todas as etapas") + ("  · apenas selecionadas" if st.show_selected else ""), colors("pink"))
    line(win, 4)
    if mode == "list":
        put(win, 5, 2, "ETAPAS DISPONÍVEIS", curses.A_BOLD | colors("pink"))
        put(win, 5, max(22, w - 24), "[x] instalar  [ ] pular", colors("muted"))
        height = h - 13
        previous_group = None
        for slot, pos in enumerate(range(top, min(len(visible), top + height))):
            step = st.steps[visible[pos]]
            y = 6 + slot
            active = pos == current
            attr = curses.A_REVERSE if active else 0
            if active:
                put(win, y, 1, " " * (w - 2), attr)
            mark = "[x]" if step.name in st.selected else "[ ]"
            put(win, y, 2, ">" if active else " ", attr | curses.A_BOLD)
            put(win, y, 4, mark, attr | colors("green" if step.name in st.selected else "red"))
            put(win, y, 9, step.name[:21].ljust(22), attr | curses.A_BOLD)
            put(win, y, 32, step.desc, attr)
            previous_group = step.group
        if not visible:
            put(win, 8, 3, "Nenhuma etapa corresponde ao filtro.", colors("yellow"))
        line(win, h - 7)
        if visible:
            step = st.steps[visible[current]]
            put(win, h - 6, 2, f"{step.name}  /  {step.group}", curses.A_BOLD | colors("pink"))
            put(win, h - 5, 2, step.desc)
            deps = ", ".join(f"{d}{' ✓' if d in st.selected else ' !'}" for d in step.deps)
            put(win, h - 4, 2, "Depende de: " + (deps or "nenhuma declarada"), colors("yellow") if any(d not in st.selected for d in step.deps) else colors("muted"))
        put(win, h - 3, 2, "↑↓ mover  Espaço marcar  G grupo  A todas  N nenhuma  / buscar  F filtrar", colors("muted"))
        put(win, h - 2, 2, "D deps  S salvar  L carregar  Y -y  R revisar  U atualizar  Q sair", colors("muted"))
    else:
        selected = [s for s in st.steps if s.name in st.selected]
        missing = st.missing()
        lines = [f"  + {s.name:<22} {s.desc}" for s in selected]
        if not lines:
            lines = ["  Nenhuma etapa selecionada."]
        lines += ["", f"Dependências não selecionadas: {len(missing)}"]
        lines += [f"  ! {name}: {', '.join(deps)}" for name, deps in missing.items()]
        lines += ["", f"Modo automático (-y): {'ATIVO' if st.yes else 'desativado'}"]
        lines += ["", "ATENÇÃO: o script baixado executará comandos com privilégios sudo."]
        lines += ["Confira a origem e as alterações antes de prosseguir."]
        put(win, 5, 2, "REVISÃO DA EXECUÇÃO", curses.A_BOLD | colors("pink"))
        for i, content in enumerate(lines[review_scroll:review_scroll + h - 10]):
            put(win, 6 + i, 2, content, colors("yellow") if content.lstrip().startswith("!") else 0)
        line(win, h - 4)
        put(win, h - 3, 2, "Enter executar  D incluir dependências  ↑↓ rolar  Esc voltar", colors("green"))
        put(win, h - 2, 2, "A execução usa o terminal original para sudo, pacman e perguntas.", colors("muted"))
    line(win, h - 1)
    put(win, h - 1, 2, st.message[:max(0, w - 5)], colors("yellow"))
    win.refresh()


def ui(win, st: State) -> bool:
    curses.curs_set(0)
    win.keypad(True)
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        for name, number in C.items():
            foreground = {"pink": curses.COLOR_MAGENTA, "green": curses.COLOR_GREEN,
                          "red": curses.COLOR_RED, "yellow": curses.COLOR_YELLOW,
                          "muted": curses.COLOR_CYAN, "blue": curses.COLOR_BLUE}[name]
            curses.init_pair(number, foreground, -1)
    mode, current, top, review_scroll = "list", 0, 0, 0
    while True:
        visible = st.filtered()
        current = max(0, min(current, len(visible) - 1))
        height = max(1, win.getmaxyx()[0] - 13)
        top = max(0, min(top, max(0, len(visible) - height)))
        if current < top: top = current
        if current >= top + height: top = current - height + 1
        draw(win, st, visible, current, top, mode, review_scroll)
        key = win.getch()
        if key == curses.KEY_RESIZE: continue
        if key in (ord("q"), ord("Q")): return False
        if mode == "list":
            if key in (curses.KEY_DOWN, ord("j")): current += 1
            elif key in (curses.KEY_UP, ord("k")): current -= 1
            elif key == curses.KEY_NPAGE: current += height
            elif key == curses.KEY_PPAGE: current -= height
            elif key == curses.KEY_HOME: current = 0
            elif key == curses.KEY_END: current = len(visible) - 1
            elif key == ord(" ") and visible:
                name = st.steps[visible[current]].name
                if name in st.selected: st.selected.remove(name)
                else: st.selected.add(name)
            elif key in (ord("g"), ord("G")) and visible:
                group = st.steps[visible[current]].group
                members = {s.name for s in st.steps if s.group == group}
                if members <= st.selected: st.selected -= members
                else: st.selected |= members
            elif key in (ord("a"), ord("A")): st.selected = set(st.lookup)
            elif key in (ord("n"), ord("N")): st.selected.clear()
            elif key in (ord("f"), ord("F")): st.show_selected = not st.show_selected; current = top = 0
            elif key == ord("/"):
                value = prompt(win, "Buscar etapa (nome, descrição ou grupo):", st.search)
                if value is not None: st.search = value; current = top = 0
            elif key in (ord("d"), ord("D")): st.add_deps()
            elif key in (ord("s"), ord("S")):
                try: save_profile(st)
                except OSError as exc: st.message = str(exc)
            elif key in (ord("l"), ord("L")):
                try: load_profile(st)
                except (OSError, ValueError) as exc: st.message = str(exc)
            elif key in (ord("y"), ord("Y")): st.yes = not st.yes
            elif key in (ord("r"), ord("R"), 10, 13): mode = "review"; review_scroll = 0
            elif key in (ord("u"), ord("U")):
                st.message = "Para atualizar a fonte, reinicie com --fetch (ou --auto-fetch)."
        else:
            if key in (27, curses.KEY_LEFT, ord("b")): mode = "list"
            elif key in (curses.KEY_DOWN, ord("j")): review_scroll += 1
            elif key in (curses.KEY_UP, ord("k")): review_scroll = max(0, review_scroll - 1)
            elif key in (ord("d"), ord("D")): st.add_deps()
            elif key in (10, 13) and st.selected: return True



# ----------------------------------------------------------------------
# V3: histórico, perfis, diagnóstico e execução acompanhada
# ----------------------------------------------------------------------
HISTORY = CACHE / 'history.json'
PROFILE_DIR = CONFIG / 'profiles'
LOG_DIR = Path.home() / '.local/state/darfinos-tui/logs'
MAX_DOWNLOAD = 2_000_000


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                     delete=False) as tmp:
        json.dump(value, tmp, ensure_ascii=False, indent=2)
        temp = Path(tmp.name)
    os.replace(temp, path)


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_version() -> tuple[Path, str, str]:
    """Update from GitHub; retain numbered copies and a readable diff."""
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / NAME
    versions = CACHE / 'versions'
    versions.mkdir(exist_ok=True)
    previous = target.read_bytes() if target.exists() else b''
    try:
        req = urllib.request.Request(RAW, headers={'User-Agent': 'DarfinOS-TUI/3.0',
                                                   'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=18) as response:
            data = response.read(MAX_DOWNLOAD + 1)
        if len(data) > MAX_DOWNLOAD or not data.lstrip().startswith(b'#!'):
            raise ValueError('Resposta inválida ou arquivo grande demais')
        with tempfile.NamedTemporaryFile(dir=CACHE, delete=False) as tmp:
            tmp.write(data)
            temp = Path(tmp.name)
        try:
            parse_script(temp)
            digest = hashlib.sha256(data).hexdigest()
            old_digest = hashlib.sha256(previous).hexdigest() if previous else None
            if old_digest != digest:
                if previous:
                    (versions / f'{old_digest}.sh').write_bytes(previous)
                (versions / f'{digest}.sh').write_bytes(data)
                temp.replace(target)
                diff = ''.join(difflib.unified_diff(
                    previous.decode('utf-8', 'replace').splitlines(True),
                    data.decode('utf-8', 'replace').splitlines(True),
                    fromfile=old_digest[:12] if old_digest else 'vazio',
                    tofile=digest[:12]))
                (CACHE / 'last.diff').write_text(diff[:1_000_000], encoding='utf-8')
                action = 'Atualizado' if previous else 'Primeira versão'
            else:
                action = 'Sem alterações'
            history = read_json(HISTORY, [])
            history.append({'time': datetime.now(timezone.utc).isoformat(),
                            'sha256': digest, 'status': action, 'source': RAW})
            atomic_json(HISTORY, history[-100:])
            return target, f'GitHub/main · {action}', action
        finally:
            temp.unlink(missing_ok=True)
    except Exception as exc:
        if target.exists():
            parse_script(target)
            return target, f'CACHE OFFLINE · {exc}', 'offline'
        raise RuntimeError(f'Sem conexão e sem cache: {exc}') from exc


def profile_paths() -> list[Path]:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(PROFILE_DIR.glob('*.json'))


def save_named(st: State, name: str) -> None:
    if not re.fullmatch(r'[\w-]{1,40}', name):
        raise ValueError('Nome inválido; use letras, números, _ ou -')
    atomic_json(PROFILE_DIR / f'{name}.json', {'selected': sorted(st.selected),
                                             'yes': st.yes, 'version': 1})
    st.profile_name = name
    st.message = f'Perfil {name} salvo.'


def load_named(st: State, name: str) -> None:
    data = read_json(PROFILE_DIR / f'{name}.json', None)
    if not isinstance(data, dict) or not isinstance(data.get('selected'), list):
        raise ValueError('Perfil não encontrado ou inválido')
    st.selected = set(data['selected']) & set(st.lookup)
    st.yes = bool(data.get('yes', False))
    st.profile_name = name
    st.message = f'Perfil {name} carregado.'


def installed_packages() -> tuple[set[str], set[str]]:
    native, flat = set(), set()
    try:
        r = subprocess.run(['pacman', '-Qq'], capture_output=True, text=True, timeout=8)
        if r.returncode == 0:
            native = set(r.stdout.splitlines())
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run(['flatpak', 'list', '--app', '--columns=application'],
                           capture_output=True, text=True, timeout=8)
        if r.returncode == 0:
            flat = set(r.stdout.splitlines())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return native, flat


def inspect_steps(st: State) -> None:
    """Only mark verified package presence, not installation-step completion."""
    native, flat = installed_packages()
    # Step name equals package is only a heuristic; use explicit description for safety.
    st.statuses = {}
    for step in st.steps:
        if step.name in native:
            st.statuses[step.name] = 'pacman: instalado'
        elif step.name in flat:
            st.statuses[step.name] = 'flatpak: instalado'
        else:
            st.statuses[step.name] = 'não verificado'
    st.message = f'Pacman: {len(native)} pacotes; Flatpak: {len(flat)} apps. Etapas não são pacotes.'


def maintenance_items() -> list[tuple[str, str, list[str]]]:
    return [
        ('Pacotes instalados', 'Consulta pacman -Q', ['pacman', '-Q']),
        ('Órfãos', 'Somente listar, sem remover', ['pacman', '-Qdt']),
        ('Atualizações disponíveis', 'Consulta pacman -Qu (base local)', ['pacman', '-Qu']),
        ('Flatpaks', 'Lista aplicativos instalados', ['flatpak', 'list', '--app']),
        ('Serviços com falha', 'Consulta systemctl --failed', ['systemctl', '--failed', '--no-pager']),
        ('Uso do disco', 'Consulta df -h', ['df', '-h']),
        ('Espaço em cache', 'Consulta du -sh /var/cache/pacman/pkg', ['du', '-sh', '/var/cache/pacman/pkg']),
    ]


def safe_maintenance(command_: list[str]) -> str:
    try:
        r = subprocess.run(command_, capture_output=True, text=True, timeout=20)
        output = (r.stdout + '\n' + r.stderr).strip()
        return output[:15000] or f'Sem resultados (código {r.returncode}).'
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f'Falha: {exc}'


def scroll_screen(win, title: str, content: str) -> None:
    lines = content.expandtabs(4).splitlines() or ['(vazio)']
    offset = 0
    while True:
        h, w = win.getmaxyx()
        win.erase()
        put(win, 0, 2, title, curses.A_BOLD | colors('pink'))
        line(win, 1)
        height = max(1, h - 4)
        for y, row in enumerate(lines[offset:offset + height], 2):
            put(win, y, 2, row)
        put(win, h - 1, 2, '↑↓/PgUp/PgDn rolar · Esc/Q voltar', colors('muted'))
        win.refresh()
        key = win.getch()
        if key in (27, ord('q'), ord('Q')):
            return
        if key in (curses.KEY_DOWN, ord('j')): offset += 1
        if key in (curses.KEY_UP, ord('k')): offset -= 1
        if key == curses.KEY_NPAGE: offset += height
        if key == curses.KEY_PPAGE: offset -= height
        offset = max(0, min(offset, max(0, len(lines) - height)))


def maintenance_screen(win) -> None:
    items = maintenance_items()
    index = 0
    while True:
        h, w = win.getmaxyx()
        win.erase()
        put(win, 0, 2, '◆ CENTRAL DE MANUTENÇÃO  ·  somente leitura',
            curses.A_BOLD | colors('pink'))
        line(win, 1)
        for i, (title, desc, _) in enumerate(items):
            attr = curses.A_REVERSE if i == index else 0
            put(win, 3 + i * 2, 3, ('▶ ' if i == index else '  ') + title, attr)
            put(win, 4 + i * 2, 6, desc, colors('muted'))
        put(win, h - 2, 2, 'Enter consultar · ↑↓ navegar · Esc voltar', colors('muted'))
        win.refresh()
        key = win.getch()
        if key in (27, ord('q')): return
        if key in (curses.KEY_DOWN, ord('j')): index = min(len(items)-1, index+1)
        if key in (curses.KEY_UP, ord('k')): index = max(0, index-1)
        if key in (10, 13):
            title, _, cmd = items[index]
            scroll_screen(win, title + '  ·  ' + shlex.join(cmd), safe_maintenance(cmd))


def history_screen(win) -> None:
    records = read_json(HISTORY, [])
    lines = ['Histórico de downloads (SHA-256, UTC):', '']
    for rec in reversed(records[-40:]):
        lines.append(f"{rec.get('time', '?')[:19]}  {rec.get('sha256', '?')[:16]}  {rec.get('status', '?')}")
    lines += ['', 'Diff mais recente:', '']
    diff = CACHE / 'last.diff'
    if diff.exists():
        lines += diff.read_text(encoding='utf-8', errors='replace').splitlines()[:1000]
    else:
        lines.append('Nenhuma diferença registrada ainda.')
    scroll_screen(win, 'HISTÓRICO DO GITHUB', '\n'.join(lines))


def draw_v3(win, st: State, visible: list[int], cursor: int, top: int,
            mode: str, review_scroll: int, digest: str) -> None:
    h, w = win.getmaxyx()
    win.erase()
    if h < 16 or w < 54:
        put(win, 1, 2, 'Terminal pequeno: mínimo 54x16. Q sai.', colors('yellow'))
        win.refresh()
        return
    split = w >= 100
    put(win, 0, 2, '◆ DARFINOS', curses.A_BOLD | colors('pink'))
    put(win, 0, 15, 'CONTROL CENTER  /  V4', curses.A_BOLD)
    put(win, 0, max(38, w - 20), f'{len(st.selected)}/{len(st.steps)} etapas', colors('green'))
    line(win, 1)
    put(win, 2, 2, f'ORIGEM: {st.source}'[:w-4], colors('muted'))
    put(win, 3, 2, f'PERFIL: {st.profile_name}   SHA256: {digest[:16]}   -y: {"SIM" if st.yes else "NÃO"}', colors('muted'))
    line(win, 4)
    if mode == 'list':
        width = (w * 60 // 100) if split else w - 2
        list_height = h - (8 if split else 12)
        put(win, 5, 2, 'ETAPAS  /  Espaço seleciona', curses.A_BOLD | colors('pink'))
        for pos in range(top, min(len(visible), top + list_height)):
            s = st.steps[visible[pos]]
            y = 6 + pos - top
            active = pos == cursor
            attr = curses.A_REVERSE if active else 0
            if active: put(win, y, 1, ' ' * (width - 2), attr)
            selected = s.name in st.selected
            label = f'{"[x]" if selected else "[ ]"} {s.name:<20} {s.desc}'
            put(win, y, 2, label[:width-4], attr | (colors('green') if selected else 0))
        if not visible: put(win, 7, 3, 'Nenhum resultado para a busca.', colors('yellow'))
        if split:
            x = width + 1
            for y in range(5, h-3): put(win, y, x, '│', colors('muted'))
            put(win, 5, x+2, 'DETALHES', curses.A_BOLD | colors('pink'))
            if visible:
                s = st.steps[visible[cursor]]
                details = [s.name, '', 'Grupo: ' + s.group, '', s.desc, '',
                           'Dependências: ' + (', '.join(s.deps) or 'nenhuma'), '',
                           'Detecção: ' + st.statuses.get(s.name, 'não consultado')]
                yy = 7
                for item in details:
                    for part in textwrap.wrap(item, max(12, w-x-5)) or ['']:
                        if yy < h-3: put(win, yy, x+2, part); yy += 1
        else:
            line(win, h-6)
            if visible:
                s = st.steps[visible[cursor]]
                put(win, h-5, 2, f'{s.name} · {s.group}', curses.A_BOLD | colors('pink'))
                put(win, h-4, 2, s.desc)
                put(win, h-3, 2, 'Deps: ' + (', '.join(s.deps) or 'nenhuma'))
        put(win, h-2, 2, '↑↓ navegar  Espaço marcar  G grupo  A/N tudo/nada  / buscar  F filtro', colors('muted'))
        put(win, h-1, 2, 'R revisar  O presets  Z retomar  B apps  P perfis  I detectar  M manutenção  H histórico  U atualizar  Q sair', colors('muted'))
    else:
        put(win, 5, 2, 'REVISÃO · Enter executa / Esc volta', curses.A_BOLD | colors('pink'))
        chosen = [s for s in st.steps if s.name in st.selected]
        lines = [f' + {s.name:<22} {s.desc}' for s in chosen]
        lines += ['', 'Dependências ausentes:']
        lines += [f' ! {name}: {", ".join(deps)}' for name, deps in st.missing().items()]
        lines += ['', 'D: incluir dependências   Y: alternar -y   B: aplicativos',
                  'ATENÇÃO: script remoto pode executar comandos com sudo.']
        for i, row in enumerate(lines[review_scroll:review_scroll + h - 9]):
            put(win, 6+i, 2, row)
        put(win, h-2, 2, '↑↓ rolar  D dependências  Enter executar  Esc voltar', colors('muted'))
    put(win, h-1 if mode == 'review' else h-3, 2, st.message[:w-4], colors('yellow'))
    win.refresh()


def profile_screen(win, st: State) -> None:
    profiles = [p.stem for p in profile_paths()]
    text = 'Perfis: ' + (', '.join(profiles) or '(nenhum)')
    value = prompt(win, text[:60] + ' · nome do perfil:', st.profile_name)
    if value is None: return
    action = prompt(win, 'S salvar / L carregar / E excluir:', 'S')
    if action is None: return
    try:
        if action.lower() == 's': save_named(st, value)
        elif action.lower() == 'l': load_named(st, value)
        elif action.lower() == 'e':
            if re.fullmatch(r'[\w-]{1,40}', value):
                (PROFILE_DIR / f'{value}.json').unlink()
                st.message = f'Perfil {value} excluído.'
    except (OSError, ValueError) as exc:
        st.message = str(exc)


def ui_v3(win, st: State, digest: str) -> str:
    curses.curs_set(0)
    win.keypad(True)
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        for name, number in C.items():
            fg = {'pink': curses.COLOR_MAGENTA, 'green': curses.COLOR_GREEN,
                  'red': curses.COLOR_RED, 'yellow': curses.COLOR_YELLOW,
                  'muted': curses.COLOR_CYAN, 'blue': curses.COLOR_BLUE}[name]
            curses.init_pair(number, fg, -1)
    mode, current, top, scroll = 'list', 0, 0, 0
    while True:
        h, w = win.getmaxyx()
        visible = st.filtered()
        current = max(0, min(current, len(visible)-1))
        height = max(1, h - (8 if w >= 100 else 12))
        top = max(0, min(top, max(0, len(visible)-height)))
        if current < top: top = current
        if current >= top+height: top = current-height+1
        draw_v3(win, st, visible, current, top, mode, scroll, digest)
        key = win.getch()
        if key == curses.KEY_RESIZE: continue
        if key in (ord('q'), ord('Q')): return 'quit'
        if mode == 'review':
            if key in (27, curses.KEY_LEFT): mode = 'list'
            elif key in (curses.KEY_DOWN, ord('j')): scroll += 1
            elif key in (curses.KEY_UP, ord('k')): scroll = max(0, scroll-1)
            elif key in (ord('d'), ord('D')): st.add_deps()
            elif key in (ord('y'), ord('Y')): st.yes = not st.yes
            elif key in (ord('b'), ord('B')): apps_screen(win, st, CURRENT_SCRIPT)
            elif key in (10, 13) and st.selected: return 'run'
            continue
        if key in (curses.KEY_DOWN, ord('j')): current += 1
        elif key in (curses.KEY_UP, ord('k')): current -= 1
        elif key == curses.KEY_NPAGE: current += height
        elif key == curses.KEY_PPAGE: current -= height
        elif key == curses.KEY_HOME: current = 0
        elif key == curses.KEY_END: current = len(visible)-1
        elif key == ord(' ') and visible:
            name = st.steps[visible[current]].name
            if name in st.selected: st.selected.remove(name)
            else: st.selected.add(name)
        elif key in (ord('g'), ord('G')) and visible:
            group = st.steps[visible[current]].group
            names = {s.name for s in st.steps if s.group == group}
            if names <= st.selected: st.selected -= names
            else: st.selected |= names
        elif key in (ord('a'), ord('A')): st.selected = set(st.lookup)
        elif key in (ord('n'), ord('N')): st.selected.clear()
        elif key in (ord('f'), ord('F')): st.show_selected = not st.show_selected; current = top = 0
        elif key == ord('/'):
            value = prompt(win, 'Buscar etapas:', st.search)
            if value is not None: st.search = value; current = top = 0
        elif key in (ord('d'), ord('D')): st.add_deps()
        elif key in (ord('p'), ord('P')): profile_screen(win, st)
        elif key in (ord('o'), ord('O')): preset_screen(win, st)
        elif key in (ord('i'), ord('I')): inspect_steps(st)
        elif key in (ord('b'), ord('B')): apps_screen(win, st, CURRENT_SCRIPT)
        elif key in (ord('m'), ord('M')): maintenance_screen(win)
        elif key in (ord('z'), ord('Z')): recovery_screen(win, st, CURRENT_SCRIPT)
        elif key in (ord('h'), ord('H')): history_screen(win)
        elif key in (ord('y'), ord('Y')): st.yes = not st.yes
        elif key in (ord('r'), ord('R'), 10, 13): mode = 'review'; scroll = 0
        elif key in (ord('u'), ord('U')): return 'refresh'


def stream_install_v3(cmd: list[str], step_names: list[str], logfile: Path) -> int:
    """PTY forwarding preserves sudo/pacman interactive prompts; stdout logged.

    Progress is an estimate from explicit step-name log matches, not a verified
    success count. Ctrl+C forwards to the whole installer process group.
    """
    import tty
    import termios as tty_termios
    logfile.parent.mkdir(parents=True, exist_ok=True)
    master, slave = pty.openpty()
    process = None
    old_tty = None
    try:
        process = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave,
                                   start_new_session=True)
        os.close(slave)
        slave = -1
        if sys.stdin.isatty():
            old_tty = tty_termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
        buffer = ''
        seen = set()
        with logfile.open('wb') as log:
            header = ('\r\nDARFINOS TUI V3 | EXECUÇÃO AO VIVO | Ctrl+C interrompe\r\n'
                      'O progresso abaixo é estimado a partir de mensagens do Bash.\r\n')
            os.write(sys.stdout.fileno(), header.encode())
            while True:
                ready, _, _ = select.select([master, sys.stdin.fileno()], [], [], 0.2)
                if master in ready:
                    try: chunk = os.read(master, 65536)
                    except OSError: chunk = b''
                    if not chunk: break
                    os.write(sys.stdout.fileno(), chunk)
                    log.write(chunk)
                    buffer = (buffer + chunk.decode('utf-8', 'replace'))[-4000:]
                    # Only recognize explicit step headers, never arbitrary mentions.
                    for name in step_names:
                        if re.search(r'(?im)^\s*(?:==>|\[STEP\]|ETAPA:)\s*' + re.escape(name) + r'(?:\s|$|:)', buffer):
                            if name not in seen:
                                seen.add(name)
                                notice = f'\r\n[TUI] Etapas identificadas nos logs: {len(seen)}/{len(step_names)} (não significa concluídas)\r\n'
                                os.write(sys.stdout.fileno(), notice.encode())
                    buffer = buffer[-200:]
                if sys.stdin.fileno() in ready:
                    data = os.read(sys.stdin.fileno(), 1024)
                    if data:
                        if b'\x03' in data:
                            os.killpg(process.pid, signal.SIGINT)
                        else:
                            os.write(master, data)
                if process.poll() is not None and not ready:
                    break
        return process.wait()
    finally:
        if old_tty is not None:
            tty_termios.tcsetattr(sys.stdin.fileno(), tty_termios.TCSADRAIN, old_tty)
        if slave >= 0: os.close(slave)
        os.close(master)
        if process is not None and process.poll() is None:
            try: os.killpg(process.pid, signal.SIGINT)
            except ProcessLookupError: pass
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()


# V4.2: diário atômico para retomada conservadora.
RUN_DIR = Path.home() / '.local/state/darfinos-tui/runs'

def latest_run():
    files = sorted(RUN_DIR.glob('run-*.json'), reverse=True)
    for path in files:
        data = read_json(path, None)
        if isinstance(data, dict) and data.get('schema') == 1:
            return path, data
    return None, None

def recovery_selection(st: State, script: Path, record: dict) -> tuple[set[str], str]:
    if not isinstance(record.get('statuses'), dict):
        raise ValueError('Registro sem estados válidos.')
    if record.get('script_sha256') != sha(script):
        raise ValueError('O Bash mudou desde a execução. Retomada bloqueada; revise o diff ou use a versão anterior.')
    known = st.lookup
    previous = record.get('statuses', {})
    original = set(record.get('selected', []))
    if not original or not original <= set(known):
        raise ValueError('O histórico contém etapas ausentes ou inválidas.')
    # RUN significa interrupção em etapa possivelmente parcialmente aplicada.
    retry = {name for name in original if previous.get(name) != 'DONE'}
    if not retry:
        raise ValueError('Todas as etapas registradas já foram concluídas.')
    # Dependências concluídas não precisam ser executadas de novo.
    queue = list(retry)
    while queue:
        name = queue.pop()
        for dep in known[name].deps:
            if dep in known and dep not in retry and previous.get(dep) != 'DONE':
                retry.add(dep)
                queue.append(dep)
    uncertain = [n for n in retry if previous.get(n) in ('RUN', 'PEND', None)]
    warning = ('ATENÇÃO: etapas RUN/PEND podem ter sido aplicadas parcialmente: ' + ', '.join(uncertain)) if uncertain else 'Etapas falhas/ignoradas selecionadas para nova tentativa.'
    return retry, warning

def prepare_run(script: Path, names: list[str], log: Path, parent: str | None = None):
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = RUN_DIR / f'run-{stamp}.json'
    data = {'schema': 1, 'started_at': datetime.now(timezone.utc).isoformat(),
            'script_sha256': sha(script), 'script_path': str(script),
            'selected': names, 'statuses': {n:'PEND' for n in names},
            'log': str(log), 'exit_code': None, 'parent_run': parent,
            'events': [], 'state': 'RUNNING'}
    atomic_json(path, data)
    path.chmod(0o600)
    return path, data

def update_run(path: Path, data: dict, event: str | None = None, code: int | None = None):
    if event:
        parts = event.split(':', 2)
        if len(parts) >= 2 and parts[0] in ('STEP_START','STEP_DONE','STEP_FAIL','STEP_SKIP'):
            name = parts[1]
            if name in data['statuses']:
                data['statuses'][name] = {'STEP_START':'RUN','STEP_DONE':'DONE',
                    'STEP_FAIL':'FAIL','STEP_SKIP':'SKIP'}[parts[0]]
                data['events'].append({'time':datetime.now(timezone.utc).isoformat(), 'event':event})
    if code is not None:
        data['exit_code'] = code
        data['finished_at'] = datetime.now(timezone.utc).isoformat()
        data['state'] = 'DONE' if code == 0 and all(v == 'DONE' for v in data['statuses'].values()) else 'INCOMPLETE'
    atomic_json(path, data)

def recovery_screen(win, st: State, script: Path):
    path, record = latest_run()
    if record is None:
        st.message = 'Nenhuma instalação anterior registrada na V4.2.'
        return
    try:
        selection, warning = recovery_selection(st, script, record)
    except ValueError as exc:
        scroll_screen(win, 'RECUPERAÇÃO BLOQUEADA', str(exc) + '\n\nRegistro: ' + str(path))
        return
    details = [f'Registro: {path.name}', f'Origem: {record.get("started_at", "?")}',
               f'Estado: {record.get("state", "?")}', f'SHA256: {record["script_sha256"][:20]}', '',
               'Concluídas anteriormente: ' + ', '.join(n for n,v in record['statuses'].items() if v=='DONE'),
               '', 'Serão selecionadas para nova tentativa:', *('  - '+n+' ['+record['statuses'].get(n,'?')+']' for n in sorted(selection)),
               '', warning, '', 'A retomada NÃO desfaz mudanças anteriores.']
    scroll_screen(win, 'DIAGNÓSTICO DA ÚLTIMA INSTALAÇÃO', '\n'.join(details))
    answer = prompt(win, 'Selecionar etapas pendentes? Digite RETOMAR para confirmar:')
    if answer == 'RETOMAR':
        st.selected = selection
        st.message = f'Retomada de {path.name}: {len(selection)} etapas. Revise antes de executar.'
        st.recovery_parent = path.name

# Presets versionados: etapas explicitamente listadas, sem comandos arbitrários.
PRESETS = {
    'minimal': ('Base enxuta', ('pacman_conf', 'mirrors', 'sysupgrade', 'base', 'fonts', 'hardware', 'cli_tools')),
    'desktop': ('SonicDE + XLibre e desktop', ('pacman_conf', 'mirrors', 'repo_xlibre', 'repo_sonicde', 'sysupgrade', 'base', 'fonts', 'hardware', 'xlibre', 'sonicde', 'desktop_extras', 'bluetooth', 'cli_tools', 'shells', 'flatpak', 'apps')),
    'gaming': ('Desktop e jogos', ('pacman_conf', 'mirrors', 'repo_xlibre', 'repo_sonicde', 'sysupgrade', 'base', 'fonts', 'hardware', 'xlibre', 'sonicde', 'desktop_extras', 'bluetooth', 'cli_tools', 'flatpak', 'gaming')),
    'full': ('Todas as etapas, inclusive Bedrock (RISCO)', tuple()),
}


def preset_selection(name: str, steps: list[Step]) -> set[str]:
    if name not in PRESETS:
        raise ValueError('Preset desconhecido: ' + name)
    known = {step.name for step in steps}
    chosen = set(known if name == 'full' else PRESETS[name][1])
    unknown = chosen - known
    if unknown:
        raise ValueError('Preset incompatível com o Bash: ' + ', '.join(sorted(unknown)))
    return chosen


def apply_preset(st: State, name: str) -> None:
    st.selected = preset_selection(name, st.steps)
    st.profile_name = 'preset:' + name
    st.message = f'Preset {name} aplicado: {len(st.selected)} etapas. Revise antes de instalar.'


def preset_screen(win, st: State) -> None:
    lines = ['PRESETS OFICIAIS · nenhum executa comandos ao selecionar', '']
    for index, (name, (description, _)) in enumerate(PRESETS.items(), 1):
        lines.append(f'{index}. {name:<10} {description}')
    lines.extend(['', 'Full inclui etapas de alto risco, como Bedrock.',
                  'Todos os presets exigem revisão antes de executar.'])
    scroll_screen(win, 'PRESETS', '\n'.join(lines))
    value = prompt(win, 'Preset (minimal/desktop/gaming/full):')
    if value:
        try:
            apply_preset(st, value.strip().lower())
        except ValueError as exc:
            st.message = str(exc)


def build_manifest(script: Path) -> dict:
    steps = parse_script(script)
    rows = inventory(script, {s.name for s in steps})
    packages = {s.name: [] for s in steps}
    for step, manager, name in rows:
        packages[step].append({'manager': manager, 'name': name})
    return {
        'schema_version': 1,
        'script_sha256': sha(script),
        'accuracy': 'partial_static',
        'warning': 'Prévia estática: variáveis, arrays, condicionais e chamadas indiretas não são resolvidos; não é lista exaustiva.',
        'steps': [
            {'id': s.name, 'description': s.desc, 'group': s.group,
             'dependencies': s.deps, 'packages': packages[s.name]}
            for s in steps
        ],
        'presets': {name: {'description': description, 'steps': [s.name for s in steps if s.name in preset_selection(name, steps)]}
                    for name, (description, _) in PRESETS.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='DarfinOS TUI V4.4 · curses · sem pip')
    ap.add_argument('script', nargs='?', type=Path, help='Script Bash local (opcional)')
    ap.add_argument('--local', action='store_true', help='Usa script Bash ao lado do TUI')
    ap.add_argument('--fetch', action='store_true', help='Consulta o GitHub em vez do Bash local')
    ap.add_argument('--dry-run', action='store_true', help='Não executa instalação')
    ap.add_argument('--empty', action='store_true', help='Inicia sem selecionar etapas')
    ap.add_argument('--profile', help='Carrega perfil salvo')
    ap.add_argument('--history', action='store_true', help='Mostra histórico em texto')
    ap.add_argument('--resume', action='store_true', help='Pré-seleciona etapas não concluídas da última execução')
    ap.add_argument('--runs', action='store_true', help='Lista execuções registradas')
    ap.add_argument('--preset', choices=tuple(PRESETS), help='Pré-seleciona um preset oficial')
    ap.add_argument('--list-presets', action='store_true', help='Lista os presets sem abrir a TUI')
    ap.add_argument('--manifest', action='store_true', help='Imprime manifesto JSON parcial, sem executar o Bash')
    args = ap.parse_args()
    if args.list_presets:
        for name, (description, _) in PRESETS.items():
            print(f'{name:<10} {description}')
        return 0
    if args.manifest:
        script = (args.script or LOCAL).expanduser().resolve()
        if not script.is_file(): ap.error(f'Não encontrado: {script}')
        print(json.dumps(build_manifest(script), ensure_ascii=False, indent=2))
        return 0
    if args.runs:
        for path in sorted(RUN_DIR.glob('run-*.json'), reverse=True):
            data = read_json(path, {})
            print(path.name, data.get('state'), data.get('exit_code'), data.get('started_at'))
        return 0
    if args.history:
        for rec in read_json(HISTORY, []): print(rec)
        return 0
    if os.geteuid() == 0 and not args.dry_run:
        ap.error('Execute como usuário normal, não como root')
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        ap.error('Precisa de um terminal interativo')
    locale.setlocale(locale.LC_ALL, '')
    os.environ.setdefault('ESCDELAY', '25')
    if args.script or args.local or (LOCAL.is_file() and not args.fetch):
        script = (args.script or LOCAL).expanduser().resolve()
        origin = 'Arquivo local'
        if not script.is_file(): ap.error(f'Não encontrado: {script}')
        parse_script(script)
    else:
        try: script, origin, _ = fetch_version()
        except (OSError, RuntimeError, ValueError) as exc: ap.error(str(exc))
    while True:
        global CURRENT_SCRIPT
        CURRENT_SCRIPT = script
        digest = sha(script)
        steps = parse_script(script)
        st = State(steps=steps, source=origin,
                   selected=set() if args.empty else {s.name for s in steps})
        if args.preset:
            try: apply_preset(st, args.preset)
            except ValueError as exc: ap.error(str(exc))
        if args.profile:
            try: load_named(st, args.profile)
            except ValueError as exc: st.message = str(exc)
        if args.resume:
            _, old = latest_run()
            if not old: ap.error('Nenhuma execução anterior registrada')
            try:
                st.selected, st.message = recovery_selection(st, script, old)
            except ValueError as exc: ap.error(str(exc))
            st.recovery_parent = latest_run()[0].name
        try: action = curses.wrapper(ui_v3, st, digest)
        except KeyboardInterrupt: return 130
        if action == 'quit': return 0
        if action == 'refresh':
            if args.script or args.local:
                print('Fonte local: atualize o arquivo manualmente ou rode sem --local.')
                input('Enter para continuar...')
            else:
                try: script, origin, _ = fetch_version()
                except Exception as exc:
                    print('Erro de atualização:', exc)
                    input('Enter para continuar...')
            continue
        if action == 'run':
            cmd = command(script, st)
            print('Fonte:', origin)
            print('SHA256:', digest)
            print('Comando:', shlex.join(cmd))
            print('Etapas:', len(st.selected))
            if args.dry_run: return 0
            answer = input('Executar este script (pode pedir sudo)? [s/N]: ').strip().lower()
            if answer not in ('s', 'sim'): return 0
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            log = LOG_DIR / f'install-{timestamp}.log'
            names = [s.name for s in steps if s.name in st.selected]
            journal, run_data = prepare_run(script, names, log, getattr(st, 'recovery_parent', None))
            code = stream_install_v4(cmd, names, log, journal, run_data)
            print(f'\nCódigo de saída: {code} | Log: {log}')
            return code



# ================================================================
# V4: inventário estático, eventos de execução, painel de instalação
# ================================================================
CURRENT_SCRIPT = LOCAL
ANSI_ESCAPE = re.compile(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))')


def inventory(script: Path, selected: set[str]):
    """Prévia estática conservadora. Chamadas dinâmicas são indicadas à parte."""
    source = script.read_text(encoding='utf-8')
    result = []
    for step in selected:
        m = re.search(r'^step_' + re.escape(step) + r'\(\)\s*\{', source, re.M)
        if not m: continue
        # Track nested braces, including shell functions with simple literal calls.
        begin = m.end(); depth = 1; pos = begin
        while pos < len(source) and depth:
            if source[pos] == '{': depth += 1
            elif source[pos] == '}': depth -= 1
            pos += 1
        body = source[begin:pos-1]
        for match in re.finditer(r'(?m)^\s*(install_pkgs_replace|install_pkgs|aur_install|flatpak_install)\s+((?:\\\n|[^\n])+(?:\n\s+[^\n]+)*)',body):
            kind = match.group(1)
            statement = match.group(2).replace('\\\n',' ')
            # Stop at shell operators and comments; skip nonliteral tokens.
            statement = re.split(r'\s(?:\|\||&&|\||;|#)\s', statement, maxsplit=1)[0]
            try: args = shlex.split(statement,comments=True)
            except ValueError: continue
            for item in args:
                if re.fullmatch(r'[a-zA-Z0-9][\w.+@/-]*',item) and not item.startswith('-'):
                    result.append((step,'flatpak' if kind=='flatpak_install' else 'aur' if kind=='aur_install' else 'pacman',item))
    return list(dict.fromkeys(result))


def apps_screen(win, st: State, script: Path):
    rows = inventory(script, st.selected)
    native, flat = installed_packages()
    lines = [f'{"ETAPA":<17} {"ORIGEM":<9} {"APLICATIVO / PACOTE":<40} STATUS', '']
    for step,origin,pkg in rows:
        installed = pkg in (flat if origin=='flatpak' else native)
        lines.append(f'{step:<17} {origin:<9} {pkg:<40} {"instalado" if installed else "não encontrado"}')
    lines.extend(['','Prévia parcial: apenas chamadas literais diretamente identificáveis.',
                  'Arrays, variáveis, comandos indiretos e condicionais podem alterar a lista.',
                  'A lista efetiva também aparece nos eventos PKG durante a execução.'])
    scroll_screen(win, f'APLICATIVOS PREVISTOS · {len(rows)} itens identificados', '\n'.join(lines))


def _modal(win, title, detail, choices=None, secret=False):
    """Modal responsivo; nunca escreve conteúdo secreto no terminal ou log."""
    h,w=win.getmaxyx()
    width=min(max(34,w-8),86); height=9 if choices else 8
    if h<height+2 or w<40: return None
    box=curses.newwin(height,width,(h-height)//2,(w-width)//2)
    box.keypad(True)
    value=''; curses.curs_set(0 if choices else 1)
    try:
        while True:
            box.erase(); box.box()
            put(box,1,2,title,curses.A_BOLD|colors('pink'))
            for idx,line_ in enumerate(textwrap.wrap(detail,width-5)[:2]): put(box,2+idx,2,line_)
            if choices:
                put(box,5,2,'[S] Sim     [N] Não     [Enter] padrão: '+choices,colors('yellow'))
                put(box,7,2,'Esc = cancelar resposta / voltar ao terminal',colors('muted'))
            else:
                put(box,5,2,'Resposta: '+ ('•'*len(value) if secret else value[-(width-16):]))
                put(box,6,2,'Enter confirma · Esc cancela',colors('muted'))
            box.refresh(); key=box.get_wch()
            if key=='\x1b': return None
            if choices:
                if key in ('s','S','y','Y'): return 's'
                if key in ('n','N'): return 'n'
                if key in ('\n','\r'): return choices
            else:
                if key in ('\n','\r'): return value
                if key in ('\x7f','\b',curses.KEY_BACKSPACE): value=value[:-1]
                elif isinstance(key,str) and key.isprintable() and len(value)<250: value+=key
    finally:
        curses.curs_set(0)


def _install_draw(win, names, status, current, tail, elapsed, log_mode, count, waiting, packages):
    h,w=win.getmaxyx(); win.erase()
    if h<15 or w<48:
        put(win,0,1,'Terminal pequeno. Amplie para 48x15.',colors('yellow'))
        win.refresh(); return
    done=sum(status.get(n)=='DONE' for n in names)
    fail=sum(status.get(n)=='FAIL' for n in names)
    skip=sum(status.get(n)=='SKIP' for n in names)
    total=len(names); finished=done+fail+skip
    spinner='|/-\\'[int(time.monotonic()*5)%4]
    put(win,0,2,'◆ DARFINOS  /  INSTALANDO',curses.A_BOLD|colors('pink'))
    put(win,0,max(31,w-24),f'{int(elapsed)//60:02d}:{int(elapsed)%60:02d}  {spinner}',colors('yellow'))
    line(win,1)
    put(win,2,2,f'Etapa atual: {current or "Preparando ambiente / autenticação"}'[:w-4],curses.A_BOLD)
    put(win,3,2,f'Concluídas: {done}   Falhas: {fail}   Ignoradas: {skip}   Total: {total}',colors('muted'))
    bw=max(8,w-6); filled=int(bw*finished/max(1,total))
    put(win,4,2,'█'*filled+'░'*(bw-filled),colors('green'))
    put(win,5,2,f'{finished}/{total} etapas finalizadas · {len(packages)} pacotes mencionados na execução',colors('muted'))
    line(win,6)
    available=h-11
    if log_mode:
        put(win,7,2,'SAÍDA RECENTE  ·  L retorna ao painel',curses.A_BOLD|colors('pink'))
        display=list(tail)[-available:]
    else:
        put(win,7,2,'STATUS DAS ETAPAS  ·  L mostra logs',curses.A_BOLD|colors('pink'))
        display=[]
        for n in names:
            flag=status.get(n,'PEND')
            sym={'DONE':'✓','FAIL':'✗','SKIP':'-','RUN':'◌','PEND':'·'}[flag]
            display.append(f'{sym} {n:<23} {flag}')
        if len(display)>available:
            idx=names.index(current) if current in names else 0
            start=max(0,min(idx-available//2,len(display)-available))
            display=display[start:start+available]
    for i,t in enumerate(display): put(win,8+i,2,t[:w-4])
    line(win,h-3)
    put(win,h-2,2,('AGUARDANDO RESPOSTA · ' if waiting else '')+'L logs/painel · T terminal · Ctrl+C interromper',colors('yellow'))
    put(win,h-1,2,'Perguntas reconhecidas aparecem em janelas. T permite responder prompts desconhecidos.',colors('muted'))
    win.refresh()


def stream_install_v4(cmd: list[str], step_names: list[str], logfile: Path, journal=None, run_data=None) -> int:
    """PTY para stdin/stdout; pipe dedicado para eventos; curses para monitoramento."""
    import errno
    logfile.parent.mkdir(parents=True,exist_ok=True)
    master,slave=pty.openpty()
    er,ew=os.pipe()
    os.set_inheritable(ew,True)
    env=os.environ.copy(); env['DARFINOS_EVENT_FD']=str(ew)
    proc=subprocess.Popen(cmd,stdin=slave,stdout=slave,stderr=slave,
                          start_new_session=True,pass_fds=(ew,),env=env)
    os.close(slave);os.close(ew)
    for fd in (master,er): os.set_blocking(fd,False)
    statuses={n:'PEND' for n in step_names}; tail=collections.deque(maxlen=1200)
    packages=set(); current=''; log_mode=False; waiting=False
    started=time.monotonic(); event_buf=b''; output_buf=''; ended=False; pending=None
    active_fds={master,er}
    def run(win):
        nonlocal current,log_mode,waiting,event_buf,output_buf,ended,pending
        curses.curs_set(0);win.keypad(True);win.nodelay(True)
        if curses.has_colors():
            curses.start_color(); curses.use_default_colors()
            for name,number in C.items():
                curses.init_pair(number,{'pink':curses.COLOR_MAGENTA,'green':curses.COLOR_GREEN,
                  'red':curses.COLOR_RED,'yellow':curses.COLOR_YELLOW,'muted':curses.COLOR_CYAN,
                  'blue':curses.COLOR_BLUE}[name],-1)
        with logfile.open('wb') as log:
            while True:
                _install_draw(win,step_names,statuses,current,tail,time.monotonic()-started,
                              log_mode,0,waiting,packages)
                for fd in select.select(list(active_fds),[],[],0.12)[0] if active_fds else []:
                    if fd==er:
                        try: chunk=os.read(er,65536)
                        except BlockingIOError: chunk=b''
                        if not chunk:
                            active_fds.discard(er)
                        event_buf+=chunk
                        while b'\n' in event_buf:
                            raw,event_buf=event_buf.split(b'\n',1)
                            evt=raw.decode('utf-8','replace').strip()
                            if journal is not None: update_run(journal, run_data, event=evt)
                            parts=evt.split(':',2); typ=parts[0]
                            if typ.startswith('STEP_') and len(parts)>=2:
                                name=parts[1]
                                if name in statuses:
                                    statuses[name]={'STEP_START':'RUN','STEP_DONE':'DONE',
                                      'STEP_FAIL':'FAIL','STEP_SKIP':'SKIP'}.get(typ,statuses[name])
                                    if typ=='STEP_START':current=name
                            elif typ=='PKG' and len(parts)==3:
                                packages.update((parts[1],p) for p in parts[2].split())
                            elif typ=='PROMPT_CONFIRM' and len(parts)==3:
                                default=parts[1];question=parts[2]
                                waiting=True;_install_draw(win,step_names,statuses,current,tail,time.monotonic()-started,log_mode,0,waiting,packages)
                                response=_modal(win,'Confirmação do instalador',question,'s' if default=='s' else 'n')
                                if response is not None:os.write(master,(response+'\n').encode())
                                else: log_mode=True
                                waiting=False
                            elif typ=='PROMPT_CHOOSE' and len(parts)==3:
                                opts=parts[2].split(':',1)
                                default=parts[1]; question=opts[1] if len(opts)>1 else parts[2]
                                waiting=True
                                response=_modal(win,'Escolha uma opção',question+'  ['+opts[0]+']')
                                if response is not None:os.write(master,(response+'\n').encode())
                                else:log_mode=True
                                waiting=False
                    else:
                        try:chunk=os.read(master,65536)
                        except (BlockingIOError,OSError):chunk=b''
                        if not chunk:
                            active_fds.discard(master)
                        if chunk:
                            log.write(chunk);log.flush()
                            clean=ANSI_ESCAPE.sub('',chunk.decode('utf-8','replace')).replace('\r','\n')
                            output_buf+=clean
                            if len(output_buf)>100000:output_buf=output_buf[-50000:]
                            while '\n' in output_buf:
                                row,output_buf=output_buf.split('\n',1)
                                if row.strip():tail.append(row[-500:])
                            # Password prompt is not emitted by Bash; detect common sudo text.
                            probe=output_buf[-250:]
                            if not waiting and re.search(r'(?i)(?:\[sudo\].*password|\[sudo\].*senha|senha para .*:|password for .*:)\s*$',probe):
                                waiting=True
                                password=_modal(win,'Senha do sudo','Digite a senha para autenticar o instalador.',secret=True)
                                if password is not None:os.write(master,(password+'\n').encode())
                                else:log_mode=True
                                output_buf='';waiting=False
                try:key=win.getch()
                except curses.error:key=-1
                if key in (ord('l'),ord('L')):log_mode=not log_mode
                elif key in (ord('t'),ord('T')):
                    # Use curses suspension for full fidelity with arbitrary prompts.
                    curses.def_prog_mode();curses.endwin()
                    print('\n[Terminal interativo: Ctrl+] volta ao painel; Ctrl+C interrompe]\n',flush=True)
                    import tty
                    old=termios.tcgetattr(sys.stdin.fileno())
                    tty.setraw(sys.stdin.fileno())
                    try:
                        while proc.poll() is None:
                            ready,_,_=select.select([sys.stdin.fileno(),master,er],[],[],0.1)
                            if sys.stdin.fileno() in ready:
                                data=os.read(sys.stdin.fileno(),1024)
                                if b'\x1d' in data:break
                                if b'\x03' in data:
                                    try:os.killpg(proc.pid,signal.SIGINT)
                                    except ProcessLookupError:pass
                                elif data:os.write(master,data)
                            if master in ready:
                                try:chunk=os.read(master,65536)
                                except OSError:chunk=b''
                                if chunk:
                                    os.write(sys.stdout.fileno(),chunk)
                                    log.write(chunk);log.flush()
                            if er in ready:
                                try:chunk=os.read(er,65536)
                                except OSError:chunk=b''
                                event_buf+=chunk
                                # Eventos serão processados ao voltar ao painel.
                                if len(event_buf)>200000:event_buf=event_buf[-100000:]
                    finally:
                        termios.tcsetattr(sys.stdin.fileno(),termios.TCSADRAIN,old)
                        # Processa eventos recebidos durante o terminal integral.
                        while b'\n' in event_buf:
                            raw,event_buf=event_buf.split(b'\n',1)
                            evt=raw.decode('utf-8','replace').strip()
                            if journal is not None: update_run(journal, run_data, event=evt)
                            bits=evt.split(':',2)
                            if len(bits)>=2 and bits[1] in statuses:
                                statuses[bits[1]]={'STEP_START':'RUN','STEP_DONE':'DONE','STEP_FAIL':'FAIL','STEP_SKIP':'SKIP'}.get(bits[0],statuses[bits[1]])
                        curses.reset_prog_mode();win.refresh()
                elif key==3:
                    try:os.killpg(proc.pid,signal.SIGINT)
                    except ProcessLookupError:pass
                if proc.poll() is not None:
                    # Drain pending output/events before leaving.
                    if not active_fds or not select.select(list(active_fds),[],[],0.15)[0]:break
            for n in step_names:
                if statuses[n]=='RUN':statuses[n]='FAIL'
            _install_draw(win,step_names,statuses,current,tail,time.monotonic()-started,True,0,False,packages)
            put(win,win.getmaxyx()[0]-1,2,'Finalizado. Pressione qualquer tecla para sair.',colors('yellow'))
            win.nodelay(False);win.getch()
    try:
        curses.wrapper(run)
    finally:
        for fd in (master,er):
            try:os.close(fd)
            except OSError:pass
        if proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGINT)
            except ProcessLookupError:pass
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
    result = proc.wait()
    if journal is not None: update_run(journal, run_data, code=result)
    return result

if __name__ == '__main__':
    sys.exit(main())

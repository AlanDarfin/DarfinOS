#!/usr/bin/env python3
"""DarfinOS Control Center: diagnósticos e backups locais, sem sudo ou instalação.

Não executa alterações de pacotes. Recuperação só modifica arquivos de configuração
da lista permitida mediante --apply; operações que sobrescrevem requerem --overwrite.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

PROFILE_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
MAX_FILE = 2 * 1024 * 1024
MAX_ARCHIVE = 20 * 1024 * 1024
MAX_ENTRIES = 80
SCHEMA = 1
CONFIG_FILES = (
    ".config/darfinos-tui/profile.json",
    ".config/fish/config.fish",
    ".config/starship.toml",
    ".config/fastfetch/config.jsonc",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def home_dir(home: Path | None = None) -> Path:
    return (home or Path.home()).expanduser().resolve()


def valid_name(value: str) -> str:
    if not PROFILE_PATTERN.fullmatch(value):
        raise ValueError("Nome inválido: use 1-40 letras ASCII, números, - ou _.")
    return value


def profile_path(name: str, home: Path | None = None) -> Path:
    root = home_dir(home)
    parent = root
    for segment in (".config", "darfinos-tui", "profiles"):
        parent = parent / segment
        if parent.is_symlink():
            raise ValueError("Diretório de perfis contém link simbólico")
    return parent / (valid_name(name) + ".json")


def load_profile(name: str, home: Path | None = None) -> dict:
    file = profile_path(name, home)
    if file.is_symlink():
        raise ValueError("Perfil não pode ser um link simbólico")
    payload = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("selected"), list):
        raise ValueError("Perfil inválido: falta selected")
    selected = payload["selected"]
    if (len(selected) > 80 or
            any(not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", item)
                for item in selected)):
        raise ValueError("Perfil inválido: etapas malformadas")
    return {"version": 1, "selected": sorted(set(selected)), "yes": False}


def save_private_json(path: Path, data: dict, overwrite: bool = False) -> None:
    if path.is_symlink() or (path.exists() and not overwrite):
        raise FileExistsError(f"Destino já existe ou é um link simbólico: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".darfinos-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        if overwrite:
            os.replace(temp, path)
        else:
            # Link atômico no mesmo filesystem: nunca sobrescreve destino criado
            # entre a verificação inicial e a gravação.
            os.link(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def export_profile(name: str, destination: Path, home: Path | None = None) -> None:
    data = load_profile(name, home)
    save_private_json(destination.expanduser(), data)


def import_profile(source: Path, name: str, home: Path | None = None,
                   replace: bool = False) -> None:
    if source.is_symlink() or source.stat().st_size > MAX_FILE:
        raise ValueError("Arquivo de perfil inseguro ou muito grande")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("selected"), list):
        raise ValueError("Perfil sem lista selected")
    selected = payload["selected"]
    if (len(selected) > 80 or
            any(not isinstance(x, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", x)
                for x in selected)):
        raise ValueError("Etapas inválidas no perfil")
    # Nunca importa --yes automaticamente de arquivos externos.
    save_private_json(profile_path(name, home),
                      {"version": 1, "selected": sorted(set(selected)), "yes": False},
                      overwrite=replace)


def diff_profiles(left: str, right: str, home: Path | None = None) -> dict:
    a = set(load_profile(left, home)["selected"])
    b = set(load_profile(right, home)["selected"])
    return {"base": left, "target": right, "add": sorted(b-a), "remove": sorted(a-b),
            "unchanged": len(a & b)}


def _read_only(argv: list[str]) -> dict:
    if not shutil.which(argv[0]):
        return {"available": False}
    try:
        process = subprocess.run(argv, capture_output=True, text=True, timeout=7,
                                 check=False)
        return {"available": True, "code": process.returncode,
                "lines": len(process.stdout.splitlines()),
                "output": process.stdout[:8192].strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": True, "error": type(exc).__name__}


def system_status(home: Path | None = None) -> dict:
    root = home_dir(home)
    history = root / ".local/state/darfinos-tui/runs"
    latest = None
    if history.is_dir():
        files = sorted(history.glob("run-*.json"), reverse=True)
        if files:
            try:
                if files[0].stat().st_size <= MAX_FILE:
                    data = json.loads(files[0].read_text(encoding="utf-8"))
                    latest = {"state": data.get("state"), "started_at": data.get("started_at")}
            except (OSError, ValueError, TypeError):
                pass
    packages = _read_only(["pacman", "-Qq"])
    root_fs = _read_only(["findmnt", "-n", "-o", "FSTYPE", "/"])
    available = None
    try:
        available = round(shutil.disk_usage(root).free / 1024**3, 2)
    except OSError:
        pass
    return {
        "arch": Path("/etc/arch-release").is_file(),
        "platform": platform.system(),
        "root": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
        "tools": {x: bool(shutil.which(x)) for x in
                  ("pacman", "sudo", "curl", "topgrade", "arch-update", "flatpak", "git")},
        "packages_installed": packages.get("lines")
        if packages.get("code") == 0 else None,
        "filesystem": root_fs.get("output") if root_fs.get("code") == 0 else None,
        "free_home_gib": available,
        "last_run": latest,
        "profiles": sorted(p.stem for p in
                           (root / ".config/darfinos-tui/profiles").glob("*.json")
                           if PROFILE_PATTERN.fullmatch(p.stem) and not p.is_symlink()),
    }


def maintenance_status(home: Path | None = None) -> dict:
    """Inventário observacional de ferramentas, tray e timers de atualização.

    Indica o que foi detectado, não declara que uma atualização funcionará.
    Não roda `topgrade` ou `arch-update --check`, nem modifica serviços.
    """
    root = home_dir(home)
    tools = {tool: bool(shutil.which(tool))
             for tool in ("topgrade", "arch-update", "arch-update-tray")}
    autostart_dir = root / ".config/autostart"
    autostart = []
    if autostart_dir.is_dir() and not autostart_dir.is_symlink():
        autostart = sorted(
            entry.name for entry in autostart_dir.glob("*.desktop")
            if "arch-update" in entry.name.casefold() and not entry.is_symlink()
        )
    timers: dict = {"available": False, "arch_update_detected": None}
    if shutil.which("systemctl"):
        query = _read_only(["systemctl", "--user", "list-timers", "--all",
                            "--no-pager", "--no-legend"])
        if query.get("code") == 0:
            timers = {"available": True, "arch_update_detected":
                      "arch-update" in query.get("output", "").casefold()}
        else:
            timers = {"available": False, "arch_update_detected": None,
                      "reason": "systemctl --user não acessível nesta sessão"}
    pacdiff = _read_only(["pacdiff", "--output"])
    pending = (pacdiff.get("output", "").splitlines() if pacdiff.get("code") == 0 else None)
    return {
        "config_review": {"pending": pending,
                          "note": "Lista somente leitura. Use Arch-Update para revisar."},
        "tools": tools,
        "arch_update_autostart_entries": autostart,
        "user_timers": timers,
        "note": "Detecção local parcial; iniciar bandeja e atualizar exigem teste em sessão gráfica.",
    }


def _allowed(relative: str) -> bool:
    path = PurePosixPath(relative)
    if str(path) != relative or path.is_absolute() or ".." in path.parts:
        return False
    if relative in CONFIG_FILES:
        return True
    return (len(path.parts) == 4 and
            path.parts[:3] == (".config", "darfinos-tui", "profiles") and
            path.suffix == ".json" and PROFILE_PATTERN.fullmatch(path.stem) is not None)


def _safe_target(root: Path, relative: str) -> Path:
    if not _allowed(relative):
        raise ValueError(f"Caminho não permitido: {relative}")
    target = root / relative
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Link simbólico não permitido: {current}")
    return target


def _candidate_files(root: Path) -> list[str]:
    files = list(CONFIG_FILES)
    profiles = root / ".config/darfinos-tui/profiles"
    if profiles.is_dir() and not profiles.is_symlink():
        files += [f".config/darfinos-tui/profiles/{p.name}"
                  for p in profiles.glob("*.json") if PROFILE_PATTERN.fullmatch(p.stem)]
    return sorted(set(files))


def create_backup(destination: Path, home: Path | None = None) -> dict:
    root = home_dir(home)
    files: list[tuple[str, bytes]] = []
    for relative in _candidate_files(root):
        target = _safe_target(root, relative)
        if not target.is_file():
            continue
        if target.stat().st_size > MAX_FILE:
            raise ValueError(f"Arquivo muito grande: {relative}")
        files.append((relative, target.read_bytes()))
    if not files:
        raise ValueError("Nenhum arquivo de configuração permitido foi encontrado")
    if len(files) > MAX_ENTRIES or sum(len(data) for _, data in files) > MAX_ARCHIVE:
        raise ValueError("Excesso de arquivos ou tamanho total para backup")
    manifest = {"schema": SCHEMA, "created_at": now(), "files": [
        {"path": relative, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        for relative, data in files]}
    destination = destination.expanduser()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Backup já existe: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=destination.parent, prefix=".darfinos-backup-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
                for relative, data in files:
                    archive.writestr("files/" + relative, data)
        if Path(temp).stat().st_size > MAX_ARCHIVE:
            raise ValueError("Backup ultrapassou limite de tamanho")
        # Evita substituir outro backup criado durante a gravação.
        os.link(temp, destination)
    finally:
        Path(temp).unlink(missing_ok=True)
    return manifest


def inspect_backup(source: Path, home: Path | None = None) -> tuple[dict, list[tuple[Path, bytes]]]:
    root = home_dir(home)
    if source.is_symlink() or source.stat().st_size > MAX_ARCHIVE:
        raise ValueError("Arquivo de backup inseguro ou acima do limite")
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        if len(names) > MAX_ENTRIES + 1 or len(names) != len(set(names)) or "manifest.json" not in names:
            raise ValueError("Backup com entradas inválidas")
        info = archive.getinfo("manifest.json")
        if info.file_size > MAX_FILE:
            raise ValueError("Manifesto muito grande")
        manifest = json.loads(archive.read("manifest.json"))
        if (not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or
                not isinstance(manifest.get("files"), list)):
            raise ValueError("Schema do backup incompatível")
        files = manifest["files"]
        expected = {"manifest.json"} | {"files/" + x["path"] for x in files
                                            if isinstance(x, dict) and isinstance(x.get("path"), str)}
        if len(files) > MAX_ENTRIES or set(names) != expected or len(expected) != len(names):
            raise ValueError("Entradas inesperadas no backup")
        restored = []
        total_size = 0
        for item in files:
            relative = item["path"]
            target = _safe_target(root, relative)
            member = archive.getinfo("files/" + relative)
            if (member.file_size > MAX_FILE or member.file_size != item.get("size") or
                    member.compress_size > MAX_ARCHIVE):
                raise ValueError(f"Tamanho inválido: {relative}")
            total_size += member.file_size
            if total_size > MAX_ARCHIVE:
                raise ValueError("Backup ultrapassa o limite total descompactado")
            data = archive.read(member)
            if hashlib.sha256(data).hexdigest() != item.get("sha256"):
                raise ValueError(f"SHA256 inválido: {relative}")
            restored.append((target, data))
    return manifest, restored


def restore_backup(source: Path, home: Path | None = None, apply: bool = False,
                   overwrite: bool = False) -> list[dict]:
    """Restaura arquivos em duas fases, revertendo substituições se ocorrer falha.

    A operação protege apenas os arquivos controlados pelo DarfinOS no HOME.
    Não é um snapshot transacional do sistema (ou de arquivos modificados
    simultaneamente por outras aplicações).
    """
    root = home_dir(home)
    _, files = inspect_backup(source, root)
    report = []
    for target, data in files:
        exists = target.exists()
        if exists and not target.is_file():
            raise ValueError(f"Destino não é arquivo regular: {target}")
        identical = (exists and target.stat().st_size == len(data)
                     and target.read_bytes() == data)
        report.append({"path": str(target), "exists": exists, "identical": bool(identical)})
    if not apply:
        return report

    # Pré-verificar todos os destinos, evitando modificar metade deles antes
    # de perceber um conflito ou diretório simbólico.
    for target, _ in files:
        relative = target.relative_to(root).as_posix()
        _safe_target(root, relative)
        if target.exists() and not overwrite:
            raise FileExistsError(f"Arquivo existente: {target} (use --overwrite)")
    marker = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    backups = {}
    for target, _ in files:
        previous = target.with_name(target.name + f".darfinos-pre-restore-{marker}.bak")
        if previous.exists() or previous.is_symlink():
            raise FileExistsError(f"Backup preventivo já existe: {previous}")
        backups[target] = previous

    # Escrever TODOS os arquivos temporários antes de substituir um existente.
    staged: dict[Path, Path] = {}
    applied: list[tuple[Path, Path | None]] = []
    try:
        for target, data in files:
            _safe_target(root, target.relative_to(root).as_posix())
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temp = tempfile.mkstemp(dir=target.parent, prefix=".darfinos-restore-")
            pending = Path(temp)
            staged[target] = pending
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())

        for target, _ in files:
            _safe_target(root, target.relative_to(root).as_posix())
            previous = backups[target] if target.exists() else None
            if previous is not None:
                os.replace(target, previous)
            # Registrar a mudança antes do próximo replace para proteger
            # inclusive falhas que ocorram entre o backup e a instalação.
            applied.append((target, previous))
            os.replace(staged[target], target)
    except OSError as exc:
        # Reversão na ordem inversa. Se não conseguirmos restaurar um destino,
        # preservar o .bak e informar explicitamente o problema.
        rollback_errors = []
        for target, previous in reversed(applied):
            try:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    os.replace(previous, target)
            except OSError as undo:
                rollback_errors.append(f"{target}: {undo}")
        if rollback_errors:
            raise RuntimeError("Falha ao restaurar: " + str(exc) +
                               "; reversão parcial: " + "; ".join(rollback_errors)) from exc
        raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)
    return report

STYLE_PROFILES = {
    "terminal": "Fish, Starship e Fastfetch do DarfinOS",
    "i3-compacto": "i3 compacto para telas de 720p",
    "workstation-1995": "Window Maker grafite e amarelo",
    "sonicde-kvantum": "Kvantum com KvDark em grafite e amarelo, sem mudar o painel",
    "i3-notebook": "DarfinOS Notebook 720p · painel, áudio, rede, calendário e Fastfetch",
}
STYLE_ROOT = ".local/state/darfinos-customization"
DEFAULT_ACCENT = "#ffcb2e"
NOTEBOOK_I3_CONFIG = ".config/i3/config"
NOTEBOOK_STYLE_DIR = ".config/darfinos/i3-notebook"
NOTEBOOK_STYLE_FILES = ("session.sh", "desktop.py", "panel.py", "media.py", "windows.py", "switcher.py", "settings.py",
                        "rofi.rasi", "dunstrc", "status.toml",
                        "polybar.ini", "wallpaper.svg", "fastfetch.jsonc", "logo.png")
NOTEBOOK_THEME_HOME = ".themes/DarfinOS-Notebook"
NOTEBOOK_FILES_THEME = f"{NOTEBOOK_THEME_HOME}/gtk-3.0/gtk.css"
NOTEBOOK_APPEARANCE = {
    NOTEBOOK_FILES_THEME: "files.css",
    f"{NOTEBOOK_THEME_HOME}/gtk-2.0/gtkrc": "gtk2.rc",
    f"{NOTEBOOK_THEME_HOME}/gtk-4.0/gtk.css": "gtk4.css",
    f"{NOTEBOOK_THEME_HOME}/Kvantum/DarfinOS-Notebook.kvconfig": "kvantum.ini",
    f"{NOTEBOOK_STYLE_DIR}/appearance/Trolltech.conf": "qt4.conf",
    f"{NOTEBOOK_STYLE_DIR}/appearance/Kvantum/kvantum.kvconfig": None,
}
NOTEBOOK_KDE_GLOBALS = f"{NOTEBOOK_STYLE_DIR}/appearance/kdeglobals"
NOTEBOOK_KDE_SCHEME = f"{NOTEBOOK_STYLE_DIR}/appearance/share/color-schemes/DarfinOSNotebook.colors"
NOTEBOOK_DOLPHIN_CONFIG = f"{NOTEBOOK_STYLE_DIR}/appearance/dolphinrc"
NOTEBOOK_KDE_PATHS = (NOTEBOOK_KDE_GLOBALS, NOTEBOOK_KDE_SCHEME, NOTEBOOK_DOLPHIN_CONFIG)
NOTEBOOK_KVANTUM_SVG = f"{NOTEBOOK_THEME_HOME}/Kvantum/DarfinOS-Notebook.svg"
NOTEBOOK_FASTFETCH_DEFAULTS = (".config/fastfetch/config.jsonc", ".config/fastfetch/logo.png")
FASTFETCH_DEFAULT_ACCENT = "38;2;255;203;46"


def _style_path(root: Path, relative: str) -> Path:
    """Only called with built-in paths (or paths from the fixed profile allowlist)."""
    current = root
    for part in PurePosixPath(relative).parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"Link simbólico não permitido: {current}")
    return current


def _style_read(path: Path) -> bytes | None:
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > MAX_FILE:
        raise ValueError(f"Arquivo não regular ou acima do limite: {path}")
    return path.read_bytes()


def _style_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, staged = tempfile.mkstemp(dir=path.parent, prefix=".darfinos-style-")
    try:
        with os.fdopen(fd, "wb") as f:
            os.fchmod(f.fileno(), mode & 0o777)
            f.write(data)
        os.replace(staged, path)
    finally:
        Path(staged).unlink(missing_ok=True)


def _edit_ini(data: bytes | None, group: str, key: str, value: str) -> bytes:
    """Set one key in a flat KConfig/QSettings group without serializing other settings."""
    text = (data or b"").decode()
    lines = text.splitlines(keepends=True)
    headers = [i for i, line in enumerate(lines) if line.strip() == f"[{group}]"]
    if any(line.strip().startswith(f"[{group}][") for line in lines):
        raise ValueError(f"Grupo protegido ou não plano: {group}")
    if len(headers) > 1:
        raise ValueError(f"Grupo duplicado: {group}")
    if not headers:
        ending = "" if not text or text.endswith("\n") else "\n"
        return (text + ending + f"\n[{group}]\n{key}={value}\n").encode()
    start = headers[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    key_pattern = re.compile(r"^\s*" + re.escape(key) + r"(?:\s*=|\[)")
    existing = [i for i in range(start, end) if key_pattern.match(lines[i])]
    if len(existing) > 1 or (existing and "[" in lines[existing[0]].split("=", 1)[0]):
        raise ValueError(f"Chave duplicada ou protegida: {group}/{key}")
    if existing:
        lines[existing[0]] = f"{key}={value}\n"
    else:
        if end and not lines[end-1].endswith("\n"):
            lines[end-1] += "\n"
        lines.insert(end, f"{key}={value}\n")
    return "".join(lines).encode()


def _render_style(template: str, accent: str) -> bytes:
    executable = shutil.which("chezmoi")
    if not executable:
        raise ValueError("Instale lab_chezmoi antes de usar este perfil.")
    with tempfile.TemporaryDirectory(prefix="darfinos-chezmoi-") as temp:
        # Use a private, empty config/source. Never evaluate the user's chezmoi repo.
        config = Path(temp) / "chezmoi.toml"
        config.write_text(f'[data]\naccent = "{accent}"\n', encoding="utf-8")
        result = subprocess.run(
            [executable, "--config", str(config), "--source", temp, "execute-template"],
            input=template, text=True, capture_output=True, check=False, timeout=20,
        )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Falha ao renderizar o template.")
    return result.stdout.encode()


def _style_paths(profile: str) -> tuple[str, ...]:
    return {
        "terminal": (".config/fish/conf.d/90-darfinos.fish", ".config/starship.toml",
                     ".config/fastfetch/config.jsonc", ".config/fastfetch/logo.png"),
        "i3-compacto": (".config/i3/config",),
        "i3-notebook": (NOTEBOOK_I3_CONFIG, *(f"{NOTEBOOK_STYLE_DIR}/{name}" for name in NOTEBOOK_STYLE_FILES),
                        *NOTEBOOK_APPEARANCE, *NOTEBOOK_KDE_PATHS, NOTEBOOK_KVANTUM_SVG, *NOTEBOOK_FASTFETCH_DEFAULTS),
        "workstation-1995": ("GNUstep/Library/WindowMaker/Styles/DarfinOS-1995.style",),
        "sonicde-kvantum": (".config/kdeglobals", ".config/Kvantum/kvantum.kvconfig",
                           ".config/Kvantum/DarfinOSGold/DarfinOSGold.kvconfig",
                           ".config/Kvantum/DarfinOSGold/DarfinOSGold.svg"),
    }[profile]


KVANTUM_BASE = Path("/usr/share/Kvantum/KvDark")


def _notebook_kvantum_svg(data: bytes, accent: str) -> bytes:
    """Tint active KvDark artwork, leaving normal widgets and transparent edges intact."""
    tree = ET.fromstring(data)
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    for node in tree:
        name = node.get("id", "")
        if not name.startswith(("progress-normal", "progress-pattern-normal", "slider-toggled",
                                "itemview-toggled", "tab-toggled-top")):
            continue
        for child in node.iter():
            # These active pieces use pre-painted gradients instead of QPalette.
            # Leave flat highlights, strokes and transparent geometry untouched.
            style = child.get("style")
            if style:
                child.set("style", re.sub(r"(?<![\w-])fill:url\(#[^)]+\)", f"fill:{accent}", style))
    return ET.tostring(tree, encoding="utf-8")


def _fastfetch_theme(source: Path, accent: str) -> tuple[bytes, bytes]:
    config = (source / "Fastfetch/config.jsonc").read_text(encoding="utf-8")
    # Raw SGR is also understood by versions of Fastfetch before hex support.
    rgb = ";".join(str(int(accent[i:i + 2], 16)) for i in (1, 3, 5))
    return (config.replace(FASTFETCH_DEFAULT_ACCENT, f"38;2;{rgb}").encode("utf-8"),
            (source / "Fastfetch/logo.png").read_bytes())


def _style_plan(profile: str, root: Path, accent: str) -> dict[str, tuple[bytes | None, bytes]]:
    if profile not in STYLE_PROFILES:
        raise ValueError("Perfil desconhecido.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        raise ValueError("Use uma cor hexadecimal #RRGGBB.")
    paths = _style_paths(profile)
    if profile == "i3-notebook":
        if not (KVANTUM_BASE / "KvDark.svg").is_file():
            paths = tuple(rel for rel in paths if rel != NOTEBOOK_KVANTUM_SVG)
        # Make plain fastfetch work on a fresh install, but never take over a
        # pre-existing Fastfetch config or logo (including symlinks).
        candidates = (*NOTEBOOK_FASTFETCH_DEFAULTS, ".config/fastfetch/config.json")
        try:
            occupied = any(_style_path(root, rel).exists() for rel in candidates)
        except ValueError:
            occupied = True
        if occupied:
            paths = paths[:-len(NOTEBOOK_FASTFETCH_DEFAULTS)]
    current = {rel: _style_read(_style_path(root, rel)) for rel in paths}
    source = Path(__file__).resolve().parent
    if profile == "terminal":
        files = (
            b"if status is-interactive; and type -q starship\n    starship init fish | source\nend\n",
            _render_style('add_newline = false\n[character]\nsuccess_symbol = "[❯]({{ .accent }})"\nerror_symbol = "[❯](bold red)"\n', accent),
            *_fastfetch_theme(source, accent),
        )
    elif profile == "i3-compacto":
        files = (_render_style('''# DarfinOS · i3 compacto
set $mod Mod4
font pango:monospace 9
default_border pixel 2
default_floating_border pixel 2
gaps inner 4
gaps outer 0
floating_modifier $mod
bindsym $mod+Return exec i3-sensible-terminal
bindsym $mod+d exec dmenu_run
bindsym $mod+Shift+q kill
bindsym $mod+Shift+r restart
bindsym $mod+Left focus left
bindsym $mod+Down focus down
bindsym $mod+Up focus up
bindsym $mod+Right focus right
bindsym $mod+Shift+Left move left
bindsym $mod+Shift+Down move down
bindsym $mod+Shift+Up move up
bindsym $mod+Shift+Right move right
bindsym $mod+h split h
bindsym $mod+v split v
bindsym $mod+w layout tabbed
bindsym $mod+e layout toggle split
bindsym $mod+f fullscreen toggle
bindsym $mod+Shift+space floating toggle
bindsym $mod+1 workspace number 1
bindsym $mod+2 workspace number 2
bindsym $mod+3 workspace number 3
bindsym $mod+Shift+1 move container to workspace number 1
bindsym $mod+Shift+2 move container to workspace number 2
bindsym $mod+Shift+3 move container to workspace number 3
client.focused {{ .accent }} #1c2026 #ffffff {{ .accent }} {{ .accent }}
bar {
    status_command i3status
    colors {
        background #171a1f
        statusline #f2f2f2
        focused_workspace {{ .accent }} #272727 #ffffff
    }
}
''', accent),)
    elif profile == "i3-notebook":
        theme = source / "themes/i3-notebook"
        templates = ((theme / name).read_text(encoding="utf-8")
                     for name in ("config", *NOTEBOOK_STYLE_FILES[:-2]))
        files = tuple(_render_style(text, accent) if "{{ .accent }}" in text else text.encode()
                      for text in templates)
        fetch_config, logo = _fastfetch_theme(source, accent)
        files += (fetch_config, logo)
        for name in NOTEBOOK_APPEARANCE.values():
            data = _render_style((theme / name).read_text(encoding="utf-8"), accent) if name else b"[General]\ntheme=DarfinOS-Notebook\n"
            files += (data,)
        # KColorScheme uses CSV RGB values rather than CSS hex. Lock only the
        # color keys in the Notebook search path so inherited KDE colors don't
        # win, without touching ~/.config/kdeglobals or the user's app state.
        rgb = ",".join(str(int(accent[j:j+2], 16)) for j in (1, 3, 5))
        kde = (theme / "kde.colors").read_text(encoding="utf-8").replace("{{ .accent }}", rgb)
        kde_globals = re.sub(r"(?m)^([^=\n]+)=", r"\1[$i]=", kde)
        files += (kde_globals.encode(), kde.encode(),
                  b"[UiSettings]\nColorScheme[$i]=DarfinOSNotebook\n")
        if NOTEBOOK_KVANTUM_SVG in paths:
            files += (_notebook_kvantum_svg((KVANTUM_BASE / "KvDark.svg").read_bytes(), accent),)
        if len(paths) > len(files):
            files += (fetch_config, logo)
    elif profile == "workstation-1995":
        files = (_render_style('''{
  FTitleBack = (solid, "#2a2d32");
  FTitleColor = "{{ .accent }}";
  UTitleBack = (solid, "#1b1d20");
  UTitleColor = "#d4d4d4";
  MenuTitleBack = (solid, "#2a2d32");
  MenuTitleColor = "{{ .accent }}";
  MenuTextBack = (solid, "#1b1d20");
  MenuTextColor = "#f0f0f0";
  IconBack = (solid, "#30343a");
}
''', accent),)
    else:
        base = KVANTUM_BASE
        theme_config = _style_read(base / "KvDark.kvconfig")
        theme_svg = _style_read(base / "KvDark.svg")
        if theme_config is None or theme_svg is None:
            raise ValueError("Instale lab_kvantum para usar o tema base KvDark.")
        theme_config = _edit_ini(theme_config, "GeneralColors", "highlight.color", accent)
        theme_config = _edit_ini(theme_config, "GeneralColors", "link.color", accent)
        theme_config = _edit_ini(theme_config, "%General", "comment", "DarfinOSGold (based on KvDark by Tsu Jan)")
        # Kvantum is a Qt application style, not a shell/panel/window decoration.
        files = (_edit_ini(current[paths[0]], "KDE", "widgetStyle", "kvantum"),
                 _edit_ini(current[paths[1]], "General", "theme", "DarfinOSGold"),
                 theme_config, theme_svg)
    return {rel: (current[rel], data) for rel, data in zip(paths, files)}


def style_preview(profile: str, accent: str = DEFAULT_ACCENT, home: Path | None = None) -> tuple[dict[str, tuple[bytes | None, bytes]], str]:
    plan = _style_plan(profile, home_dir(home), accent)
    lines = [f"{profile} · {STYLE_PROFILES[profile]}", ""]
    for rel, (old, new) in plan.items():
        if old == new:
            lines.append(f"  {rel}: idêntico")
            continue
        if rel.endswith((".png", ".svg")):
            lines.append(f"  {rel}: {'novo' if old is None else 'mudança'} ({len(new)} bytes)")
            continue
        before = (old or b"").decode(errors="replace").splitlines(keepends=True)
        after = new.decode().splitlines(keepends=True)
        lines.extend(line.rstrip("\n") for line in difflib.unified_diff(
            before, after, fromfile=("atual/" + rel if old is not None else "/dev/null"),
            tofile="perfil/" + rel, n=2))
    if all(old == new for old, new in plan.values()):
        lines.append("Nada a mudar.")
    return plan, "\n".join(lines)


def _style_hash(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def style_apply(profile: str, plan: dict, selected: list[str], home: Path | None = None) -> str:
    root = home_dir(home)
    allowed = set(_style_paths(profile))
    if not selected or not set(selected) <= set(plan) <= allowed:
        raise ValueError("Selecione apenas arquivos do perfil.")
    if profile == "i3-notebook" and NOTEBOOK_I3_CONFIG in selected:
        required = (f"{NOTEBOOK_STYLE_DIR}/{name}" for name in NOTEBOOK_STYLE_FILES)
        for rel in (*required, *NOTEBOOK_APPEARANCE, *NOTEBOOK_KDE_PATHS):
            if rel not in selected and (rel not in plan or _style_read(_style_path(root, rel)) != plan[rel][1]):
                raise ValueError("Para ativar o i3 Notebook, aplique também os arquivos do perfil.")
    if profile == "i3-notebook" and set(selected).intersection(NOTEBOOK_FASTFETCH_DEFAULTS):
        if not set(NOTEBOOK_FASTFETCH_DEFAULTS) <= set(selected):
            raise ValueError("Para instalar o Fastfetch padrão, selecione o tema e o logo juntos.")
        for rel in (*NOTEBOOK_FASTFETCH_DEFAULTS, ".config/fastfetch/config.json"):
            if _style_path(root, rel).exists():
                raise ValueError("Já existe uma configuração ou logo do Fastfetch. Refazer a prévia preserva seus arquivos.")
    changes = {rel: plan[rel] for rel in dict.fromkeys(selected) if plan[rel][0] != plan[rel][1]}
    if profile == "i3-notebook" and NOTEBOOK_I3_CONFIG in changes:
        # Publish the entry point after the files it uses.
        changes[NOTEBOOK_I3_CONFIG] = changes.pop(NOTEBOOK_I3_CONFIG)
    if not changes:
        return "Nada a mudar."
    for rel, (old, _) in changes.items():
        if _style_read(_style_path(root, rel)) != old:
            raise ValueError(f"Arquivo mudou desde a prévia: {rel}")
    directory = _style_path(root, STYLE_ROOT)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    journal = Path(tempfile.mkdtemp(dir=directory, prefix=profile + "-"))
    manifest = {}
    for idx, (rel, (old, new)) in enumerate(changes.items()):
        if old is not None:
            _style_write(journal / str(idx), old)
        manifest[rel] = {"backup": str(idx) if old is not None else None,
                         "before": _style_hash(old), "after": _style_hash(new),
                         "mode": _style_path(root, rel).stat().st_mode & 0o777 if old is not None else 0o600}
    _style_write(journal / "manifest.json", json.dumps({"profile": profile, "files": manifest}).encode())
    try:
        for rel, (old, new) in changes.items():
            target = _style_path(root, rel)
            if _style_read(target) != old:
                raise ValueError(f"Arquivo mudou durante a aplicação: {rel}")
            _style_write(target, new, manifest[rel]["mode"])
    except (ValueError, OSError) as exc:
        try:
            style_undo(journal.name, apply=True, home=root)
        except (ValueError, OSError) as restore:
            raise RuntimeError(f"{exc}. Reversão incompleta: {restore}. Cópias: {journal.name}") from exc
        raise RuntimeError(f"{exc}. As alterações aplicadas foram revertidas. Cópias: {journal.name}") from exc
    return f"Perfil aplicado. Desfazer: {journal.name}"


def style_undo(run: str, apply: bool = False, home: Path | None = None) -> str:
    if not re.fullmatch(r"[a-z0-9-]+-[A-Za-z0-9_]{8}", run):
        raise ValueError("Identificador de aplicação inválido.")
    root = home_dir(home)
    journal = _style_path(root, STYLE_ROOT + "/" + run)
    payload = json.loads(_style_read(_style_path(root, STYLE_ROOT + "/" + run + "/manifest.json")) or b"{}")
    profile = payload["profile"]
    allowed = set(_style_paths(profile))
    files = payload["files"]
    if not isinstance(files, dict) or not set(files) <= allowed:
        raise ValueError("Registro de personalização inválido.")
    actions = []
    for rel, item in files.items():
        target = _style_path(root, rel)
        current = _style_read(target)
        if _style_hash(current) != item["after"]:
            actions.append((rel, False, current, None))
            continue
        backup = item["backup"]
        if backup is not None and not re.fullmatch(r"[0-9]+", backup):
            raise ValueError("Nome de cópia inválido.")
        old = (_style_read(_style_path(root, (journal / backup).relative_to(root).as_posix()))
               if backup is not None else None)
        if _style_hash(old) != item["before"]:
            raise ValueError(f"Cópia de {rel} ausente ou alterada.")
        actions.append((rel, True, current, old))
    report = []
    for rel, ready, current, old in actions:
        target = _style_path(root, rel)
        if not ready or _style_read(target) != current:
            report.append(f"{rel}: mantido (mudou depois do perfil ou já foi restaurado)")
            continue
        if apply:
            if old is None:
                target.unlink()
            else:
                _style_write(target, old, files[rel].get("mode", 0o600))
        report.append(f"{rel}: {'restaurado' if apply else 'pronto para desfazer'}")
    return "\n".join(report) or "Nada a desfazer."


def style_history(home: Path | None = None) -> list[str]:
    root = home_dir(home)
    folder = _style_path(root, STYLE_ROOT)
    if not folder.is_dir():
        return []
    runs = [p for p in folder.iterdir() if not p.is_symlink() and
            not (p / "manifest.json").is_symlink() and (p / "manifest.json").is_file()]
    return [p.name for p in sorted(runs, key=lambda p: p.stat().st_mtime, reverse=True)]


def theme_palette(image: Path) -> dict[str, str]:
    tool = shutil.which("matugen")
    if not tool:
        raise ValueError("Instale lab_matugen para gerar a paleta.")
    image = image.expanduser().resolve(strict=True)
    if not image.is_file():
        raise ValueError("Informe um arquivo de imagem.")
    with tempfile.TemporaryDirectory(prefix="darfinos-matugen-") as folder:
        config = Path(folder) / "config.toml"
        config.write_text("[config]\n[templates]\n", encoding="utf-8")
        p = subprocess.run([tool, "--config", str(config), "image", str(image), "--json", "hex",
                            "--dry-run", "--source-color-index", "0"],
                           capture_output=True, text=True, timeout=45)
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or "Matugen não conseguiu ler a imagem.")
    raw = json.loads(p.stdout)["colors"]
    dark = raw.get("dark", raw)  # Matugen 4 groups modes by color name.
    colors = {}
    for key in ("primary", "secondary", "background", "on_background"):
        value = dark.get(key)
        if isinstance(value, dict):
            value = value.get("dark", value)
            if isinstance(value, dict):
                value = value.get("color") or value.get("hex")
        if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            colors[key] = value
    if "primary" not in colors:
        raise ValueError("Matugen não retornou uma cor de destaque válida.")
    return colors


def configure_maintenance_timer(enabled: bool, home: Path | None = None) -> str:
    """Opt-in, read-only periodic check. It never schedules upgrades or backups."""
    root = home_dir(home)
    systemctl = shutil.which("systemctl")
    if not systemctl:
        raise ValueError("systemctl indisponível.")
    unit = "darfinos-config-review"
    units = _style_path(root, ".config/systemd/user")
    timer = _style_path(root, f".config/systemd/user/{unit}.timer")
    service = _style_path(root, f".config/systemd/user/{unit}.service")
    def systemd(*args: str) -> None:
        proc = subprocess.run([systemctl, "--user", *args], capture_output=True, text=True, timeout=12)
        if proc.returncode:
            raise RuntimeError(proc.stderr.strip() or "Falha no systemd do usuário.")
    if not enabled:
        if not timer.exists():
            return "Timer do DarfinOS não está instalado."
        if not (_style_read(timer) or b"").startswith(b"# Managed by DarfinOS\n"):
            raise ValueError("Timer existente não pertence ao DarfinOS.")
        systemd("disable", "--now", unit + ".timer")
        return "Timer do DarfinOS desativado."
    python = str(Path(sys.executable).resolve())
    script = str(Path(__file__).resolve())
    # systemd tokenization is not shell syntax; escape quoting and specifiers.
    def quote(value: str) -> str:
        if any(ch in value for ch in "\n\r"):
            raise ValueError("Caminho do Control Center inválido para o timer.")
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%").replace("$", "$$") + '"'
    content = {
        service: ("# Managed by DarfinOS\n[Unit]\nDescription=DarfinOS read-only configuration review\n"
                  "[Service]\nType=oneshot\n"
                  f"ExecStart={quote(python)} {quote(script)} maintenance-notify\n").encode(),
        timer: ("# Managed by DarfinOS\n[Unit]\nDescription=Weekly DarfinOS configuration review\n"
                "[Timer]\nOnCalendar=weekly\nPersistent=true\n"
                f"Unit={unit}.service\n[Install]\nWantedBy=timers.target\n").encode(),
    }
    for path, data in content.items():
        previous = _style_read(path)
        if previous is not None and not previous.startswith(b"# Managed by DarfinOS\n"):
            raise ValueError(f"Arquivo externo existente: {path.name}")
    units.mkdir(parents=True, exist_ok=True)
    for path, data in content.items():
        if _style_read(path) != data:
            _style_write(path, data)
    systemd("daemon-reload")
    systemd("enable", "--now", unit + ".timer")
    return "Timer semanal ativado. Ele só verifica pendências e avisa."


def maintenance_notify() -> None:
    pending = maintenance_status()["config_review"]["pending"]
    if pending is None:
        print("Não foi possível consultar pendências. Verifique se pacman-contrib está instalado.")
    elif pending:
        message = f"{len(pending)} arquivos .pacnew/.pacsave ou .pacorig para revisar com Arch-Update."
        print(message)
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", "DarfinOS · revisão de configuração", message],
                           check=False, timeout=8)
    else:
        print("Nenhum arquivo de configuração pendente.")


def xfce_look(apply: bool = False) -> str:
    query = shutil.which("xfconf-query")
    if not query:
        raise ValueError("Instale lab_desktop_config para usar Xfconf.")
    if not os.environ.get("DISPLAY") or "xfce" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
        raise ValueError("Abra esta opção dentro de uma sessão Xfce.")
    props = [
        ("xsettings", "/Net/ThemeName", "Chicago95"),
        ("xsettings", "/Net/IconThemeName", "Chicago95"),
        ("xsettings", "/Gtk/CursorThemeName", "Chicago95_Standard_Cursors"),
        ("xfwm4", "/general/theme", "Chicago95"),
    ]
    paths = [".themes/Chicago95/index.theme", ".icons/Chicago95/index.theme",
             ".icons/Chicago95_Standard_Cursors/index.theme"]
    if not all((Path.home() / path).is_file() for path in paths):
        raise ValueError("Instale lab_chicago95 antes de aplicar o tema.")
    lines = []
    planned = []
    for channel, prop, value in props:
        command = [query, "--channel", channel, "--property", prop]
        old = subprocess.run(command, capture_output=True, text=True, timeout=8,
                             env={**os.environ, "LC_ALL": "C"})
        if old.returncode and "does not exist" not in old.stderr:
            raise RuntimeError(old.stderr.strip() or "Não foi possível consultar a sessão Xfce.")
        previous = old.stdout.strip() if not old.returncode else None
        lines.append(f"{channel}/{prop}: {previous or '(padrão)'} → {value}")
        if previous != value:
            planned.append((command, previous, value))
    if apply:
        applied = []
        try:
            for command, previous, value in planned:
                extra = [] if previous is not None else ["--create", "--type", "string"]
                changed = subprocess.run(command + extra + ["--set", value], capture_output=True,
                                         text=True, timeout=8)
                if changed.returncode:
                    raise RuntimeError(changed.stderr.strip() or f"Falha ao ajustar {command[-1]}.")
                applied.append((command, previous))
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            for command, previous in reversed(applied):
                options = ["--reset"] if previous is None else ["--set", previous]
                reverted = subprocess.run(command + options, capture_output=True, text=True, timeout=8)
                if reverted.returncode:
                    raise RuntimeError(f"{error}. Não foi possível reverter {command[-1]}.") from error
            raise
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DarfinOS Control Center · sem sudo")
    sub = parser.add_subparsers(dest="action", required=True)
    status = sub.add_parser("status", help="Estado do sistema (somente leitura)")
    status.add_argument("--json", action="store_true")
    maintenance = sub.add_parser("maintenance", help="Verificar Topgrade/Arch-Update sem executar")
    maintenance.add_argument("--json", action="store_true")
    exp = sub.add_parser("profile-export", help="Exportar perfil para JSON")
    exp.add_argument("name")
    exp.add_argument("path", type=Path)
    imp = sub.add_parser("profile-import", help="Importar perfil com execução automática desativada")
    imp.add_argument("path", type=Path)
    imp.add_argument("name")
    imp.add_argument("--replace", action="store_true")
    diff = sub.add_parser("profile-diff", help="Comparar etapas entre dois perfis")
    diff.add_argument("base")
    diff.add_argument("target")
    backup = sub.add_parser("backup", help="Criar arquivo ZIP com configurações permitidas")
    backup.add_argument("path", type=Path)
    restore = sub.add_parser("restore", help="Inspecionar backup; restaurar apenas com --apply")
    restore.add_argument("path", type=Path)
    restore.add_argument("--apply", action="store_true")
    restore.add_argument("--overwrite", action="store_true")
    sub.add_parser("styles", help="Listar perfis de personalização")
    style = sub.add_parser("style", help="Prévia ou aplicação seletiva de perfil")
    style.add_argument("name", choices=STYLE_PROFILES)
    style.add_argument("--accent", default=DEFAULT_ACCENT)
    style.add_argument("--apply", action="store_true")
    selection = style.add_mutually_exclusive_group()
    selection.add_argument("--file", action="append", default=[], help="Arquivo relativo ao HOME; pode repetir")
    selection.add_argument("--all-files", action="store_true", help="Selecionar todos os arquivos deste perfil")
    sub.add_parser("style-history", help="Listar aplicações que podem ser desfeitas")
    undo = sub.add_parser("style-undo", help="Prévia ou desfazer alterações de uma aplicação")
    undo.add_argument("run")
    undo.add_argument("--apply", action="store_true")
    palette = sub.add_parser("palette", help="Gerar uma prévia de paleta sem mudar o tema")
    palette.add_argument("image", type=Path)
    timer = sub.add_parser("maintenance-timer", help="Ativar ou desativar a revisão semanal de configuração")
    timer.add_argument("mode", choices=("enable", "disable"))
    sub.add_parser("maintenance-notify", help="Checar pendências e avisar, sem aplicar mudanças")
    xfce = sub.add_parser("xfce-look", help="Prévia ou ativação pontual do Chicago95 no Xfce")
    xfce.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "maintenance-timer":
            print(configure_maintenance_timer(args.mode == "enable"))
        elif args.action == "maintenance-notify":
            maintenance_notify()
        elif args.action == "xfce-look":
            print(xfce_look(args.apply))
        elif args.action == "styles":
            for name, description in STYLE_PROFILES.items():
                print(f"{name}: {description}")
        elif args.action == "style":
            plan, preview = style_preview(args.name, args.accent)
            if args.apply:
                print(style_apply(args.name, plan, list(plan) if args.all_files else args.file))
            else:
                print(preview)
        elif args.action == "style-history":
            print("\n".join(style_history()) or "Sem aplicações.")
        elif args.action == "style-undo":
            print(style_undo(args.run, args.apply))
        elif args.action == "palette":
            print(json.dumps(theme_palette(args.image), indent=2))
        elif args.action == "status":
            result = system_status()
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("DarfinOS · Diagnóstico local (somente leitura)")
                for key, value in result.items():
                    print(f"  {key}: {value}")
        elif args.action == "maintenance":
            result = maintenance_status()
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("DarfinOS · Ferramentas de manutenção (somente leitura)")
                for key, value in result.items():
                    print(f"  {key}: {value}")
        elif args.action == "profile-export":
            export_profile(args.name, args.path)
            print(f"Perfil exportado para {args.path}")
        elif args.action == "profile-import":
            import_profile(args.path, args.name, replace=args.replace)
            print(f"Perfil {args.name} importado com yes=false")
        elif args.action == "profile-diff":
            print(json.dumps(diff_profiles(args.base, args.target), indent=2))
        elif args.action == "backup":
            result = create_backup(args.path)
            print(f"Backup criado: {args.path} ({len(result['files'])} arquivos)")
            print("Atenção: o ZIP pode conter dados privados de configurações. Não o compartilhe.")
        elif args.action == "restore":
            result = restore_backup(args.path, apply=args.apply, overwrite=args.overwrite)
            for item in result:
                print(f"{item['path']}: {'existente' if item['exists'] else 'novo'}"
                      f"{' · idêntico' if item['identical'] else ''}")
            print("Restauração aplicada." if args.apply else
                  "Apenas prévia. Para aplicar, use --apply; sobrescrever exige --overwrite.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"DarfinOS: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

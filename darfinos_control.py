#!/usr/bin/env python3
"""DarfinOS Control Center: diagnósticos e backups locais, sem sudo ou instalação.

Não executa alterações de pacotes. Recuperação só modifica arquivos de configuração
da lista permitida mediante --apply; operações que sobrescrevem requerem --overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
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
        os.replace(temp, path)
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
    if len(files) > MAX_ENTRIES:
        raise ValueError("Excesso de arquivos para backup")
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
        os.replace(temp, destination)
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
        for item in files:
            relative = item["path"]
            target = _safe_target(root, relative)
            member = archive.getinfo("files/" + relative)
            if (member.file_size > MAX_FILE or member.file_size != item.get("size") or
                    member.compress_size > MAX_ARCHIVE):
                raise ValueError(f"Tamanho inválido: {relative}")
            data = archive.read(member)
            if hashlib.sha256(data).hexdigest() != item.get("sha256"):
                raise ValueError(f"SHA256 inválido: {relative}")
            restored.append((target, data))
    return manifest, restored


def restore_backup(source: Path, home: Path | None = None, apply: bool = False,
                   overwrite: bool = False) -> list[dict]:
    _, files = inspect_backup(source, home)
    report = [{"path": str(target), "exists": target.exists(),
               "identical": target.is_file() and target.read_bytes() == data}
              for target, data in files]
    if not apply:
        return report
    # Validar todos os conflitos antes de alterar o primeiro arquivo.
    for target, _ in files:
        if target.exists() and not overwrite:
            raise FileExistsError(f"Arquivo existente: {target} (use --overwrite)")
    marker = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    for target, _ in files:
        previous = target.with_name(target.name + f".darfinos-pre-restore-{marker}.bak")
        if previous.exists() or previous.is_symlink():
            raise FileExistsError(f"Backup preventivo já existe: {previous}")
    for target, data in files:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            previous = target.with_name(target.name + f".darfinos-pre-restore-{marker}.bak")
            os.replace(target, previous)
        fd, temp = tempfile.mkstemp(dir=target.parent, prefix=".darfinos-restore-")
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(data)
            os.replace(temp, target)
        finally:
            Path(temp).unlink(missing_ok=True)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DarfinOS Control Center · sem sudo")
    sub = parser.add_subparsers(dest="action", required=True)
    status = sub.add_parser("status", help="Estado do sistema (somente leitura)")
    status.add_argument("--json", action="store_true")
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
    args = parser.parse_args(argv)
    try:
        if args.action == "status":
            result = system_status()
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("DarfinOS · Diagnóstico local (somente leitura)")
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
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, RuntimeError) as exc:
        print(f"DarfinOS: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

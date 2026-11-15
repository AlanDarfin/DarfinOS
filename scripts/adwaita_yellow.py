#!/usr/bin/env python3
"""Install the pinned upstream Adwaita Yellow GTK3 themes without selecting them.

Theme selection belongs to the Control Center's preview/history workflow. This
helper downloads data only: it does not run upstream scripts or edit settings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.request

UPSTREAM = "https://github.com/merechinn/Adwaita-yellow-theme"
REVISION = "ab19a5e0737ec28506864b9bec849a76726250c9"
SHA256 = "e556a80954ae9dede6de8c497d3ec86ed4cbfe46c0aaba11c35d586390dbbe52"
ARCHIVE_URL = f"https://codeload.github.com/merechinn/Adwaita-yellow-theme/tar.gz/{REVISION}"
ARCHIVE_ROOT = f"Adwaita-yellow-theme-{REVISION}"
THEMES = ("Adwaita-yellow", "Adwaita-yellow-dark")
MARKER = ".darfinos-adwaita-yellow.json"
MAX_ARCHIVE = 32 * 1024 * 1024


def verify_archive(archive: Path, expected_sha: str = SHA256) -> None:
    if not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError("Arquivo Adwaita Yellow ausente ou acima do limite esperado.")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha:
        raise ValueError("SHA-256 do Adwaita Yellow não corresponde à revisão fixada.")


def download_archive(destination: Path) -> None:
    request = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": "DarfinOS-theme-installer"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as stream:
        size = 0
        while chunk := response.read(128 * 1024):
            size += len(chunk)
            if size > MAX_ARCHIVE:
                raise ValueError("Download Adwaita Yellow acima do limite esperado.")
            stream.write(chunk)
    verify_archive(destination)


def theme_ready(path: Path) -> bool:
    return ((path / "gtk-3.0/gtk.css").is_file()
            and (path / "gtk-3.0/gtk-contained.css").is_file())


def extract_themes(archive: Path, stage: Path) -> None:
    """Extract regular theme data, rejecting archive paths and link surprises."""
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if len(members) > 4096 or sum(member.size for member in members) > MAX_ARCHIVE:
            raise ValueError("Estrutura Adwaita Yellow acima do limite esperado.")
        for member in members:
            relative = PurePosixPath(member.name)
            if (relative.is_absolute() or ".." in relative.parts or not relative.parts
                    or relative.parts[0] != ARCHIVE_ROOT or not (member.isdir() or member.isfile())):
                raise ValueError("Caminho ou tipo de arquivo inesperado no Adwaita Yellow.")
            if len(relative.parts) < 2 or relative.parts[1] not in THEMES:
                continue
            target = stage.joinpath(*relative.parts[1:])
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = source.extractfile(member)
                if stream is None:
                    raise ValueError("Não consegui ler um arquivo do Adwaita Yellow.")
                with stream, target.open("wb") as output:
                    shutil.copyfileobj(stream, output)
                target.chmod(0o644)
    for theme in THEMES:
        target = stage / theme
        if not theme_ready(target):
            raise ValueError(f"Tema upstream incompleto: {theme}.")
        # Upstream ships the compiled GTK3 data, without index.theme metadata.
        # Add the standard descriptor locally; keep its CSS/assets unchanged.
        dark = theme.endswith("-dark")
        (target / "index.theme").write_text(
            "[Desktop Entry]\nType=X-GNOME-Metatheme\n"
            f"Name=Adwaita Yellow{' Dark' if dark else ''}\n"
            f"Comment=Upstream Adwaita Yellow GTK3 · {REVISION}\n\n"
            f"[X-GNOME-Metatheme]\nGtkTheme={theme}\n"
            "IconTheme=Papirus-Yellow\nCursorTheme=Bibata-Modern-Ice\n",
            encoding="utf-8",
        )
        (target / MARKER).write_text(json.dumps({"upstream": UPSTREAM, "revision": REVISION,
                                               "sha256": SHA256, "gtk_versions": [3]}, indent=2) + "\n")


def install_archive(archive: Path, themes_dir: Path, expected_sha: str = SHA256) -> dict[str, str]:
    verify_archive(archive, expected_sha)
    if themes_dir.is_symlink():
        raise ValueError(f"Diretório de temas com link simbólico preservado: {themes_dir}")
    themes_dir.mkdir(parents=True, exist_ok=True)
    for name in THEMES:
        target = themes_dir / name
        if target.is_symlink() or (target.exists() and not theme_ready(target)):
            raise ValueError(f"Destino existente preservado: {target}. Revise-o antes de instalar.")
    states = {}
    with tempfile.TemporaryDirectory(dir=themes_dir, prefix=".darfinos-adwaita-") as temporary:
        stage = Path(temporary)
        extract_themes(archive, stage)
        for name in THEMES:
            target = themes_dir / name
            if target.exists():
                states[name] = "preservado"
                continue
            os.rename(stage / name, target)
            states[name] = "instalado"
    return states


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use o arquivo local da mesma revisão e SHA-256 fixados.")
    args = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="darfinos-adwaita-download-") as temporary:
            archive = args.archive or Path(temporary) / "adwaita-yellow.tar.gz"
            if args.archive is None:
                download_archive(archive)
            installed = install_archive(archive, Path.home() / ".themes")
        for name, status in installed.items():
            print(f"Adwaita Yellow · {name}: {status}")
        print("Fonte: " + UPSTREAM)
        print("Temas GTK3 baixados. Selecione a aparência global pela prévia do Control Center.")
        return 0
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(1, f"Adwaita Yellow: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())

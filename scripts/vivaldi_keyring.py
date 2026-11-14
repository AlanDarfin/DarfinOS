"""Pin the existing Vivaldi key store without opening or modifying its profile."""
import argparse
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import tempfile

BACKENDS = ("kwallet6", "kwallet5", "gnome-libsecret")
APP = "com.vivaldi.Vivaldi"
MARKER = "X-DarfinOS-Vivaldi-Keyring=true"
APP_RUN = re.compile(r"^(Exec=.*?\brun[ \t]+.*?)\b" + re.escape(APP) + r"(?=[ \t]|$)")


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")


def file_data(path):
    if path.is_symlink():
        raise ValueError(f"Link simbólico não alterado: {path}")
    if path.exists():
        if not path.is_file() or path.stat().st_size > 256 * 1024:
            raise ValueError(f"Arquivo não regular ou muito grande: {path}")
        return path.read_text(encoding="utf-8")
    return None


def native_flags(before, backend):
    before = before or ""
    tokens = shlex.split(before, comments=True)
    for i, arg in enumerate(tokens):
        if arg == "--password-store" or arg.startswith("--password-store="):
            selected = arg.partition("=")[2] or (tokens[i + 1] if i + 1 < len(tokens) else "")
            if selected != backend:
                raise ValueError("Já existe uma opção --password-store diferente. Preserve-a até confirmar o chaveiro do perfil.")
            return before
    join = "" if not before or before.endswith("\n") else "\n"
    return before + join + f"--password-store={backend}\n"


def launcher(source, backend):
    out = []
    main = False
    main_exec = False
    for line in source.splitlines():
        if line.startswith("["):
            main = line == "[Desktop Entry]"
            out.append(line)
            if main:
                out.extend((MARKER, "DBusActivatable=false"))
            continue
        if main and (line.startswith("DBusActivatable=") or line == MARKER):
            continue
        if line.startswith("Exec="):
            match = APP_RUN.match(line)
            if not match or "--password-store" in line:
                raise ValueError("O lançador Flatpak não usa o formato esperado. Nenhuma configuração foi alterada.")
            line = line[:match.end()] + f" --password-store={backend}" + line[match.end():]
            main_exec |= main
        out.append(line)
    if not main_exec:
        raise ValueError("Lançador principal do Vivaldi não encontrado.")
    return "\n".join(out) + "\n"


def write_update(path, before, after):
    if before == after:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if before is not None:
        # Keep the original even when subsequently changing the chosen backend.
        backup = path.with_name(path.name + ".darfinos.bak")
        try:
            with backup.open("x", encoding="utf-8") as stream:
                stream.write(before)
        except FileExistsError:
            pass
    if file_data(path) != before:
        raise ValueError(f"Arquivo mudou durante a configuração: {path}")
    temp = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            os.fchmod(stream.fileno(), stat.S_IMODE(path.stat().st_mode) if before is not None else 0o644)
            stream.write(after)
        os.replace(temp, path)
    finally:
        if temp:
            temp.unlink(missing_ok=True)


def flatpak_source():
    for scope in ("--user", "--system"):
        try:
            info = subprocess.run(["flatpak", "info", scope, "--show-location", APP],
                                  text=True, capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            continue
        if info.returncode == 0 and info.stdout.strip():
            exported = Path(info.stdout.strip()) / "export/share/applications" / f"{APP}.desktop"
            if exported.is_file():
                return exported
    raise ValueError("Não encontrei o lançador exportado do Vivaldi Flatpak.")


def configure(backend, edition):
    if edition == "native":
        target = config_home() / "vivaldi-stable.conf"
        before = file_data(target)
        write_update(target, before, native_flags(before, backend))
    else:
        source = flatpak_source()
        target = data_home() / "applications" / f"{APP}.desktop"
        before = file_data(target)
        if before is not None and MARKER not in before.splitlines():
            raise ValueError("Já existe um lançador pessoal do Vivaldi Flatpak. Preserve-o e configure nele o mesmo --password-store.")
        write_update(target, before, launcher(source.read_text(encoding="utf-8"), backend))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edition", choices=("flatpak", "native"))
    parser.add_argument("backend", choices=BACKENDS)
    args = parser.parse_args()
    try:
        path = configure(args.backend, args.edition)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"DarfinOS: {exc}\n")
    print(f"Vivaldi: {args.backend} configurado em {path}.")
    print("Feche todo o Vivaldi e abra pelo menu. A senha do chaveiro ainda pode ser solicitada.")


if __name__ == "__main__":
    main()

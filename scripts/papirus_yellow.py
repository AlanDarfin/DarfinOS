"""Install a per-user Papirus Yellow overlay and apply it across desktop sessions."""
import argparse
import configparser
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

THEME = "Papirus-Yellow"
SYSTEM_ICONS = Path("/usr/share/icons")
MARKER = ".darfinos-papirus"
VARIANT = re.compile(r"(folder|user)-yellow((?:-[\w-]+)?)\.svg")


def same_write(path, text):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"Arquivo não regular preservado: {path}")
    previous = path.read_text(encoding="utf-8") if path.exists() else None
    if previous == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if previous is not None:
        try:
            with path.with_name(path.name + ".darfinos-icons.bak").open("x", encoding="utf-8") as backup:
                backup.write(previous)
        except FileExistsError:
            pass
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as temp:
        try:
            temp.write(text)
            temp.close()
            os.replace(temp.name, path)
        finally:
            Path(temp.name).unlink(missing_ok=True)


def ini_value(path, group, key, value):
    old = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = old.splitlines()
    heading = f"[{group}]"
    if heading not in lines:
        if lines and lines[-1]:
            lines.append("")
        lines.extend((heading, f"{key}={value}"))
    else:
        start = lines.index(heading) + 1
        end = next((idx for idx in range(start, len(lines)) if lines[idx].lstrip().startswith("[")), len(lines))
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
        matching = [i for i in range(start, end) if pattern.match(lines[i])]
        if matching:
            lines[matching[0]] = f"{key}={value}"
            for i in reversed(matching[1:]):
                del lines[i]
        else:
            lines.insert(start, f"{key}={value}")
    same_write(path, "\n".join(lines) + "\n")


def install_theme(icons, source=SYSTEM_ICONS):
    base = source / "Papirus"
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(base / "index.theme", encoding="utf-8")
    if not parser.has_section("Icon Theme"):
        raise ValueError("Pacote papirus-icon-theme não encontrado.")
    entries = {}
    base_theme = parser["Icon Theme"]
    standard = base_theme.get("Directories", "").split(",")
    scaled = base_theme.get("ScaledDirectories", "").split(",")
    for item in dict.fromkeys(standard + scaled):
        directory = item.strip()
        if not re.fullmatch(r"\d+x\d+(?:@\d+x)?/places", directory) or not parser.has_section(directory):
            continue
        for icon in sorted((base / directory).glob("*-yellow*.svg")):
            m = VARIANT.fullmatch(icon.name)
            if m and icon.is_file():
                entries.setdefault(directory, {})[m[1] + m[2] + ".svg"] = icon.resolve()
        # Legacy aliases (e.g. folder_home and inode-directory) can point to
        # the generic blue name. Keep those aliases yellow in the overlay too.
        names = entries.get(directory)
        if names:
            for icon in (base / directory).glob("*.svg"):
                if icon.name in names or not icon.is_symlink():
                    continue
                link = icon.readlink()
                if link.parent == Path(".") and link.name in names:
                    names[icon.name] = names[link.name]
    if not any("folder.svg" in names for names in entries.values()):
        raise ValueError("O Papirus instalado não contém as pastas amarelas oficiais.")

    target = icons / THEME
    if target.is_symlink() or (target.exists() and not (target / MARKER).is_file()):
        raise ValueError(f"Tema pessoal preservado: {target}")
    icons.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=icons, prefix=".darfinos-papirus-") as temp:
        stage = Path(temp) / THEME
        stage.mkdir()
        index = ["[Icon Theme]\nName=Papirus Yellow (DarfinOS)\nComment=Papirus Dark with yellow folders\n"
                 "Inherits=Papirus-Dark,Papirus,hicolor\n"]
        for key, directories in (("Directories", standard), ("ScaledDirectories", scaled)):
            index[0] += f"{key}=" + ",".join(item.strip() for item in directories if item.strip() in entries) + "\n"
        for directory, names in entries.items():
            place = stage / directory
            place.mkdir(parents=True)
            for name, icon in names.items():
                (place / name).symlink_to(icon)
            section = parser[directory]
            index.append(f"[{directory}]\nSize={section['Size']}\nContext=Places\nType={section.get('Type', 'Fixed')}\n")
            for field in ("MinSize", "MaxSize", "Threshold", "Scale"):
                if field in section:
                    index[-1] += f"{field}={section[field]}\n"
        (stage / "index.theme").write_text("\n".join(index), encoding="utf-8")
        (stage / MARKER).touch()
        previous = Path(temp) / "previous"
        if target.exists():
            target.rename(previous)
        try:
            stage.rename(target)
        except OSError:
            if previous.exists():
                previous.rename(target)
            raise
    return target


def gtk2_theme(path):
    old = path.read_text(encoding="utf-8") if path.is_file() else ""
    pattern = r"(?m)^[ \t]*gtk-icon-theme-name[ \t]*=[^\n]*\n?"
    updated = re.sub(pattern, "", old).rstrip()
    same_write(path, (updated + "\n" if updated else "") + f'gtk-icon-theme-name="{THEME}"\n')


def run_setting(*args):
    try:
        return subprocess.run(args, check=False, timeout=5, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def link_theme(icons, installed):
    link = icons / THEME
    if link.resolve() != installed.resolve():
        icons.mkdir(parents=True, exist_ok=True)
        link.symlink_to(installed, target_is_directory=True)


def select_theme(home, config, installed):
    tde = Path(os.environ.get("TDEHOME") or home / ".trinity").expanduser()
    qt_paths = [config / tool / f"{tool}.conf" for tool in ("qt5ct", "qt6ct")]
    settings = [
        (config / version / "settings.ini", "Settings", "gtk-icon-theme-name")
        for version in ("gtk-3.0", "gtk-4.0")
    ] + [
        (config / "kdeglobals", "Icons", "Theme"),
        (tde / "share/config/kdeglobals", "Icons", "Theme"),
    ] + [(path, "Appearance", "icon_theme") for path in qt_paths if path.exists()]

    errors = []

    def apply(operation, *args):
        try:
            operation(*args)
        except (OSError, ValueError, ET.ParseError) as exc:
            errors.append(str(exc))

    for path, group, key in settings:
        apply(ini_value, path, group, key, THEME)
    apply(gtk2_theme, home / ".gtkrc-2.0")
    apply(link_theme, tde / "share/icons", installed)
    apply(xfce_theme, config)
    if os.environ.get("DBUS_SESSION_BUS_ADDRESS") and shutil.which("gsettings"):
        # This schema is optional on a minimal WM. GTK desktops which own
        # XSETTINGS may read their own settings instead of settings.ini.
        run_setting("gsettings", "set", "org.gnome.desktop.interface", "icon-theme", THEME)
    if errors:
        raise ValueError("\n".join(errors))


def xfce_theme(config):
    # Xfce publishes its own XSETTINGS. Set that channel as well as GTK files.
    xfconf = shutil.which("xfconf-query")
    if xfconf and os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        command = [xfconf, "-c", "xsettings", "-p", "/Net/IconThemeName"]
        if run_setting(*command, "-s", THEME) or run_setting(*command, "-n", "-t", "string", "-s", THEME):
            return
    path = config / "xfce4/xfconf/xfce-perchannel-xml/xsettings.xml"
    channel = ET.parse(path).getroot() if path.is_file() else ET.Element("channel", name="xsettings", version="1.0")
    net = channel.find("./property[@name='Net']")
    if net is None:
        net = ET.SubElement(channel, "property", name="Net", type="empty")
    theme = net.find("./property[@name='IconThemeName']")
    if theme is None:
        theme = ET.SubElement(net, "property", name="IconThemeName")
    theme.attrib.update(type="string", value=THEME)
    ET.indent(channel)
    same_write(path, '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(channel, encoding="unicode") + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-only", action="store_true", help="Install the theme without selecting it in other desktops.")
    args = parser.parse_args()
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    try:
        path = install_theme(home / ".icons")
        data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
        link_theme(data / "icons", path)
        if not args.assets_only:
            select_theme(home, config, path)
    except (OSError, ValueError, configparser.Error, ET.ParseError) as exc:
        parser.exit(1, f"Papirus Yellow: {exc}\n")
    print(f"Papirus Yellow: {path}. Reabra os aplicativos ou a sessão para aplicar.")


if __name__ == "__main__":
    main()

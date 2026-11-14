"""Tests for Papirus's desktop settings and sparse yellow overlay."""
import configparser
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from scripts import papirus_yellow


class PapirusYellowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.source = root / "system"
        self.home = root / "home"
        self.config = root / "config"
        self.icons = self.home / ".icons"
        base = self.source / "Papirus"
        self.places = base / "48x48/places"
        self.places.mkdir(parents=True)
        (base / "index.theme").write_text(
            "[Icon Theme]\nName=Papirus\nDirectories=48x48/places\n"
            "[48x48/places]\nContext=Places\nSize=48\nType=Fixed\n"
        )
        for name in ("folder-blue", "folder-yellow", "folder-yellow-documents", "user-yellow-home"):
            (self.places / f"{name}.svg").write_text(name)
        (self.places / "folder.svg").symlink_to("folder-blue.svg")
        (self.places / "inode-directory.svg").symlink_to("folder.svg")

    def install(self):
        return papirus_yellow.install_theme(self.icons, self.source)

    def test_overlay_uses_only_yellow_variants_and_keeps_base_icons(self):
        overlay = self.install()
        index = configparser.ConfigParser()
        index.read(overlay / "index.theme")
        self.assertEqual(index["Icon Theme"]["Inherits"], "Papirus-Dark,Papirus,hicolor")
        files = overlay / "48x48/places"
        self.assertEqual((files / "folder.svg").read_text(), "folder-yellow")
        self.assertEqual((files / "folder-documents.svg").read_text(), "folder-yellow-documents")
        self.assertEqual((files / "user-home.svg").read_text(), "user-yellow-home")
        self.assertEqual((files / "inode-directory.svg").read_text(), "folder-yellow")
        self.assertEqual((self.places / "folder.svg").read_text(), "folder-blue")
        self.assertEqual(self.install(), overlay)

    def test_existing_unmanaged_theme_is_preserved(self):
        target = self.icons / "Papirus-Yellow"
        target.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "Tema pessoal"):
            self.install()
        self.assertTrue(target.is_dir())

    def test_desktop_settings_keep_original_palettes_and_other_preferences(self):
        overlay = self.install()
        kde = self.config / "kdeglobals"
        gtk = self.config / "gtk-3.0/settings.ini"
        qt = self.config / "qt6ct/qt6ct.conf"
        xfce = self.config / "xfce4/xfconf/xfce-perchannel-xml/xsettings.xml"
        xdg_icons = self.home / ".local/share/icons"
        tde = self.home / ".trinity-custom"
        initial = {
            kde: "[General]\nColorScheme=DarfinOS\n[Icons]\nTheme=Adwaita\n",
            gtk: "[Settings]\ngtk-theme-name=DarfinOS\ngtk-icon-theme-name=Adwaita\n",
            qt: "[Appearance]\nstyle=kvantum\n",
            self.home / ".gtkrc-2.0": 'gtk-theme-name="DarfinOS"\n',
            xfce: '<channel name="xsettings"><property name="Net" type="empty">'
                  '<property name="ThemeName" type="string" value="DarfinOS"/></property></channel>',
        }
        for path, value in initial.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
        papirus_yellow.link_theme(xdg_icons, overlay)
        self.assertEqual((xdg_icons / "Papirus-Yellow").resolve(), overlay)
        with patch.dict("os.environ", {"DBUS_SESSION_BUS_ADDRESS": "", "TDEHOME": str(tde)}):
            for _ in range(2):
                papirus_yellow.select_theme(self.home, self.config, overlay)
        for path, other_value in [(kde, "ColorScheme=DarfinOS"), (gtk, "gtk-theme-name=DarfinOS"),
                                  (qt, "style=kvantum"), (self.home / ".gtkrc-2.0", 'gtk-theme-name="DarfinOS"')]:
            text = path.read_text()
            self.assertIn("Papirus-Yellow", text)
            self.assertIn(other_value, text)
            self.assertEqual(path.with_name(path.name + ".darfinos-icons.bak").read_text(), initial[path])
        self.assertIn("Papirus-Yellow", (self.config / "gtk-4.0/settings.ini").read_text())
        self.assertIn("Theme=Papirus-Yellow", (tde / "share/config/kdeglobals").read_text())
        self.assertEqual((tde / "share/icons/Papirus-Yellow").resolve(), overlay)
        channel = ET.parse(xfce)
        self.assertEqual(channel.find(".//property[@name='ThemeName']").get("value"), "DarfinOS")
        self.assertEqual(channel.find(".//property[@name='IconThemeName']").get("value"), "Papirus-Yellow")

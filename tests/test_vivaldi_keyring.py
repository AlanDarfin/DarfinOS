"""Verify launcher changes use the selected backend and never inspect profile data."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import vivaldi_keyring as vivaldi

EXPORTED = """[Desktop Entry]
Name=Vivaldi
DBusActivatable=true
Exec=/usr/bin/flatpak run --branch=stable --command=vivaldi --file-forwarding com.vivaldi.Vivaldi @@u %U @@
[Desktop Action Private]
Name=Private
Exec=/usr/bin/flatpak run --command=vivaldi com.vivaldi.Vivaldi --incognito
"""


class VivaldiTests(unittest.TestCase):
    def test_flatpak_keeps_urls_and_actions(self):
        text = vivaldi.launcher(EXPORTED, "kwallet6")
        self.assertIn("DBusActivatable=false", text)
        self.assertIn("com.vivaldi.Vivaldi --password-store=kwallet6 @@u %U @@", text)
        self.assertIn("com.vivaldi.Vivaldi --password-store=kwallet6 --incognito", text)

    def test_flatpak_updates_its_own_launcher_without_touching_profile(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = base / "export.desktop"
            package.write_text(EXPORTED)
            profile = base / ".var/app/com.vivaldi.Vivaldi/config/vivaldi/Default/Preferences"
            profile.parent.mkdir(parents=True)
            profile.write_text("profile data")
            with patch.object(vivaldi, "data_home", return_value=base), patch.object(vivaldi, "flatpak_source", return_value=package):
                target = vivaldi.configure("kwallet6", "flatpak")
                vivaldi.configure("kwallet6", "flatpak")
            self.assertEqual(target.read_text().count("--password-store=kwallet6"), 2)
            self.assertEqual(profile.read_text(), "profile data")

    def test_flatpak_does_not_replace_a_personal_launcher(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "applications/com.vivaldi.Vivaldi.desktop"
            target.parent.mkdir()
            target.write_text("my own launcher")
            with patch.object(vivaldi, "data_home", return_value=base), patch.object(vivaldi, "flatpak_source"):
                with self.assertRaisesRegex(ValueError, "lançador pessoal"):
                    vivaldi.configure("kwallet6", "flatpak")
            self.assertEqual(target.read_text(), "my own launcher")

    def test_native_preserves_flags_and_rejects_a_different_backend(self):
        with TemporaryDirectory() as tmp, patch.object(vivaldi, "config_home", return_value=Path(tmp)):
            target = Path(tmp) / "vivaldi-stable.conf"
            original = '# local flags\n--disable-features=Example\n'
            target.write_text(original)
            vivaldi.configure("kwallet6", "native")
            vivaldi.configure("kwallet6", "native")
            self.assertEqual(target.read_text(), original + "--password-store=kwallet6\n")
            self.assertEqual(target.with_suffix(".conf.darfinos.bak").read_text(), original)
            with self.assertRaisesRegex(ValueError, "diferente"):
                vivaldi.configure("gnome-libsecret", "native")

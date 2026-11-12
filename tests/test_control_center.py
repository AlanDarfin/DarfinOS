"""Testes do Control Center: não tocam em pacman, sudo ou rede."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import darfinos_control as control


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()
        self.profile_dir = self.home / ".config/darfinos-tui/profiles"
        self.profile_dir.mkdir(parents=True)
        (self.profile_dir / "minimal.json").write_text(
            json.dumps({"version": 1, "selected": ["base", "maintenance"], "yes": True}))
        (self.profile_dir / "gaming.json").write_text(
            json.dumps({"version": 1, "selected": ["base", "gaming", "maintenance"]}))
        fish = self.home / ".config/fish/config.fish"
        fish.parent.mkdir(parents=True)
        fish.write_text("set -gx EDITOR nvim\n", encoding="utf-8")

    def test_profile_roundtrip_disables_automatic_yes(self):
        destination = self.home / "export.json"
        control.export_profile("minimal", destination, home=self.home)
        self.assertFalse(json.loads(destination.read_text())["yes"])
        control.import_profile(destination, "imported", home=self.home)
        self.assertFalse(control.load_profile("imported", self.home)["yes"])
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            control.import_profile(destination, "imported", home=self.home)
        self.assertEqual(control.diff_profiles("minimal", "gaming", self.home)["add"], ["gaming"])

    def test_invalid_profile_names_are_rejected(self):
        for name in ("../x", "nested/path", "", " space", "ç", "a"*41):
            with self.subTest(name=name), self.assertRaises(ValueError):
                control.profile_path(name, self.home)

    def test_backup_is_private_and_restore_is_preview_first(self):
        backup = self.home / "darfinos.zip"
        manifest = control.create_backup(backup, self.home)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        self.assertTrue(any(x["path"].endswith("config.fish") for x in manifest["files"]))
        with self.assertRaises(FileExistsError):
            control.create_backup(backup, self.home)
        fish = self.home / ".config/fish/config.fish"
        fish.write_text("mudou\n")
        preview = control.restore_backup(backup, self.home)
        self.assertTrue(any(not x["identical"] for x in preview))
        self.assertEqual(fish.read_text(), "mudou\n")
        with self.assertRaises(FileExistsError):
            control.restore_backup(backup, self.home, apply=True)
        control.restore_backup(backup, self.home, apply=True, overwrite=True)
        self.assertEqual(fish.read_text(), "set -gx EDITOR nvim\n")
        self.assertEqual(len(list(fish.parent.glob("config.fish.darfinos-pre-restore-*.bak"))), 1)

    def test_archive_escapes_refused(self):
        archive = self.home / "bad.zip"
        relative = "../outside"
        payload = b"wrong"
        manifest = {"schema": 1, "files": [
            {"path": relative, "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}]}
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("manifest.json", json.dumps(manifest))
            zipped.writestr("files/" + relative, payload)
        with self.assertRaises(ValueError):
            control.restore_backup(archive, self.home, apply=True, overwrite=True)
        self.assertFalse((self.home.parent / "outside").exists())

    def test_hash_tampering_refused_before_any_writes(self):
        archive = self.home / "badsha.zip"
        rel = ".config/fish/config.fish"
        manifest = {"schema": 1, "files": [{"path": rel, "sha256": "a"*64, "size": 4}]}
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("manifest.json", json.dumps(manifest))
            zipped.writestr("files/" + rel, b"oops")
        original = (self.home / rel).read_bytes()
        with self.assertRaises(ValueError):
            control.restore_backup(archive, self.home, apply=True, overwrite=True)
        self.assertEqual((self.home / rel).read_bytes(), original)

    def test_symlink_in_destination_tree_refused(self):
        other = Path(self.tmp.name) / "outside"
        other.mkdir()
        config = self.home / ".config/fish"
        (config / "config.fish").unlink()
        config.rmdir()
        config.symlink_to(other, target_is_directory=True)
        with self.assertRaises(ValueError):
            control.create_backup(self.home / "backup.zip", self.home)

    def test_status_is_observational(self):
        with mock.patch.object(control, "_read_only") as cmd:
            cmd.side_effect = lambda argv: {"available": False}
            result = control.system_status(self.home)
        self.assertEqual(result["packages_installed"], None)
        self.assertIn("minimal", result["profiles"])
        self.assertIn("topgrade", result["tools"])
        calls = [call.args[0] for call in cmd.call_args_list]
        self.assertEqual(calls, [["pacman", "-Qq"], ["findmnt", "-n", "-o", "FSTYPE", "/"]])


if __name__ == "__main__":
    unittest.main()

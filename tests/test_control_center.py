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

    def test_restore_reverts_all_files_when_commit_fails(self):
        archive = self.home / "transaction.zip"
        control.create_backup(archive, self.home)
        fish = self.home / ".config/fish/config.fish"
        profile = self.profile_dir / "gaming.json"
        fish.write_text("minha versão\n", encoding="utf-8")
        profile.write_text('{"selected": ["minha-etapa"]}', encoding="utf-8")
        prior_fish, prior_profile = fish.read_bytes(), profile.read_bytes()
        real_replace = control.os.replace

        def fail_during_install(source, destination):
            # Falha depois que o original foi movido para .bak.
            if (Path(destination) == fish and
                    Path(source).name.startswith(".darfinos-restore-")):
                raise OSError("falha simulada ao instalar arquivo")
            return real_replace(source, destination)

        with mock.patch.object(control.os, "replace", side_effect=fail_during_install):
            with self.assertRaises(OSError):
                control.restore_backup(archive, self.home, apply=True, overwrite=True)
        self.assertEqual(fish.read_bytes(), prior_fish)
        self.assertEqual(profile.read_bytes(), prior_profile)
        self.assertFalse(list(self.home.rglob(".darfinos-restore-*")))
        self.assertFalse(list(self.home.rglob("*.darfinos-pre-restore-*.bak")))

    def test_rejects_oversized_archive_contents(self):
        archive = self.home / "large.zip"
        relative = ".config/fish/config.fish"
        content = b"x" * (control.MAX_FILE + 1)
        manifest = {"schema": 1, "files": [
            {"path": relative, "sha256": hashlib.sha256(content).hexdigest(),
             "size": len(content)}]}
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr("manifest.json", json.dumps(manifest))
            zipped.writestr("files/" + relative, content)
        with self.assertRaises(ValueError):
            control.restore_backup(archive, self.home, apply=True, overwrite=True)

    def test_save_private_json_does_not_overwrite_race_winner(self):
        target = self.home / "profile.json"
        original_link = control.os.link

        def concurrent_creation(source, destination):
            Path(destination).write_text("arquivo concorrente", encoding="utf-8")
            return original_link(source, destination)

        with mock.patch.object(control.os, "link", side_effect=concurrent_creation):
            with self.assertRaises(FileExistsError):
                control.save_private_json(target, {"yes": False})
        self.assertEqual(target.read_text(), "arquivo concorrente")

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

    def test_maintenance_health_is_read_only(self):
        autostart = self.home / ".config/autostart"
        autostart.mkdir(parents=True)
        (autostart / "arch-update-tray.desktop").write_text("[Desktop Entry]\n")
        with (mock.patch.object(control.shutil, "which", side_effect=lambda name:
                                "/usr/bin/" + name if name in ("systemctl", "topgrade") else None),
              mock.patch.object(control, "_read_only", return_value={
                  "code": 0, "output": "arch-update.timer", "available": True}) as runner):
            report = control.maintenance_status(self.home)
        self.assertTrue(report["tools"]["topgrade"])
        self.assertFalse(report["tools"]["arch-update"])
        self.assertIn("arch-update-tray.desktop", report["arch_update_autostart_entries"])
        self.assertTrue(report["user_timers"]["arch_update_detected"])
        runner.assert_called_once_with([
            "systemctl", "--user", "list-timers", "--all", "--no-pager", "--no-legend"
        ])

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

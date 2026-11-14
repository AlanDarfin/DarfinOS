"""Exercise previews, selective writes, drift-aware undo, and timer isolation."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import darfinos_control as control


class CustomizationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)

    def fake_chezmoi(self):
        return mock.patch.object(control, "_render_style",
                                 side_effect=lambda template, accent: template.replace("{{ .accent }}", accent).encode())

    def test_preview_selective_apply_idempotence_and_undo(self):
        fish = ".config/fish/conf.d/90-darfinos.fish"
        starship = ".config/starship.toml"
        target = self.home / starship
        target.parent.mkdir()
        target.write_bytes(b"my old starship\n")
        target.chmod(0o644)
        with self.fake_chezmoi():
            plan, preview = control.style_preview("terminal", home=self.home)
            self.assertIn("my old starship", preview)
            self.assertFalse((self.home / fish).exists())
            self.assertFalse((self.home / control.STYLE_ROOT).exists())
            control.style_apply("terminal", plan, [fish, starship], self.home)
            self.assertFalse((self.home / ".config/fastfetch/config.jsonc").exists())
            self.assertEqual(target.stat().st_mode & 0o777, 0o644)
            plan, _ = control.style_preview("terminal", home=self.home)
            self.assertEqual(control.style_apply("terminal", plan, [fish, starship], self.home), "Nada a mudar.")
            run = control.style_history(self.home)[0]
            self.assertIn("pronto para desfazer", control.style_undo(run, home=self.home))
            control.style_undo(run, apply=True, home=self.home)
        self.assertFalse((self.home / fish).exists())
        self.assertEqual(target.read_bytes(), b"my old starship\n")

    def test_undo_preserves_user_edits_and_apply_rejects_stale_preview(self):
        rel = ".config/i3/config"
        with self.fake_chezmoi():
            first, _ = control.style_preview("i3-compacto", home=self.home)
            control.style_apply("i3-compacto", first, [rel], self.home)
            with self.assertRaisesRegex(ValueError, "desde a prévia"):
                control.style_apply("i3-compacto", first, [rel], self.home)
        target = self.home / rel
        target.write_bytes(b"new custom configuration")
        msg = control.style_undo(control.style_history(self.home)[0], True, self.home)
        self.assertIn("mantido", msg)
        self.assertEqual(target.read_bytes(), b"new custom configuration")

    def test_i3_notebook_matches_accents_preserves_global_settings_and_undoes(self):
        target = self.home / control.NOTEBOOK_I3_CONFIG
        target.parent.mkdir(parents=True)
        target.write_bytes(b"my old i3\n")
        dunst = self.home / ".config/dunst/dunstrc"
        dunst.parent.mkdir()
        dunst.write_bytes(b"my global dunst\n")
        with self.fake_chezmoi():
            plan, preview = control.style_preview("i3-notebook", "#aacc33", self.home)
            self.assertEqual(len(plan), 1 + len(control.NOTEBOOK_STYLE_FILES) + 3)
            self.assertIn(f"{control.NOTEBOOK_STYLE_DIR}/polybar.ini", plan)
            self.assertIn(f"{control.NOTEBOOK_STYLE_DIR}/wallpaper.svg", plan)
            self.assertIn(control.NOTEBOOK_FILES_THEME, plan)
            self.assertIn("my old i3", preview)
            for name, (_, content) in plan.items():
                if name.endswith(("fastfetch.jsonc", "config.jsonc")):
                    self.assertIn(b"38;2;170;204;51", content)
                elif not name.endswith(("session.sh", "desktop.py", "media.py", "switcher.py", "settings.py", ".png")):
                    self.assertIn(b"#aacc33", content)
                self.assertNotIn(b"{{ .accent }}", content)
                if name != control.NOTEBOOK_I3_CONFIG:
                    self.assertFalse((self.home / name).exists())
            with self.assertRaisesRegex(ValueError, "aplique também"):
                control.style_apply("i3-notebook", plan, [control.NOTEBOOK_I3_CONFIG], self.home)
            self.assertEqual(target.read_bytes(), b"my old i3\n")
            control.style_apply("i3-notebook", plan, list(plan), self.home)
            self.assertIn(b"DarfinOS", target.read_bytes())
            self.assertEqual(dunst.read_bytes(), b"my global dunst\n")
            control.style_undo(control.style_history(self.home)[0], True, self.home)
        self.assertEqual(target.read_bytes(), b"my old i3\n")
        self.assertEqual(dunst.read_bytes(), b"my global dunst\n")
        self.assertFalse((self.home / control.NOTEBOOK_FILES_THEME).exists())
        for name in control.NOTEBOOK_STYLE_FILES:
            self.assertFalse((self.home / control.NOTEBOOK_STYLE_DIR / name).exists())

    @unittest.skipUnless(shutil.which("chezmoi"), "requires the real template engine")
    def test_i3_notebook_renders_popup_with_real_chezmoi(self):
        plan, _ = control.style_preview("i3-notebook", "#aacc33", self.home)
        data = plan[f"{control.NOTEBOOK_STYLE_DIR}/panel.py"][1]
        self.assertIn(b'ACCENT = "#aacc33"', data)
        self.assertIn(b"#notebook-popup { background:", data)
        compile(data, "panel.py", "exec")
        data = plan[f"{control.NOTEBOOK_STYLE_DIR}/windows.py"][1]
        self.assertIn(b'ACCENT = "#aacc33"', data)
        compile(data, "windows.py", "exec")

    def test_i3_notebook_preserves_existing_fastfetch_but_has_its_own_preset(self):
        global_config = self.home / ".config/fastfetch/config.jsonc"
        global_config.parent.mkdir(parents=True)
        with self.fake_chezmoi():
            first, _ = control.style_preview("i3-notebook", home=self.home)
            self.assertIn(".config/fastfetch/logo.png", first)
            global_config.write_text("my Fastfetch config")
            with self.assertRaisesRegex(ValueError, "Já existe"):
                control.style_apply("i3-notebook", first, list(first), self.home)
            plan, _ = control.style_preview("i3-notebook", home=self.home)
            self.assertNotIn(".config/fastfetch/config.jsonc", plan)
            self.assertNotIn(".config/fastfetch/logo.png", plan)
            control.style_apply("i3-notebook", plan, list(plan), self.home)
        self.assertEqual(global_config.read_text(), "my Fastfetch config")
        self.assertTrue((self.home / control.NOTEBOOK_STYLE_DIR / "logo.png").is_file())
        self.assertTrue((self.home / control.NOTEBOOK_STYLE_DIR / "fastfetch.jsonc").is_file())

    def test_kvantum_only_edits_the_intended_config_keys(self):
        base = self.home / "base"
        base.mkdir()
        (base / "KvDark.svg").write_bytes(b"<svg/>")
        (base / "KvDark.kvconfig").write_bytes(b"[%General]\nauthor=upstream\n[GeneralColors]\nhighlight.color=#999999\nlink.color=blue\n")
        desktop = self.home / ".config/kdeglobals"
        desktop.parent.mkdir()
        desktop.write_bytes(b"[KDE]\nwidgetStyle=breeze\nShowIconsOnPushButtons=true\n[General]\nColorScheme=BreezeDark\n")
        with mock.patch.object(control, "KVANTUM_BASE", base):
            plan, preview = control.style_preview("sonicde-kvantum", home=self.home)
            self.assertIn("+widgetStyle=kvantum", preview)
            control.style_apply("sonicde-kvantum", plan, list(plan), self.home)
            _, preview = control.style_preview("sonicde-kvantum", home=self.home)
            self.assertIn("Nada a mudar.", preview)
        self.assertIn(b"ColorScheme=BreezeDark", desktop.read_bytes())
        self.assertIn(b"ShowIconsOnPushButtons=true", desktop.read_bytes())
        self.assertIn(b"highlight.color=#ffcb2e", (self.home / ".config/Kvantum/DarfinOSGold/DarfinOSGold.kvconfig").read_bytes())

    def test_rejects_symlinks_and_locked_kconfig(self):
        with self.assertRaisesRegex(ValueError, "protegido"):
            control._edit_ini(b"[KDE][$i]\nwidgetStyle=breeze\n", "KDE", "widgetStyle", "kvantum")
        (self.home / ".config").symlink_to("/tmp")
        with self.assertRaisesRegex(ValueError, "Link simbólico"), self.fake_chezmoi():
            control.style_preview("i3-compacto", home=self.home)

    def test_matugen4_palette_uses_dry_run_and_no_user_hooks(self):
        image = self.home / "wallpaper.jpg"
        image.touch()
        payload = {"colors": {"primary": {"dark": {"color": "#ffcb2e"}}}}
        with (mock.patch.object(control.shutil, "which", return_value="/usr/bin/matugen"),
              mock.patch.object(control.subprocess, "run", return_value=subprocess.CompletedProcess(
                  [], 0, json.dumps(payload), "")) as command):
            self.assertEqual(control.theme_palette(image), {"primary": "#ffcb2e"})
            self.assertIn("--dry-run", command.call_args.args[0])
            self.assertIn("--source-color-index", command.call_args.args[0])

    def test_timer_only_enables_read_only_review(self):
        with (mock.patch.object(control.shutil, "which", return_value="/usr/bin/systemctl"),
              mock.patch.object(control.subprocess, "run", return_value=subprocess.CompletedProcess(
                  [], 0, "", "")) as command):
            control.configure_maintenance_timer(True, self.home)
            folder = self.home / ".config/systemd/user"
            self.assertIn("maintenance-notify", (folder / "darfinos-config-review.service").read_text())
            self.assertIn("OnCalendar=weekly", (folder / "darfinos-config-review.timer").read_text())
            control.configure_maintenance_timer(False, self.home)
            self.assertEqual(command.call_args.args[0], [
                "/usr/bin/systemctl", "--user", "disable", "--now", "darfinos-config-review.timer"])

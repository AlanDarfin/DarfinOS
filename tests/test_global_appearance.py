"""Global GTK selection preserves other keys/CSS and is reversible."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import darfinos_control as control


class GlobalAppearanceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="DarfinOS global home ")
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        theme = self.home / ".themes/Adwaita-yellow-dark/gtk-3.0"
        theme.mkdir(parents=True)
        (theme / "gtk.css").write_text("/* installed upstream */")
        context = patch.object(control, "_render_style", side_effect=lambda text, accent: text.replace("{{ .accent }}", accent).encode())
        context.start()
        self.addCleanup(context.stop)

    def test_global_appearance_preserves_css_keys_is_idempotent_and_undoes(self):
        settings = self.home / ".config/gtk-3.0/settings.ini"
        settings.parent.mkdir(parents=True)
        original = "[Settings]\ngtk-theme-name=OldTheme\ngtk-enable-animations=false\n"
        settings.write_text(original)
        css = settings.with_name("gtk.css")
        css.write_text(".my-app { font-size: 12pt; }\n")
        plan, preview = control.style_preview("adwaita-yellow", home=self.home)
        self.assertIn("Adwaita-yellow-dark", preview)
        self.assertEqual(settings.read_text(), original)
        with self.assertRaisesRegex(ValueError, "recursos do tema"):
            control.style_apply("adwaita-yellow", plan, [".config/gtk-3.0/settings.ini"], self.home)
        report = control.style_apply("adwaita-yellow", plan, list(plan), self.home)
        self.assertIn("global salva", report)
        self.assertIn("gtk-theme-name=Adwaita-yellow-dark", settings.read_text())
        self.assertIn("gtk-enable-animations=false", settings.read_text())
        self.assertIn(".my-app", css.read_text())
        self.assertIn("%20", css.read_text())
        plan, _ = control.style_preview("adwaita-yellow", home=self.home)
        self.assertTrue(all(before == after for before, after in plan.values()))
        self.assertEqual(css.read_text().count("/* DarfinOS global appearance */"), 1)
        run = control.style_history(self.home)[0]
        control.style_undo(run, True, self.home)
        self.assertEqual(settings.read_text(), original)
        self.assertEqual(css.read_text(), ".my-app { font-size: 12pt; }\n")
        self.assertFalse((self.home / control.GLOBAL_STYLE_DIR / "gtk-4.0/gtk.css").exists())

    def test_global_profile_requires_downloaded_upstream_theme(self):
        (self.home / ".themes/Adwaita-yellow-dark/gtk-3.0/gtk.css").unlink()
        with self.assertRaisesRegex(ValueError, "scripts/adwaita_yellow.py"):
            control.style_preview("adwaita-yellow", home=self.home)

    def test_global_profile_has_gtk4_compatibility_without_claiming_upstream_gtk4(self):
        plan, _ = control.style_preview("adwaita-yellow", "#aacc33", self.home)
        gtk4 = plan[".config/gtk-4.0/settings.ini"][1]
        self.assertIn(b"gtk-theme-name=Adwaita", gtk4)
        self.assertNotIn(b"Adwaita-yellow-dark", gtk4)
        self.assertIn(b"#aacc33", plan[control.GLOBAL_STYLE_DIR + "/gtk-4.0/gtk.css"][1])
        self.assertNotIn(b"gtk-cursor-theme-size", plan[control.GLOBAL_STYLE_DIR + "/gtk-2.0/gtkrc"][1])

"""Exercise the notebook's display, wallpaper and cursor settings without X11."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "notebook_desktop", Path(__file__).resolve().parents[1] / "themes/i3-notebook/desktop.py"
)
desktop = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = desktop
spec.loader.exec_module(desktop)

QUERY = """Screen 0: minimum 8 x 8, current 1920 x 1080, maximum 32767 x 32767
eDP-1 connected primary 1440x810+0+0 (normal left inverted right x axis y axis)
   1920x1080     59.97*+  60.00
   1280x720      60.00    30.00
HDMI-1 connected 1920x1080+1440+0 (normal left inverted right x axis y axis)
   1920x1080     60.00*+
   1280x720      60.00
DP-1 disconnected (normal left inverted right x axis y axis)
"""


def result(code=0, stdout=""):
    return subprocess.CompletedProcess([], code, stdout=stdout)


class DesktopTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.profile = self.home / ".config/darfinos/i3-notebook"
        self.profile.mkdir(parents=True)
        self.settings = self.profile / "desktop.json"
        ctx = patch.multiple(desktop, HOME=self.home, PROFILE=self.profile, SETTINGS=self.settings)
        ctx.start()
        self.addCleanup(ctx.stop)

    def test_output_mode_is_not_framebuffer_geometry_and_external_is_not_targeted(self):
        panel, hdmi = desktop.parse_outputs(QUERY)
        self.assertEqual((panel.name, panel.current, panel.rate, panel.geometry),
                         ("eDP-1", "1920x1080", "59.97", "1440x810"))
        self.assertIs(desktop.panel_for_720p([panel, hdmi]), panel)
        self.assertIsNone(desktop.panel_for_720p([hdmi]))
        panel.modes.remove("1280x720")
        self.assertIsNone(desktop.panel_for_720p([panel, hdmi]))

    def test_diagnosis_does_not_change_resolution_until_requested(self):
        with patch.object(desktop, "read_outputs", return_value=desktop.parse_outputs(QUERY)), \
             patch.object(desktop.shutil, "which", return_value=True), \
             patch.object(desktop, "run", return_value=result(1)) as command:
            desktop.display_picker()
            self.assertIn("eDP-1   1920x1080 @ 59.97 Hz  ·  área X11 1440x810", command.call_args.args[-1])
            self.assertIn("Usar 1280×720", command.call_args.kwargs["input"])
            self.assertEqual(command.call_count, 1)
        self.assertFalse(self.settings.exists())

    def test_rejected_720p_restores_mode_and_rate(self):
        menu = result(stdout="Usar 1280×720 na tela interna\n")
        with patch.object(desktop, "read_outputs", return_value=desktop.parse_outputs(QUERY)), \
             patch.object(desktop.shutil, "which", return_value=True), \
             patch.object(desktop, "run", side_effect=[menu, result(), result(1), result()]) as command:
            desktop.display_picker()
            self.assertEqual(command.call_args_list[1].args, ("xrandr", "--output", "eDP-1", "--mode", "1280x720"))
            self.assertEqual(command.call_args.args,
                             ("xrandr", "--output", "eDP-1", "--mode", "1920x1080", "--rate", "59.97"))
        self.assertFalse(self.settings.exists())

    def test_accepted_720p_preserves_wallpaper_setting(self):
        desktop.save_settings(wallpaper="/some image.png")
        with patch.object(desktop, "read_outputs", return_value=desktop.parse_outputs(QUERY)), \
             patch.object(desktop.shutil, "which", return_value=True), \
             patch.object(desktop, "run", side_effect=[result(stdout="Usar 1280×720 na tela interna\n"),
                                                       result(), result(), result()]):
            desktop.display_picker()
        self.assertEqual(desktop.read_settings(), {"wallpaper": "/some image.png", "mode_720p": True})

    def test_wallpaper_is_saved_and_applied_as_a_literal_path(self):
        image = self.home / "Alan's imagem.png"
        image.touch()
        with patch.object(desktop.shutil, "which", return_value=True), \
             patch.object(desktop, "run", side_effect=[result(stdout=f"{image}\n"), result(), result()]) as command, \
             patch.object(desktop, "apply_cursor"):
            desktop.wallpaper_picker()
            self.assertEqual(desktop.read_settings()["wallpaper"], str(image))
            desktop.desktop_start()
            self.assertEqual(command.call_args.args, ("feh", "--no-fehbg", "--bg-fill", "--", str(image)))

    def test_default_wallpaper_renders_without_replacing_user_preference(self):
        (self.profile / "wallpaper.svg").write_text("<svg/>")
        with patch.object(desktop, "load_background", side_effect=[False, True]) as load, \
             patch.object(desktop.shutil, "which", return_value=True), \
             patch.object(desktop, "run", return_value=result()) as command:
            desktop.apply_background("/removed/wallpaper.png")
            self.assertEqual(command.call_args.args[:2], ("rsvg-convert", "-o"))
            self.assertEqual(command.call_args.args[3], str(self.profile / "wallpaper.svg"))
            self.assertEqual(load.call_args.args, (command.call_args.args[2],))
        self.assertFalse(self.settings.exists())

    def test_window_title_keeps_one_short_plain_text_line(self):
        self.assertEqual(desktop.clean_title("  "), "Área de trabalho")
        self.assertEqual(desktop.clean_title(" Editor\n%{A:x:}"), "Editor ％{A:x:}")
        self.assertEqual(desktop.clean_title("á" * 40), "á" * 27 + "…")
        self.assertEqual(desktop.focused_title({"floating_nodes": [
            {"focused": True, "window": 99, "name": "Terminal de bolso"}]}), "Terminal de bolso")

    def test_sonicde_cursor_is_imported_without_overwriting_settings(self):
        config = self.home / ".config/kcminputrc"
        config.write_text("[Mouse]\ncursorTheme=Bibata-Modern-Ice\ncursorSize=32\n")
        pointer = self.home / ".local/share/icons/Bibata-Modern-Ice/cursors/left_ptr"
        pointer.parent.mkdir(parents=True)
        pointer.touch()
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(config.parent), "XDG_DATA_HOME": str(self.home / ".local/share")}), \
             patch.object(desktop.shutil, "which", side_effect=lambda name: name if name in {"xrdb", "xsetroot"} else None), \
             patch.object(desktop, "run", return_value=result()) as command:
            desktop.apply_cursor()
        self.assertEqual(command.call_args_list[0].kwargs["input"],
                         "Xcursor.theme: Bibata-Modern-Ice\nXcursor.size: 32\n")
        self.assertEqual(command.call_args.args, ("xsetroot", "-xcf", str(pointer), "32"))
        self.assertIn("cursorSize=32", config.read_text())

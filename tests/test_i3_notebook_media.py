"""Offline tests for the media dock selector and subprocess arguments."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

THEME = Path(__file__).resolve().parents[1] / "themes/i3-notebook"
spec = importlib.util.spec_from_file_location("notebook_media", THEME / "media.py")
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class NotebookMediaTests(unittest.TestCase):
    def test_prefers_playing_and_keeps_a_paused_player_after_playback(self):
        self.assertIsNone(media.select({"vlc": "Paused"}))
        self.assertEqual(media.select({"vlc": "Paused"}, "vlc"), "vlc")
        self.assertEqual(media.select({"vlc": "Paused", "firefox": "Playing"}, "vlc"), "firefox")
        self.assertEqual(media.select({"vlc": "Playing", "firefox": "Playing"}, "firefox"), "firefox")
        self.assertIsNone(media.select({"vlc": "Stopped"}, "vlc"))

    def test_dock_actions_hold_the_exact_player_and_do_not_include_unsafe_data(self):
        for playing, icon in (("Playing", "󰏤"), ("Paused", "󰐊")):
            row = media.render("firefox.instance_2", playing)
            for action in ("previous", "play-pause", "next"):
                self.assertIn(f"{action} firefox.instance_2:", row)
            self.assertIn(icon, row)
        self.assertEqual(media.render("evil:;app", "Playing"), "")
        self.assertEqual(media.render("firefox", "Stopped"), "")

    def test_action_does_not_fall_through_to_another_player(self):
        with patch.object(media.sys, "argv", ["media.py", "next", "vlc.instance42"]):
            with patch.object(media, "run_player", return_value=None) as run:
                self.assertEqual(media.main(), 1)
                run.assert_called_once_with("--player", "vlc.instance42", "next")

    def test_rejects_bad_player_rows(self):
        with patch.object(media, "run_player", return_value="app;bad Playing\nfirefox.instance2 Playing\nvlc Stopped\n"):
            self.assertEqual(media.players(), {"firefox.instance2": "Playing", "vlc": "Stopped"})

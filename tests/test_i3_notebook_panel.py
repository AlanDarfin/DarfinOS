"""No GUI or sound server is needed for these backend tests."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "notebook_panel", Path(__file__).resolve().parents[1] / "themes/i3-notebook/panel.py"
)
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


class NotebookPanelTests(unittest.TestCase):
    def test_pipewire_reads_separate_devices_and_mute(self):
        with patch.object(panel, "command", side_effect=["Volume: 0.75\n", "Volume: 0.36 [MUTED]\n"]) as run:
            self.assertEqual(panel.audio_state("sink"), panel.Audio("wire", 75, False))
            self.assertEqual(panel.audio_state("source"), panel.Audio("wire", 36, True))
        self.assertEqual(run.call_args_list[0].args, ("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"))
        self.assertEqual(run.call_args_list[1].args, ("wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"))

    def test_pulse_fallback_averages_channels_and_clamps(self):
        with patch.object(panel, "command", side_effect=[
            None, "Volume: front-left: 0 / 124% / 0 dB, front-right: 0 / 120% / 0 dB",
            "Mute: yes\n",
        ]):
            self.assertEqual(panel.audio_state("sink"), panel.Audio("pulse", 100, True))

    def test_missing_devices_are_not_treated_as_zero_volume(self):
        with patch.object(panel, "command", return_value=None):
            self.assertIsNone(panel.audio_state("sink"))
            self.assertEqual(panel.audio_label("source"), "󰍭 —")

    def test_volume_and_mute_actions_target_only_the_requested_device(self):
        with patch.object(panel, "command", return_value="") as run:
            self.assertTrue(panel.audio_change("source", "wire", 122))
            run.assert_called_once_with("wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SOURCE@", "100%")
        with patch.object(panel, "command", return_value="") as run:
            self.assertTrue(panel.audio_change("sink", "pulse"))
            run.assert_called_once_with("pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle")

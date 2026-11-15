"""No GUI or sound server is needed for these backend tests."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "notebook_panel", Path(__file__).resolve().parents[1] / "themes/i3-notebook/panel.py"
)
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


class NotebookPanelTests(unittest.TestCase):
    def test_notification_state_reports_pause_and_visible_queued_counts(self):
        with patch.object(panel, "command", side_effect=["true\n", "2\n", "5\n"]):
            self.assertEqual(panel.notification_state(), {"paused": True, "displayed": 2, "waiting": 5})
        with patch.object(panel, "command", return_value=None) as command:
            self.assertIsNone(panel.notification_state())
            self.assertEqual(command.call_count, 1)
        for state, expected in ((None, "󰂛 —"),
                                ({"paused": True, "displayed": 0, "waiting": 7}, "󰂛 7"),
                                ({"paused": False, "displayed": 0, "waiting": 0}, "󰂚")):
            with self.subTest(state=state), patch.object(panel, "notification_state", return_value=state):
                self.assertEqual(panel.notification_label(), expected)

    def test_notification_history_unwraps_dbus_variants_as_bounded_plain_text(self):
        history = {"type": "aa{sv}", "data": [[
            {"appname": {"type": "s", "data": "Steam"},
             "summary": {"type": "s", "data": "<b>Download</b> &amp; pronto"},
             "body": {"type": "s", "data": "Texto\n" + "x" * 900}},
            {"summary": "Mensagem simples", "body": "Olá"},
            {"summary": {"data": ["wrong type"]}},
        ]]}
        result = panel.notification_history(json.dumps(history))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["app"], "Steam")
        self.assertEqual(result[0]["summary"], "Download & pronto")
        self.assertEqual(len(result[0]["body"]), 600)
        self.assertEqual(result[1]["body"], "Olá")
        for malformed in (None, "invalid", "{}", '{"data":false}', '["invalid"]'):
            self.assertEqual(panel.notification_history(malformed), [])

    def test_popup_bounds_intersect_the_current_output_and_clear_top_bar(self):
        screen = SimpleNamespace(x=-1280, y=0, width=1280, height=720)
        shared = SimpleNamespace(x=-1280, y=0, width=3200, height=720)
        local = SimpleNamespace(x=-1280, y=32, width=1280, height=660)
        self.assertEqual(panel.popup_bounds(screen, shared), (-1280, 28, 1280, 692))
        self.assertEqual(panel.popup_bounds(screen, local), (-1280, 32, 1280, 660))

    def test_context_menu_stays_within_the_clicked_monitor(self):
        area = (-1280, 28, 1280, 692)
        self.assertEqual(panel.popup_position(area, (300, 280), (-597, 350)), (-597, 350))
        self.assertEqual(panel.popup_position(area, (300, 280), (-5, 713)), (-300, 440))
        self.assertEqual(panel.popup_position(area, (300, 280)), (-308, 28))

    def test_brightness_reads_only_machine_readable_backlight(self):
        with patch.object(panel, "command", return_value="intel,backlight,512,50%,1024\n") as run:
            self.assertEqual(panel.brightness_level(), 50)
            run.assert_called_once_with("brightnessctl", "--class=backlight", "--machine-readable", "info")
        for result in ("", None, "intel,backlight,800,125%,1024"):
            with patch.object(panel, "command", return_value=result):
                self.assertIsNone(panel.brightness_level())

    def test_bluetooth_state_distinguishes_service_adapter_and_power(self):
        for replies, expected in (
            ([None], "inactive"),
            (["active\n", None], "no-adapter"),
            (["active\n", "Controller X\n\tPowered: yes\n"], "on"),
            (["active\n", "Controller X\n\tPowered: no\n"], "off"),
        ):
            with self.subTest(expected=expected):
                with patch.object(panel, "command", side_effect=replies):
                    self.assertEqual(panel.bluetooth_state(), expected)

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

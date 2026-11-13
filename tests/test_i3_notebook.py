"""Offline checks for the i3 Notebook shell entry points and package selection."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

from test_bash_protocol import ROOT, bash_harness, function


class I3NotebookTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="DarfinOS home ")
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.bin = self.home / "bin"
        self.bin.mkdir()
        self.entry = ROOT / "themes/i3-notebook/session.sh"
        self.installed_entry = self.home / ".config/darfinos/i3-notebook/session.sh"
        self.installed_entry.parent.mkdir(parents=True)
        self.installed_entry.write_bytes(self.entry.read_bytes())
        self.stub("tail", 'exec /usr/bin/tail "$@"')
        self.stub("sh", 'exec /bin/sh "$@"')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def run_entry(self, action):
        return subprocess.run(["/bin/sh", str(self.entry), action], capture_output=True, check=True,
                              env=dict(os.environ, HOME=str(self.home), PATH=str(self.bin)), timeout=5)

    def test_rofi_launches_three_modes_and_script_supports_spaces_in_home(self):
        self.stub("rofi", "printf '%s\\n' \"$@\"")
        for command, mode in (("apps", "drun"), ("windows", "window"), ("shortcuts", "Atalhos do i3")):
            with self.subTest(mode=mode):
                args = self.run_entry(command).stdout.decode().splitlines()
                self.assertEqual(args[-2:], ["-show", mode])
                self.assertEqual(args[args.index("-theme") + 1], str(self.installed_entry.with_name("rofi.rasi")))
                _, _, script_mode = args[args.index("-modes") + 1].split(",", 2)
                label, command_line = script_mode.split(":", 1)
                self.assertEqual(label, "Atalhos do i3")
                choices = subprocess.run(shlex.split(command_line), capture_output=True, check=True,
                                         env=dict(os.environ, HOME=str(self.home), PATH=str(self.bin)), timeout=5)
                self.assertIn(b"\x00no-custom\x1ftrue\n", choices.stdout)
                self.assertIn(b"Super+Shift+N", choices.stdout)

    def test_dmenu_fallback_hides_rofi_control_record(self):
        self.stub("dmenu_run", 'echo fallback')
        self.stub("dmenu", '/usr/bin/cat > "$HOME/menu"')
        self.assertEqual(self.run_entry("apps").stdout.strip(), b"fallback")
        self.run_entry("shortcuts")
        choices = (self.home / "menu").read_bytes()
        self.assertNotIn(b"\x00", choices)
        self.assertIn(b"Super+Shift+N", choices)

    def test_volume_uses_existing_audio_stack(self):
        self.stub("wpctl", 'printf "%s\\n" "$*"')
        self.stub("pactl", 'printf "%s\\n" "$*"')
        self.assertEqual(self.run_entry("volume-up").stdout.strip(),
                         b"set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+")
        self.stub("wpctl", "exit 1")
        self.assertEqual(self.run_entry("mic-mute").stdout.strip(),
                         b"set-source-mute @DEFAULT_SOURCE@ toggle")

    def test_installer_only_installs_packages_after_confirmation(self):
        setup = """
info() { :; }
install_pkgs() { darfinos_event "PKG:pacman:$*"; }
lab_confirm() { [[ "$1" == i3_notebook && "$approved" == 1 ]]; }
approved=0
step_lab_i3_notebook && exit 1
approved=1
step_lab_i3_notebook
"""
        result, events = bash_harness(function("step_lab_i3_notebook") + setup)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(events), 1)
        packages = set(events[0].split(":", 2)[2].split())
        self.assertTrue({"i3-wm", "rofi", "dunst", "i3status-rust", "brightnessctl",
                         "xss-lock", "flameshot", "xterm", "chezmoi", "libnotify"} <= packages)
        self.assertFalse({"wireplumber", "pipewire", "picom", "sonicde"} & packages)

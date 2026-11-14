"""Offline checks for the i3 Notebook shell entry points and package selection."""
import hashlib
import io
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
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
                for shortcut in (b"Super+Enter", b"Super+B ", b"Super+E ", b"Super+Shift+B", b"Super+Shift+N"):
                    self.assertIn(shortcut, choices.stdout)

    def test_dmenu_fallback_hides_rofi_control_record(self):
        self.stub("dmenu_run", 'echo fallback')
        self.stub("dmenu", '/usr/bin/cat > "$HOME/menu"')
        self.assertEqual(self.run_entry("apps").stdout.strip(), b"fallback")
        self.run_entry("shortcuts")
        choices = (self.home / "menu").read_bytes()
        self.assertNotIn(b"\x00", choices)
        self.assertIn(b"Super+Shift+N", choices)

    def test_browser_launches_desktop_default_without_url_or_extra_args(self):
        self.stub("xdg-settings", '[ "$*" = "get default-web-browser" ] && echo custom-browser.desktop')
        self.stub("xdg-mime", 'echo wrong-browser.desktop')
        self.stub("gtk-launch", 'printf "<%s>\\n" "$@"')
        self.assertEqual(self.run_entry("browser").stdout.splitlines(), [b"<-->", b"<custom-browser.desktop>"])

    def test_browser_falls_back_to_https_association(self):
        self.stub("xdg-settings", 'exit 4')
        self.stub("xdg-mime", '[ "$*" = "query default x-scheme-handler/https" ] && echo https.desktop')
        self.stub("gtk-launch", 'printf "<%s>\\n" "$@"')
        self.assertEqual(self.run_entry("browser").stdout.splitlines(), [b"<-->", b"<https.desktop>"])

    def test_file_manager_passes_home_as_one_arg(self):
        self.stub("xdg-mime", '[ "$*" = "query default inode/directory" ] && echo custom-files.desktop')
        self.stub("gtk-launch", 'printf "<%s>\\n" "$@"')
        self.assertEqual(self.run_entry("files").stdout.decode().splitlines(),
                         ["<-->", "<custom-files.desktop>", f"<{self.home}>"])

    def test_missing_or_invalid_browser_shows_notice_instead_of_running_it(self):
        self.stub("xdg-settings", 'printf "%s\\n" --invalid.desktop')
        self.stub("gtk-launch", 'echo unexpected; exit 0')
        self.stub("notify-send", 'printf "%s\\n" "$@"')
        output = self.run_entry("browser").stdout.decode()
        self.assertIn("Defina um navegador padrão", output)
        self.assertNotIn("unexpected", output)

    def test_volume_uses_existing_audio_stack(self):
        self.stub("wpctl", 'printf "%s\\n" "$*"')
        self.stub("pactl", 'printf "%s\\n" "$*"')
        self.assertEqual(self.run_entry("volume-up").stdout.strip(),
                         b"set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+")
        self.stub("wpctl", "exit 1")
        self.assertEqual(self.run_entry("mic-mute").stdout.strip(),
                         b"set-source-mute @DEFAULT_SOURCE@ toggle")

    def test_network_reports_status_and_uses_the_existing_networkmanager(self):
        self.stub("nmcli", """
case "$*" in
    '-t -f RUNNING general') echo running ;;
    '-t -f TYPE,STATE device status') echo wifi:connected ;;
esac
""")
        self.stub("grep", 'exec /usr/bin/grep "$@"')
        self.stub("timeout", 'exec /usr/bin/timeout "$@"')
        self.stub("xterm", 'printf "<%s>\n" "$@"')
        self.assertIn("Wi-Fi", self.run_entry("network-status").stdout.decode())
        args = self.run_entry("network-terminal").stdout.decode().splitlines()
        self.assertIn("<JetBrainsMono Nerd Font Mono>", args)
        self.assertEqual(args[-2:], ["<-e>", "<nmtui>"])
        self.stub("nmcli", "exit 1")
        self.assertIn("NetworkManager não está ativo", self.run_entry("network-terminal").stderr.decode())

    def test_fastfetch_targets_the_profile_preset_and_logo(self):
        self.stub("fastfetch", 'printf "<%s>\n" "$@"')
        profile = self.installed_entry.parent
        self.assertEqual(self.run_entry("fastfetch").stdout.decode().splitlines(),
                         ["<--config>", f"<{profile / 'fastfetch.jsonc'}>",
                          "<--logo>", f"<{profile / 'logo.png'}>", "<--logo-type>", "<chafa>"])

    def test_power_dispatch_accepts_only_named_actions(self):
        self.stub("systemctl", 'printf "%s\n" "$@"')
        self.stub("i3-msg", 'printf "%s\n" "$@"')
        for action, expected in (("poweroff", b"poweroff"), ("reboot", b"reboot"), ("logout", b"exit")):
            with self.subTest(action=action):
                run = subprocess.run(["/bin/sh", str(self.entry), "power-action", action],
                                     capture_output=True, env=dict(os.environ, HOME=str(self.home), PATH=str(self.bin)))
                self.assertEqual((run.returncode, run.stdout.strip()), (0, expected))
        run = subprocess.run(["/bin/sh", str(self.entry), "power-action", "--force"],
                             capture_output=True, env=dict(os.environ, HOME=str(self.home), PATH=str(self.bin)))
        self.assertEqual((run.returncode, run.stdout), (2, b""))

    def test_bar_toggle_only_targets_the_notebook_dock_on_current_display(self):
        self.stub("head", 'exec /usr/bin/head "$@"')
        self.stub("xdotool", """
case "$1" in
    search) [ "$3" = '^darfinos-notebook-bar$' ] && printf '99\\n100\\n' ;;
    getwindowpid) [ "$2" = 99 ] && echo 412 ;;
esac
""")
        self.stub("polybar-msg", 'printf "%s\\n" "$*"')
        self.assertEqual(self.run_entry("bar-toggle").stdout.strip(), b"-p 412 cmd toggle")

    def test_missing_polybar_uses_i3bar_without_global_commands(self):
        self.stub("i3-msg", 'printf "%s\\n" "$*"')
        self.assertEqual(self.run_entry("bar-start").stdout.strip(), b"bar mode dock notebook")
        self.assertEqual(self.run_entry("bar-toggle").stdout.strip(), b"bar mode toggle notebook")

    def test_installer_only_installs_packages_after_confirmation(self):
        setup = """
info() { :; }
notebook_install_cursor() { [[ "$approved" == 1 ]]; }
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
                         "xss-lock", "flameshot", "xterm", "chezmoi", "libnotify", "feh",
                         "zenity", "xorg-xrandr", "xorg-xrdb", "xorg-xsetroot", "xsettingsd", "polybar",
                         "ttf-jetbrains-mono-nerd", "xdotool", "powerline-fonts", "librsvg",
                         "xdg-utils", "gtk3", "python-gobject", "pavucontrol", "network-manager-applet", "python-xlib", "arandr", "lxappearance",
                         "bluez-utils", "blueman", "polkit-gnome", "fastfetch", "chafa", "playerctl", "thunar", "gvfs", "adwaita-icon-theme", "kvantum", "kvantum-qt5",
                         "curl", "tar", "xz"} <= packages)
        self.assertFalse({"wireplumber", "pipewire", "picom", "sonicde"} & packages)


class NotebookCursorInstallerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="DarfinOS cursor ")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.archive = self.root / "fixture.tar.xz"
        self.dest = self.root / "data/icons/Bibata-Modern-Ice"
        self.make_archive()

    def make_archive(self, escape=False, wrong_root=False):
        with tarfile.open(self.archive, "w:xz") as archive:
            prefix = "unexpected" if wrong_root else "Bibata-Modern-Ice"
            for name, content in (("index.theme", b"[Icon Theme]\nName=Bibata Modern Ice\n"),
                                  ("cursors/left_ptr", b"fixture cursor")):
                member = tarfile.TarInfo(f"{prefix}/{name}")
                member.size = len(content)
                member.mode = 0o644
                archive.addfile(member, io.BytesIO(content))
            alias = tarfile.TarInfo(f"{prefix}/cursors/arrow")
            alias.type = tarfile.SYMTYPE
            alias.linkname = "/etc/passwd" if escape else "left_ptr"
            archive.addfile(alias)

    def run_installer(self, code, checksum=None):
        checksum = checksum or hashlib.sha256(self.archive.read_bytes()).hexdigest()
        setup = f"""
XDG_DATA_HOME={shlex.quote(str(self.root / 'data'))}
TMP_DIR={shlex.quote(str(self.root / 'tmp'))}
fixture={shlex.quote(str(self.archive))}
BIBATA_VERSION=v2.0.7
BIBATA_SHA256={checksum}
mkdir -p "$TMP_DIR"
info() {{ :; }}
warn() {{ :; }}
curl() {{
  printf '%s\\n' "$*" >> "$TMP_DIR/downloads"
  while [[ "$1" != -o ]]; do shift; done
  cp -- "$fixture" "$2"
}}
"""
        return bash_harness(function("notebook_cursor_ready") + "\n" +
                            function("notebook_install_cursor") + setup + code)

    def test_installs_checked_archive_in_xdg_path_and_preserves_existing(self):
        result, _ = self.run_installer(r'''
notebook_install_cursor
notebook_cursor_ready || exit 61
[[ "$(cat "$XDG_DATA_HOME/icons/Bibata-Modern-Ice/cursors/left_ptr")" == 'fixture cursor' ]] || exit 62
[[ "$(readlink "$XDG_DATA_HOME/icons/Bibata-Modern-Ice/cursors/arrow")" == left_ptr ]] || exit 63
printf 'user cursor' > "$XDG_DATA_HOME/icons/Bibata-Modern-Ice/cursors/left_ptr"
notebook_install_cursor
[[ "$(cat "$XDG_DATA_HOME/icons/Bibata-Modern-Ice/cursors/left_ptr")" == 'user cursor' ]] || exit 64
[[ "$(wc -l < "$TMP_DIR/downloads")" == 1 ]] || exit 65
grep -Fq 'https://github.com/ful1e5/Bibata_Cursor/releases/download/v2.0.7/Bibata-Modern-Ice.tar.xz' "$TMP_DIR/downloads"
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list((self.root / "data/icons").glob(".bibata-stage.*")), [])

    def test_incomplete_existing_theme_is_preserved_without_download(self):
        self.dest.mkdir(parents=True)
        marker = self.dest / "my-custom-file"
        marker.write_text("keep me")
        result, _ = self.run_installer(r'''
notebook_cursor_ready && exit 61
notebook_install_cursor && exit 62
[[ ! -e "$TMP_DIR/downloads" ]]
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(marker.read_text(), "keep me")

    def test_bad_checksum_never_publishes_theme(self):
        result, _ = self.run_installer("notebook_install_cursor && exit 61\ntrue", checksum="0" * 64)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.dest.exists())

    def test_unexpected_root_or_escaping_alias_never_publishes_theme(self):
        for fixture in ("escape", "wrong_root"):
            with self.subTest(fixture=fixture):
                self.make_archive(**{fixture: True})
                result, _ = self.run_installer("notebook_install_cursor && exit 61\ntrue")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(self.dest.exists())

    def test_module_probe_reports_missing_cursor_as_partial_and_ready_as_installed(self):
        code = r'''
MODULE_PACMAN_AVAILABLE=1
module_packages_ready() { return 0; }
module_probe lab_i3_notebook
[[ "$MODULE_STATUS" == partial ]] || exit 61
mkdir -p "$XDG_DATA_HOME/icons/Bibata-Modern-Ice/cursors"
touch "$XDG_DATA_HOME/icons/Bibata-Modern-Ice/index.theme" "$XDG_DATA_HOME/icons/Bibata-Modern-Ice/cursors/left_ptr"
module_probe lab_i3_notebook
[[ "$MODULE_STATUS" == installed ]]
'''
        result, _ = self.run_installer(function("module_probe") + code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

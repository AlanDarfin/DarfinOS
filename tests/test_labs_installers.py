"""Test Labs installers with offline doubles and temporary user files."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_bash_protocol import bash_harness, function, ROOT


def run_functions(names, code, stdin=''):
    return bash_harness('\n'.join(function(name) for name in names) + '\n' + code, stdin=stdin)


class LabsInstallers(unittest.TestCase):
    def test_advanced_steps_reject_unattended_installation_before_sudo(self):
        installer = ROOT / 'DarfinOSInstallScript.sh'
        for step in ('lab_trinity', 'lab_booster', 'lab_xomposite', 'i3,lab_chicago95'):
            result = subprocess.run(['bash', installer, '--only', step, '-y'],
                                    text=True, capture_output=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Labs não permite -y', result.stdout + result.stderr)
            self.assertNotIn('Autenticando sudo', result.stdout + result.stderr)

    def test_trinity_uses_candidate_and_only_persists_after_success(self):
        code = r'''
HOME=$(mktemp -d)
trap 'rm -rf "$HOME"' EXIT
TMP_DIR="$HOME"
conf="$HOME/pacman.conf"
printf '[options]\n' > "$conf"
TRINITY_SERVER='https://mirror.ppa.trinitydesktop.org/trinity/archlinux/$arch'
TRINITY_FINGERPRINT=verified
lab_confirm() { return 0; }
info() { :; }; ok() { :; }; warn() { :; }
pacman-conf() {
  if [[ "$1" == --repo-list ]]; then
    grep -q '^\[trinity\]$' "$conf" && echo trinity
    return 0
  fi
  [[ "$1" == --config && "$2" == "$TMP_DIR/trinity-pacman.conf" ]] || return 60
  grep -q '^SigLevel = PackageRequired PackageTrustedOnly DatabaseOptional DatabaseTrustedOnly$' "$2"
}
trinity_key() { :; }
trinity_repo_valid() { grep -q '^\[trinity\]$' "$conf"; }
trinity_session_ready() { :; }
pacman() { [[ "$*" == '-Qq tde-meta tde-tdebase' ]]; }
sudo() {
  if [[ "$1" == pacman ]]; then
    [[ "$*" == "pacman --config $TMP_DIR/trinity-pacman.conf -Syu --needed trinity/tde-meta" ]] || return 61
    ! grep -q '^\[trinity\]$' "$conf" || return 62
    [[ "$install_succeeds" == 1 ]]
  else
    "$@"
  fi
}
install_succeeds=0
trinity_install "$conf" && exit 63
! grep -q '^\[trinity\]$' "$conf" || exit 64
[[ ! -e "$conf.darfinos-trinity.bak" ]] || exit 65
install_succeeds=1
trinity_install "$conf"
[[ "$(grep -Fc '[trinity]' "$conf")" == 1 ]] || exit 66
[[ "$(cat "$conf.darfinos-trinity.bak")" == '[options]' ]]
'''
        result, events = run_functions(('trinity_repo_stanza', 'trinity_install'), code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(events, ['PKG:pacman:tde-meta'] * 2)

    def test_trinity_rejects_a_bad_existing_repository_without_touching_it(self):
        code = r'''
TRINITY_SERVER=expected; TRINITY_FINGERPRINT=expected; TMP_DIR=/nonexistent
pacman-conf() { printf 'core\ntrinity\n'; }
lab_confirm() { :; }; info() { :; }; warn() { :; }
trinity_repo_valid() { return 1; }
trinity_key() { exit 60; }; sudo() { exit 61; }
trinity_install /nonexistent/pacman.conf
'''
        result, events = run_functions(('trinity_install',), code)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(events, [])

    def test_trinity_signing_key_requires_exact_primary_fingerprint(self):
        code = r'''
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
TRINITY_FINGERPRINT=D6D6FAA25E9A3E4ECD9FBDBEC93AF1698685AD8B
warn() { :; }
curl() { :; }
gpg() {
  printf 'pub:::::::::\nfpr:::::::::%s:\n' "$provided"
  if [[ "${extra:-}" == 1 ]]; then printf 'pub:::::::::\nfpr:::::::::EXTRA:\n'; fi
  return 0
}
sudo() {
  printf '%s\n' "$*" >> "$TMP_DIR/calls"
  [[ "$2" != --list-keys ]]
}
provided=000000000000000000000000C93AF1698685AD8B
trinity_key && exit 60
provided=$TRINITY_FINGERPRINT
extra=1
trinity_key && exit 61
! grep -q -- '--add' "$TMP_DIR/calls" || exit 62
extra=0
trinity_key
grep -Fqx "pacman-key --lsign-key $TRINITY_FINGERPRINT" "$TMP_DIR/calls"
'''
        result, _ = run_functions(('trinity_key',), code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_download_checks_checksum_and_never_overwrites(self):
        code = r'''
HOME=$(mktemp -d)
trap 'rm -rf "$HOME"' EXIT
TMP_DIR="$HOME"
info() { :; }; warn() { :; }
curl() {
  while [[ "$1" != -o ]]; do shift; done
  printf 'trusted file\n' > "$2"
}
expected=$(printf 'trusted file\n' | sha256sum)
lab_download_binary example https://example.invalid/file 000000 && exit 61
[[ ! -e "$HOME/.local/bin/example" ]] || exit 62
lab_download_binary example https://example.invalid/file "${expected%% *}"
[[ -x "$HOME/.local/bin/example" ]] || exit 63
[[ "$(cat "$HOME/.local/bin/example")" == 'trusted file' ]] || exit 64
printf 'different\n' > "$TMP_DIR/replacement"
lab_publish_binary "$TMP_DIR/replacement" example && exit 65
[[ "$(cat "$HOME/.local/bin/example")" == 'trusted file' ]]
'''
        result, _ = run_functions(('lab_publish_binary', 'lab_download_binary'), code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_chicago_accepts_relative_links_but_rejects_escape(self):
        code = r'''
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
info() { :; }; warn() { :; }
mkdir "$work/theme"
touch "$work/theme/index.theme" "$work/outside"
ln -s index.theme "$work/theme/icon"
chicago95_copy_component "$work/theme" "$work/installed" index.theme
[[ -L "$work/installed/icon" && -f "$work/installed/icon" ]] || exit 61
ln -s ../outside "$work/theme/escape"
chicago95_copy_component "$work/theme" "$work/rejected" index.theme && exit 62
[[ ! -e "$work/rejected" ]] || exit 63
rm "$work/theme/escape"
ln -s "$work/theme/index.theme" "$work/theme/absolute"
chicago95_links_safe "$work/theme" && exit 64
true
'''
        result, _ = run_functions(('chicago95_links_safe', 'chicago95_copy_component'), code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_junest_detects_package_without_rootfs_as_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            bindir = home / 'bin'
            bindir.mkdir()
            pacman = bindir / 'pacman'
            pacman.write_text('#!/bin/sh\nprintf "junest-git\\n"\n')
            pacman.chmod(0o755)
            env = {**os.environ, 'HOME': tmp, 'JUNEST_HOME': str(home / 'test-root'),
                   'PATH': str(bindir) + ':' + os.environ['PATH']}
            command = ['bash', ROOT / 'DarfinOSInstallScript.sh', '--check-modules']
            before = subprocess.check_output(command, text=True, env=env, timeout=5)
            self.assertIn('lab_junest\tpartial\t', before)
            inner = home / 'test-root/usr/bin/pacman'
            inner.parent.mkdir(parents=True)
            inner.touch(mode=0o755)
            metadata = home / 'test-root/etc/junest/info'
            metadata.parent.mkdir(parents=True)
            metadata.touch()
            after = subprocess.check_output(command, text=True, env=env, timeout=5)
            self.assertIn('lab_junest\tinstalled\t', after)

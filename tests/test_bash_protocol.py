"""Testes reais das funções Bash isoladas: sem root, rede, pacman ou serviços."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'DarfinOSInstallScript.sh').read_text()

def function(name):
    match = re.search(r'^' + re.escape(name) + r'\(\)\s*\{', SOURCE, re.M)
    if not match:
        raise AssertionError(f'Função ausente: {name}')
    # All targeted functions are self-contained, with no nested literal braces.
    depth = 1
    pos = match.end()
    while depth and pos < len(SOURCE):
        if SOURCE[pos] == '{': depth += 1
        elif SOURCE[pos] == '}': depth -= 1
        pos += 1
    if depth:
        raise AssertionError('Função sem fechamento')
    return SOURCE[match.start():pos]

def bash_harness(commands, *, stdin=''):
    # Capture events on FD 3 without executing the original top-level installer.
    script = 'set -euo pipefail\n' + '\n'.join(function(n) for n in ('darfinos_event', 'run_step', 'confirm', 'choose'))
    script += '\n' + commands + '\n'
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'harness.sh'
        events = Path(tmp) / 'events.txt'
        path.write_text(script)
        # fd 3 is opened by bash, not inherited from the test runner.
        result = subprocess.run(['bash', '-c', 'exec 3>"$1"; export DARFINOS_EVENT_FD=3; bash "$2"', '_', str(events), str(path)],
                                input=stdin, capture_output=True, text=True, timeout=5)
        return result, events.read_text().splitlines()

class BashProtocolTests(unittest.TestCase):
    def test_installer_requires_explicit_selection_before_sudo(self):
        run = subprocess.run(['bash', str(ROOT / 'DarfinOSInstallScript.sh')],
                             capture_output=True, text=True, timeout=5)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn('Nenhuma seleção informada', run.stdout + run.stderr)
        self.assertIn('--all', run.stdout)
        self.assertNotIn('Autenticando sudo', run.stdout)

    def test_invalid_or_conflicting_step_selections_fail_early(self):
        for args in (['--only', ','], ['--only', 'base,'],
                     ['--only', 'base,,fonts'], ['--only', 'nonexistent'],
                     ['--only', 'base', '--skip', 'fonts'],
                     ['--only', 'base', '--all']):
            with self.subTest(args=args):
                result = subprocess.run(['bash', str(ROOT / 'DarfinOSInstallScript.sh'), *args],
                                        capture_output=True, text=True, timeout=5)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('Autenticando sudo', result.stdout)

    def test_labs_catalog_does_not_ask_for_sudo_or_start_installing(self):
        for args in (['--labs'], ['--lab-info', 'yserver'], ['--lab-info', 'i3']):
            with self.subTest(args=args):
                res = subprocess.run(['bash', str(ROOT / 'DarfinOSInstallScript.sh'), *args],
                                     capture_output=True, text=True, timeout=5)
                self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
                self.assertIn('https://', res.stdout)
                self.assertNotIn('Autenticando sudo', res.stdout)

    def test_labs_install_stays_off_on_full_and_skip(self):
        codes = function('step_enabled') + '''
ONLY=""
SKIP=""
step_enabled lab_nscde && exit 13
step_enabled i3 || exit 14
ONLY="lab_nscde"
step_enabled lab_nscde || exit 15
'''
        result, _ = bash_harness(codes)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_lab_confirmation_is_explicit_and_tui_compatible(self):
        code = function('lab_aur_install') + """
ASSUME_YES=0
declare -A LABS_URL=([nscde]="https://github.com/NsCDE/NsCDE")
info() { :; }
warn() { :; }
ok() { :; }
detect_aur_helper() { echo yay; }
LAB_INSTALLED=0
pacman() { [[ "$LAB_INSTALLED" == 1 ]]; }
aur_install() { LAB_INSTALLED=1; }
lab_aur_install nscde nscde
"""
        result, events = bash_harness(code, stdin='LABS\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events, [
            'PROMPT_CHOOSE:n:labs/n:Digite LABS para abrir a transação de nscde'
        ])
        result, events = bash_harness(code, stdin='\n')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(events), 1)

    def test_labs_refuse_yes_even_when_explicitly_selected(self):
        code = function('lab_aur_install') + """
ASSUME_YES=1
warn() { :; }
lab_aur_install nscde nscde
"""
        result, events = bash_harness(code)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(events, [])

    def test_modules_checker_is_read_only(self):
        result = subprocess.run(['bash', str(ROOT / 'DarfinOSInstallScript.sh'),
                                 '--check-modules'], capture_output=True, text=True, check=True)
        rows = result.stdout.splitlines()
        self.assertEqual(rows[0], 'module\tstatus\treason')
        self.assertEqual(len(rows), 42)
        self.assertTrue(any(x.startswith('lab_chicago95\t') for x in rows))
        self.assertNotIn('Autenticando sudo', result.stdout)

    def test_modular_probe_reads_complete_partial_and_chicago_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            bin_dir = Path(tmp) / "bin"
            home.mkdir()
            bin_dir.mkdir()
            packages = ["i3-wm", "i3status", "i3lock", "dmenu", "xorg-xinit", "xfce4-session"]
            pacman = bin_dir / "pacman"
            pacman.write_text("#!/bin/sh\nif [ \"$1\" = \"-Qq\" ]; then\n" +
                              "printf '%s\\n' " + " ".join(packages) + "\nfi\n")
            pacman.chmod(0o755)
            env = dict(os.environ, HOME=str(home), PATH=str(bin_dir) + ":" + os.environ["PATH"])
            cmd = ['bash', str(ROOT / 'DarfinOSInstallScript.sh'), '--check-modules']
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            rows = {parts[0]: parts[1:] for line in result.stdout.splitlines()[1:]
                    if len(parts := line.split("\t", 2)) == 3}
            self.assertEqual(rows['i3'][0], 'installed')
            self.assertEqual(rows['xfce'][0], 'partial')
            self.assertEqual(rows['lab_chicago95'][0], 'missing')
            for directory in ('.themes/Chicago95', '.icons/Chicago95'):
                target = home / directory
                target.mkdir(parents=True)
                (target / 'index.theme').write_text('[Icon Theme]\\n')
            css = home / '.themes/Chicago95/gtk-3.0/gtk.css'
            css.parent.mkdir(parents=True)
            css.write_text('/* Chicago95 */')
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            rows = {parts[0]: parts[1:] for line in result.stdout.splitlines()[1:]
                    if len(parts := line.split("\t", 2)) == 3}
            self.assertEqual(rows['lab_chicago95'][0], 'installed')

    def test_skip_verified_module_before_installing(self):
        codes = '''
STEPS=(i3)
declare -A STEP_DESC=([i3]="i3")
declare -A STEP_DEPS=()
FAILED_STEPS=(); SKIPPED_STEPS=()
step_enabled() { return 0; }
modules_refresh() { :; }
module_probe() { MODULE_STATUS=installed; MODULE_REASON="pacotes presentes"; }
info() { :; }; warn() { :; }
step_i3() { exit 11; }
run_step i3
'''
        result, events = bash_harness(codes)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(events, ['STEP_ALREADY:i3'])

    def test_force_reinstall_executes_step(self):
        codes = '''
STEPS=(i3)
declare -A STEP_DESC=([i3]="i3")
declare -A STEP_DEPS=()
FAILED_STEPS=(); SKIPPED_STEPS=()
FORCE_MODULES=1
step_enabled() { return 0; }
info() { :; }; warn() { :; }
step_i3() { :; }
run_step i3
'''
        result, events = bash_harness(codes)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(events, ['STEP_START:i3', 'STEP_DONE:i3'])

    def test_event_success_failure_skip_and_dependency(self):
        result, events = bash_harness('''
STEPS=(ok bad dependent disabled)
declare -A STEP_DESC=([ok]="OK" [bad]="Bad" [dependent]="Dependent")
declare -A STEP_DEPS=([dependent]="bad")
FAILED_STEPS=(); SKIPPED_STEPS=()
step_enabled() { [[ "$1" != disabled ]]; }
modules_refresh() { :; }; module_probe() { MODULE_STATUS=unknown; }
info() { :; }; warn() { :; }
step_ok() { :; }; step_bad() { return 7; }; step_dependent() { :; }
run_step ok
run_step bad
run_step dependent
run_step disabled
printf 'failed=%s skipped=%s\\n' "${FAILED_STEPS[*]}" "${SKIPPED_STEPS[*]}"
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events, ['STEP_START:ok', 'STEP_DONE:ok', 'STEP_START:bad',
                                  'STEP_FAIL:bad:7', 'STEP_SKIP:dependent:dependencia:bad',
                                  'STEP_SKIP:disabled:desmarcada'])
        self.assertIn('failed=bad skipped=dependent', result.stdout)

    def test_maintenance_fails_when_required_updaters_missing(self):
        # Substitui somente funções de instalação e descoberta, sem invocar sudo.
        code = function('step_maintenance') + '''
info() { :; }
warn() { :; }
detect_aur_helper() { echo ""; }
command() {
  if [[ "$1" == "-v" ]]; then
    case "$2" in
      topgrade|arch-update|arch-update-tray|systemctl|paccache) return 1 ;;
    esac
  fi
  builtin command "$@"
}
step_maintenance
'''
        result, _ = bash_harness(code)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_maintenance_succeeds_with_updaters_present(self):
        code = function('step_maintenance') + '''
info() { :; }
ok() { :; }
warn() { :; }
detect_aur_helper() { echo "yay"; }
topgrade() { :; }
arch-update() { :; }
arch-update-tray() { :; }
sudo() { :; }
step_maintenance
'''
        result, _ = bash_harness(code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_confirm_and_choose_events(self):
        result, events = bash_harness('''
ASSUME_YES=0
confirm 'Prosseguir?' n
choose 'Canal?' 'stable/beta' 'stable'
''', stdin='s\nbeta\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events, ['PROMPT_CONFIRM:n:Prosseguir?',
                                  'PROMPT_CHOOSE:stable:stable/beta:Canal?'])
        self.assertIn('beta', result.stdout)

    def test_no_event_fd_keeps_original_behavior(self):
        result, events = bash_harness('''
unset DARFINOS_EVENT_FD
ASSUME_YES=0
confirm 'Prosseguir?' s
''', stdin='\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events, [])

    def test_yes_does_not_emit_prompt(self):
        result, events = bash_harness('''
ASSUME_YES=1
confirm 'Prosseguir?' s
choose 'Canal?' 'stable/beta' 'stable'
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events, [])

if __name__ == '__main__':
    unittest.main()

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
    def test_event_success_failure_skip_and_dependency(self):
        result, events = bash_harness('''
STEPS=(ok bad dependent disabled)
declare -A STEP_DESC=([ok]="OK" [bad]="Bad" [dependent]="Dependent")
declare -A STEP_DEPS=([dependent]="bad")
FAILED_STEPS=(); SKIPPED_STEPS=()
step_enabled() { [[ "$1" != disabled ]]; }
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

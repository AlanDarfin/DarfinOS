"""Testes offline do frontend, sem curses interativo nem instalação real."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('darfinos_tui', ROOT / 'DarfinOSInstallScript-TUI.py')
TUI = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = TUI
SPEC.loader.exec_module(TUI)
BASH = ROOT / 'DarfinOSInstallScript.sh'

class ParserTests(unittest.TestCase):
    def test_34_steps_and_unique_names(self):
        steps = TUI.parse_script(BASH)
        self.assertEqual(len(steps), 34)
        self.assertEqual(len({s.name for s in steps}), 34)
        self.assertEqual(steps[0].name, 'pacman_conf')
        self.assertEqual(steps[-1].name, 'terminal_extras')

    def test_search_tolerates_typo_and_respects_selected(self):
        st = TUI.State(TUI.parse_script(BASH), 'test', selected={'gaming'})
        st.search = 'gamng'
        self.assertIn('gaming', [st.steps[i].name for i in st.filtered()])
        st.show_selected = True
        self.assertEqual([st.steps[i].name for i in st.filtered()], ['gaming'])

    def test_doctor_is_read_only_and_checks_all_functions(self):
        report = TUI.diagnose_script(BASH)
        self.assertEqual(report['steps'], 34)
        self.assertTrue(report['ready'], report['errors'])
        self.assertEqual(report['errors'], [])

    def test_doctor_detects_invalid_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'invalid.sh'
            path.write_text(BASH.read_text().replace('[apps]="flatpak"', '[apps]="missing_step"'))
            report = TUI.diagnose_script(path)
            self.assertFalse(report['ready'])
            self.assertTrue(any('missing_step' in msg for msg in report['errors']))

    def test_known_dependencies(self):
        lookup = {s.name: s for s in TUI.parse_script(BASH)}
        self.assertIn('flatpak', lookup['apps'].deps)
        self.assertIn('hardware', lookup['gaming'].deps)

    def test_bad_script_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'invalid.sh'
            path.write_text('#!/bin/bash\necho hello\n')
            with self.assertRaises(ValueError):
                TUI.parse_script(path)

    def test_dependency_expansion_and_command(self):
        steps = TUI.parse_script(BASH)
        st = TUI.State(steps, 'test', selected={'apps'})
        self.assertEqual(st.missing(), {'apps': ['flatpak']})
        st.add_deps()
        self.assertEqual(st.selected, {'apps', 'flatpak'})
        cmd = TUI.command(BASH, st)
        self.assertEqual(cmd[:3], ['bash', str(BASH), '--only'])
        self.assertEqual(cmd[3], 'flatpak,apps')
        st.yes = True
        self.assertEqual(TUI.command(BASH, st)[-1], '-y')

    def test_no_empty_execution(self):
        st = TUI.State(TUI.parse_script(BASH), 'test')
        with self.assertRaises(ValueError):
            TUI.command(BASH, st)

    def test_inventory_is_partial_and_readonly(self):
        result = TUI.inventory(BASH, {'base'})
        self.assertTrue(any(step == 'base' and kind == 'pacman' and pkg == 'git'
                            for step, kind, pkg in result))

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.steps = TUI.parse_script(BASH)
        self.st = TUI.State(self.steps, 'test')
        self.patch = mock.patch.object(TUI, 'RUN_DIR', self.folder / 'runs')
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_journal_transitions_and_final_state(self):
        journal, data = TUI.prepare_run(BASH, ['flatpak', 'apps'], self.folder / 'run.log')
        self.assertEqual(journal.stat().st_mode & 0o777, 0o600)
        self.assertEqual(data['statuses'], {'flatpak': 'PEND', 'apps': 'PEND'})
        TUI.update_run(journal, data, 'STEP_START:flatpak')
        TUI.update_run(journal, data, 'STEP_DONE:flatpak')
        TUI.update_run(journal, data, 'STEP_START:apps')
        TUI.update_run(journal, data, 'STEP_FAIL:apps:17')
        TUI.update_run(journal, data, code=0)  # Bash may return 0 despite failed steps
        stored = json.loads(journal.read_text())
        self.assertEqual(stored['state'], 'INCOMPLETE')
        self.assertEqual(stored['statuses']['apps'], 'FAIL')
        self.assertEqual(stored['exit_code'], 0)
        self.assertEqual(len(stored['events']), 4)

    def test_successful_journal(self):
        path, data = TUI.prepare_run(BASH, ['base'], self.folder / 'run.log')
        TUI.update_run(path, data, 'STEP_DONE:base', code=0)
        self.assertEqual(json.loads(path.read_text())['state'], 'DONE')

    def test_unknown_event_ignored(self):
        path, data = TUI.prepare_run(BASH, ['base'], self.folder / 'run.log')
        TUI.update_run(path, data, 'STEP_DONE:other')
        TUI.update_run(path, data, 'PROMPT_CONFIRM:n:hello')
        self.assertEqual(data['statuses']['base'], 'PEND')
        self.assertEqual(data['events'], [])

    def test_resume_only_incomplete_and_skip_done_dependencies(self):
        record = {'script_sha256': TUI.sha(BASH),
                  'selected': ['flatpak', 'apps'],
                  'statuses': {'flatpak': 'DONE', 'apps': 'FAIL'}}
        selected, _ = TUI.recovery_selection(self.st, BASH, record)
        self.assertEqual(selected, {'apps'})

    def test_resume_includes_unfinished_dependencies(self):
        record = {'script_sha256': TUI.sha(BASH),
                  'selected': ['flatpak', 'apps'],
                  'statuses': {'flatpak': 'FAIL', 'apps': 'SKIP'}}
        selected, _ = TUI.recovery_selection(self.st, BASH, record)
        self.assertEqual(selected, {'flatpak', 'apps'})

    def test_resume_warns_uncertain(self):
        record = {'script_sha256': TUI.sha(BASH),
                  'selected': ['base'], 'statuses': {'base': 'RUN'}}
        selected, warning = TUI.recovery_selection(self.st, BASH, record)
        self.assertEqual(selected, {'base'})
        self.assertIn('parcialmente', warning)

    def test_resume_rejects_changed_bash(self):
        record = {'script_sha256': 'wrong', 'selected': ['base'],
                  'statuses': {'base': 'FAIL'}}
        with self.assertRaisesRegex(ValueError, 'mudou'):
            TUI.recovery_selection(self.st, BASH, record)

    def test_resume_rejects_complete_or_unknown_steps(self):
        for record in (
            {'script_sha256': TUI.sha(BASH), 'selected': ['base'], 'statuses': {'base': 'DONE'}},
            {'script_sha256': TUI.sha(BASH), 'selected': ['missing'], 'statuses': {'missing': 'FAIL'}},
        ):
            with self.subTest(record=record), self.assertRaises(ValueError):
                TUI.recovery_selection(self.st, BASH, record)

    def test_latest_run_and_invalid_json(self):
        p, data = TUI.prepare_run(BASH, ['base'], self.folder / 'run.log')
        (TUI.RUN_DIR / 'run-zzzz.json').write_text('not-json')
        found, stored = TUI.latest_run()
        self.assertEqual(found, p)
        self.assertEqual(stored['schema'], 1)

class ProfilesTests(unittest.TestCase):
    def test_named_profiles_roundtrip_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(TUI, 'PROFILE_DIR', Path(tmp)):
            st = TUI.State(TUI.parse_script(BASH), 'test', selected={'base', 'apps'}, yes=True)
            TUI.save_named(st, 'teste')
            st.selected.clear(); st.yes = False
            TUI.load_named(st, 'teste')
            self.assertEqual(st.selected, {'base', 'apps'})
            self.assertTrue(st.yes)
            with self.assertRaises(ValueError):
                TUI.save_named(st, '../fora')

if __name__ == '__main__':
    unittest.main()

class CliTests(unittest.TestCase):
    def test_help_and_runs_are_noninteractive(self):
        import subprocess
        for option in ('--help', '--runs', '--doctor', '--doctor-json', '--plan', '--plan --preset gaming'):
            with self.subTest(option=option), tempfile.TemporaryDirectory() as tmp:
                env = os.environ.copy()
                env['HOME'] = tmp
                proc = subprocess.run([sys.executable, str(ROOT / 'DarfinOSInstallScript-TUI.py'), *option.split()],
                                      capture_output=True, text=True, env=env, timeout=10)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bash_list_does_not_require_root_or_install(self):
        import subprocess
        proc = subprocess.run(['bash', str(BASH), '--list'], capture_output=True,
                              text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len([line for line in proc.stdout.splitlines() if line.strip()]), 34)

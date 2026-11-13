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
    def test_48_steps_and_unique_names(self):
        steps = TUI.parse_script(BASH)
        self.assertEqual(len(steps), 48)
        self.assertEqual(len({s.name for s in steps}), 48)
        self.assertEqual(steps[0].name, 'pacman_conf')
        self.assertEqual(steps[-1].name, 'lab_booster')

    def test_new_retro_modules(self):
        steps = TUI.parse_script(BASH)
        self.assertIn('lab_chicago95', {step.name for step in steps})
        self.assertIn('xfce', TUI.preset_selection('retro', steps))
        self.assertIn('lab_chicago95', TUI.preset_selection('retro', steps))
        self.assertNotIn('lab_chicago95', TUI.preset_selection('full', steps))
        catalog = {project['id']: project for project in TUI.labs_catalog(BASH)}
        self.assertEqual(catalog['chicago95']['step'], 'lab_chicago95')
        self.assertEqual(catalog['chicago95']['url'], 'https://github.com/grassmunk/Chicago95')

    def test_modules_json_matches_bash_checker(self):
        report = TUI.module_checks(BASH)
        self.assertEqual(len(report), 48)
        self.assertEqual(set(report), {x.name for x in TUI.parse_script(BASH)})
        self.assertIn(report['xfce']['status'], ('installed','partial','missing','unknown'))
        import subprocess
        out = subprocess.run([sys.executable, str(ROOT / 'DarfinOSInstallScript-TUI.py'),
                             '--check-modules'], capture_output=True, text=True, check=True)
        self.assertEqual(len(json.loads(out.stdout)['modules']), 48)

    def test_force_reinstall_option(self):
        st = TUI.State(TUI.parse_script(BASH), 'test', selected={'i3'})
        st.force_modules = True
        self.assertIn('--reinstall', TUI.command(BASH, st))
        st.force_modules = False
        self.assertNotIn('--reinstall', TUI.command(BASH, st))

    def test_i3_and_labs_group_are_distinct(self):
        steps = TUI.parse_script(BASH)
        assert next(x for x in steps if x.name == 'i3').group.startswith('Window')
        assert all(x.group.startswith('DarfinOS Labs') for x in steps if x.name.startswith('lab_'))
        selection = TUI.preset_selection('full', steps)
        self.assertIn('i3', selection)
        self.assertFalse(any(x.startswith('lab_') for x in selection))
        self.assertIn('i3', TUI.preset_selection('i3', steps))
        self.assertNotIn('sonicde', TUI.preset_selection('i3', steps))

    def test_labs_catalog_links_and_modes(self):
        projects = TUI.labs_catalog(BASH)
        self.assertEqual(len(projects), 13)
        self.assertEqual(len({x['id'] for x in projects}), 13)
        by_id = {x['id']: x for x in projects}
        self.assertEqual(by_id['i3']['step'], 'i3')
        self.assertEqual(by_id['yserver']['mode'], 'aur')
        self.assertEqual(by_id['trinity']['mode'], 'repositorio')
        self.assertEqual(by_id['booster']['step'], 'lab_booster')
        self.assertEqual(by_id['xomposite']['url'], 'https://github.com/demostenex/xomposite')
        steps = {s.name for s in TUI.parse_script(BASH)}
        self.assertTrue(all(x['step'] in steps for x in projects))
        self.assertEqual(by_id['wayback']['url'], 'https://gitlab.freedesktop.org/wayback/wayback')
        self.assertTrue(all(x['url'].startswith('https://') for x in projects))

    def test_labs_cli_outputs_json_without_tty(self):
        import subprocess
        out = subprocess.run([sys.executable, str(ROOT / 'DarfinOSInstallScript-TUI.py'), '--labs'],
                             capture_output=True, text=True, check=True)
        self.assertEqual(len(json.loads(out.stdout)['projects']), 13)
        result = subprocess.run([sys.executable, str(ROOT / 'DarfinOSInstallScript-TUI.py'),
                                 '--lab-info', 'nscde'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['step'], 'lab_nscde')

    def test_search_tolerates_typo_and_respects_selected(self):
        st = TUI.State(TUI.parse_script(BASH), 'test', selected={'gaming'})
        st.search = 'gamng'
        self.assertIn('gaming', [st.steps[i].name for i in st.filtered()])
        st.show_selected = True
        self.assertEqual([st.steps[i].name for i in st.filtered()], ['gaming'])

    def test_doctor_is_read_only_and_checks_all_functions(self):
        report = TUI.diagnose_script(BASH)
        self.assertEqual(report['steps'], 48)
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
        self.assertIn('aur_helper', lookup['maintenance'].deps)

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

    def test_maintenance_updaters_in_default_presets(self):
        for preset in ('minimal', 'desktop', 'gaming', 'full'):
            with self.subTest(preset=preset):
                self.assertIn('maintenance', TUI.preset_selection(preset, TUI.parse_script(BASH)))
                self.assertIn('aur_helper', TUI.preset_selection(preset, TUI.parse_script(BASH)))
        packages = TUI.inventory(BASH, {'maintenance'})
        self.assertIn(('maintenance', 'aur', 'topgrade-bin'), packages)
        self.assertIn(('maintenance', 'aur', 'arch-update-bin'), packages)
        self.assertNotIn(('maintenance', 'aur', 'arch-update-tray'), packages)

    def test_step_details_and_package_preview(self):
        steps = TUI.parse_script(BASH)
        st = TUI.State(steps, 'test', selected={'maintenance', 'aur_helper'})
        TUI.load_package_preview(st, BASH)
        step = st.lookup['maintenance']
        self.assertIn('Topgrade', step.detail)
        self.assertIn('topgrade-bin', TUI.package_summary(st.packages['maintenance']))
        details = TUI.inspection_lines(st, step)
        self.assertTrue(any('PACOTES PREVISTOS' in item for item in details))
        self.assertFalse(any('DEPENDÊNCIAS PENDENTES' in item for item in details))
        st.selected.remove('aur_helper')
        self.assertIn('maintenance', st.missing())

    def test_show_only_missing_dependencies(self):
        st = TUI.State(TUI.parse_script(BASH), 'test', selected={'flatpak', 'apps'})
        self.assertFalse(any('DEPENDÊNCIAS PENDENTES' in line
                             for line in TUI.inspection_lines(st, st.lookup['apps'])))
        st.selected.remove('flatpak')
        self.assertTrue(any('flatpak' in line and 'DEPENDÊNCIAS PENDENTES' in line
                            for line in TUI.inspection_lines(st, st.lookup['apps'])))

    def test_profile_audit_uses_partial_inventory_without_claiming_step_complete(self):
        state = TUI.State(TUI.parse_script(BASH), 'test', selected={'base'})
        report = TUI.audit_selected(state, BASH, {'pacman': {'git'}, 'flatpak': None})
        self.assertEqual(report['accuracy'], 'partial_static')
        self.assertGreater(report['packages_previewed'], 0)
        installed = [item for item in report['steps']['base']
                     if item['name'] == 'git']
        self.assertEqual(installed[0]['status'], 'instalado')
        self.assertIn('não detectado', report['counts'])
        unknown = TUI.audit_selected(state, BASH, {'pacman': None, 'flatpak': None})
        self.assertEqual(unknown['counts']['indisponível'], unknown['packages_previewed'])

    def test_profile_audit_cli_no_tty_or_pacman_required(self):
        import subprocess
        import sys
        command = [sys.executable, str(ROOT / 'DarfinOSInstallScript-TUI.py'),
                   '--audit', '--preset', 'minimal']
        outcome = subprocess.run(command, capture_output=True, text=True, check=True)
        report = json.loads(outcome.stdout)
        self.assertEqual(report['accuracy'], 'partial_static')
        self.assertGreater(report['selected_steps'], 0)

    def test_topgrade_disabled_in_dry_run(self):
        st = TUI.State(TUI.parse_script(BASH), 'test')
        with mock.patch.object(TUI.shutil, 'which') as which:
            TUI.launch_topgrade(None, st, allow_updates=False)
            which.assert_not_called()
        self.assertIn('dry-run', st.message)


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

    def test_already_installed_is_success_and_not_retried(self):
        path, data = TUI.prepare_run(BASH, ['base', 'i3'], self.folder / 'run.log')
        TUI.update_run(path, data, 'STEP_ALREADY:base')
        TUI.update_run(path, data, 'STEP_DONE:i3', code=0)
        self.assertEqual(data['state'], 'DONE')
        self.assertEqual(data['statuses']['base'], 'ALREADY')
        record = {'script_sha256': TUI.sha(BASH), 'selected': ['base', 'i3'],
                  'statuses': {'base': 'ALREADY', 'i3': 'FAIL'}}
        retry, _ = TUI.recovery_selection(self.st, BASH, record)
        self.assertEqual(retry, {'i3'})

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
        self.assertEqual(len([line for line in proc.stdout.splitlines() if line.strip()]), 48)

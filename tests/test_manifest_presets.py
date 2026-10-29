"""Testes de manifesto e presets, sem instalação nem rede."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('darfinos_frontend_manifest', ROOT / 'DarfinOSInstallScript-TUI.py')
TUI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TUI
SPEC.loader.exec_module(TUI)
BASH = ROOT / 'DarfinOSInstallScript.sh'


class ManifestPresetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.steps = TUI.parse_script(BASH)

    def test_manifest_has_all_steps_and_sha(self):
        manifest = TUI.build_manifest(BASH)
        self.assertEqual(len(manifest['steps']), 34)
        self.assertEqual(manifest['script_sha256'], TUI.sha(BASH))
        self.assertEqual(manifest['accuracy'], 'partial_static')

    def test_manifest_packages_are_associated_with_step(self):
        manifest = TUI.build_manifest(BASH)
        base = next(step for step in manifest['steps'] if step['id'] == 'base')
        self.assertIn({'manager': 'pacman', 'name': 'git'}, base['packages'])

    def test_preset_names_and_risk(self):
        self.assertEqual(set(TUI.PRESETS), {'minimal', 'desktop', 'gaming', 'full'})
        self.assertNotIn('bedrock', TUI.preset_selection('minimal', self.steps))
        self.assertNotIn('bedrock', TUI.preset_selection('desktop', self.steps))
        self.assertNotIn('bedrock', TUI.preset_selection('gaming', self.steps))
        self.assertIn('bedrock', TUI.preset_selection('full', self.steps))

    def test_preset_preserves_dependency_metadata(self):
        st = TUI.State(self.steps, 'test', selected={'bedrock'})
        TUI.apply_preset(st, 'gaming')
        self.assertNotIn('bedrock', st.selected)
        self.assertIn('gaming', st.selected)
        self.assertFalse(st.missing(), 'Preset gaming deve incluir dependências declaradas')

    def test_unknown_preset_is_rejected(self):
        with self.assertRaises(ValueError):
            TUI.preset_selection('unknown', self.steps)

    def test_manifest_cli_no_tty_required(self):
        result = subprocess.run([sys.executable, str(ROOT / 'DarfinOSInstallScript-TUI.py'), '--manifest'],
                                capture_output=True, text=True, check=True)
        self.assertEqual(len(json.loads(result.stdout)['steps']), 34)

    def test_list_presets_cli_no_tty_required(self):
        result = subprocess.run([sys.executable, str(ROOT / 'DarfinOSInstallScript-TUI.py'), '--list-presets'],
                                capture_output=True, text=True, check=True)
        self.assertIn('gaming', result.stdout)

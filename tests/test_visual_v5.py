"""Pure, offline visual helpers: no terminal or package operations."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('darfinos_visual_test', ROOT / 'DarfinOSInstallScript-TUI.py')
TUI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TUI
SPEC.loader.exec_module(TUI)


class VisualTests(unittest.TestCase):
    def test_meter_empty(self):
        self.assertEqual(TUI.progress_meter(0, 32, 10), '░' * 10)

    def test_meter_full(self):
        self.assertEqual(TUI.progress_meter(32, 32, 10), '█' * 10)

    def test_meter_bounds(self):
        self.assertEqual(TUI.progress_meter(50, 32, 8), '█' * 8)
        self.assertEqual(TUI.progress_meter(-1, 32, 8), '░' * 8)
        self.assertEqual(TUI.progress_meter(0, 0, 0), '')

    def test_visual_status(self):
        self.assertEqual(TUI.visual_status('DONE')[1], 'green')
        self.assertEqual(TUI.visual_status('FAIL')[1], 'red')
        self.assertEqual(TUI.visual_status('RUN')[1], 'blue')
        self.assertEqual(TUI.visual_status('UNKNOWN')[0], '?')


if __name__ == '__main__':
    unittest.main()

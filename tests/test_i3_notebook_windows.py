"""Verify i3 workflow logic without an X display or active window manager."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

THEME = Path(__file__).resolve().parents[1] / "themes/i3-notebook"
sys.path.insert(0, str(THEME))
try:
    import settings
    import windows
finally:
    sys.path.remove(str(THEME))

AREA = dict(x=0, y=28, width=1280, height=692)


def node(id_, **kw):
    return {"id": id_, "nodes": [], "floating_nodes": [], "focus": [], **kw}


def window(id_, app="Firefox", instance="browser", **kw):
    return node(id_, window=id_ + 100, name=f"{app} %{ '{' }A1:untrusted:}}", rect=AREA,
                window_properties={"class": app, "instance": instance}, **kw)


class NotebookWindowTests(unittest.TestCase):
    def test_focus_stack_and_exclusion_of_unrelated_scratchpads(self):
        hidden = node(8, type="workspace", name="__i3_scratch", rect=AREA,
                      floating_nodes=[window(4, marks=[windows.MIN + "0-123"]), window(5)])
        active = node(9, type="workspace", name="1", rect=AREA, focus=[2, 1],
                      nodes=[window(1), window(2, focused=True),
                             window(3, instance="darfinos-pocket")])
        result = windows.windows(node(10, nodes=[hidden, active], focus=[9, 8]))
        self.assertEqual([item.id for item in result], [2, 1, 4])
        self.assertTrue(result[-1].hidden)
        bar = windows.dock(result, "1")
        self.assertIn("window-focus 2:", bar)
        self.assertIn("window-list-minimized:", bar)
        self.assertNotIn("untrusted", bar)
        self.assertLess(bar.index("window-focus 1"), bar.index("window-focus 2"))

    def test_maximize_uses_workspace_rectangle_without_fullscreen(self):
        w = windows.Window(10, "Notes", "Editor", "1", AREA, AREA, False, False, True, [])
        with patch.object(windows, "send", return_value=True) as send:
            self.assertTrue(windows.maximize(w))
            self.assertIn("resize set 1272 px 684 px", send.call_args.args[0])
            self.assertIn("position 4 px 32 px", send.call_args.args[0])
            self.assertNotIn("fullscreen", send.call_args.args[0])
            w.marks = [windows.MAX + "0_0_28_1280_692"]
            self.assertTrue(windows.maximize(w))
            self.assertIn("floating disable", send.call_args.args[0])

    def test_restore_tiles_a_previously_tiled_application(self):
        w = windows.Window(10, "Notes", "Editor", "__i3_scratch", AREA, AREA, True, False, False,
                           [windows.MIN + "0-123"])
        with patch.object(windows, "send", return_value=True) as send:
            self.assertTrue(windows.activate(w))
            self.assertIn("scratchpad show", send.call_args_list[0].args[0])
            self.assertIn("floating disable", send.call_args_list[1].args[0])
            self.assertIn("unmark", send.call_args_list[1].args[0])


class NotebookPreferencesTests(unittest.TestCase):
    def test_preferences_only_parse_the_supported_options(self):
        values = settings.preferences("gaps outer 14\ngaps inner 999\nfocus_follows_mouse no\n"
                                      "smart_gaps off\nworkspace_layout tabbed\nexec not-part-of-the-form\n")
        self.assertEqual(values, dict(inner=32, outer=14, mouse=False, smart=False, layout="tabbed"))
        self.assertEqual(settings.preferences(settings.render(values)), values)

    def test_invalid_candidate_does_not_replace_live_preferences(self):
        with tempfile.TemporaryDirectory(prefix="Notebook settings ") as tmp:
            path = Path(tmp)
            cfg, prefs = path / "config", path / "preferences.conf"
            cfg.write_text(settings.INCLUDE + "\n")
            prefs.write_text("original")
            with patch.multiple(settings, CONFIG=cfg, OVERRIDES=prefs, PROFILE=path):
                with patch.object(settings.subprocess, "run") as run:
                    run.return_value.returncode = 1
                    with self.assertRaisesRegex(ValueError, "rejeitou"):
                        settings.write_preferences("invalid")
                self.assertEqual(prefs.read_text(), "original")
                self.assertEqual(cfg.read_text(), settings.INCLUDE + "\n")
                self.assertEqual(set(path.iterdir()), {cfg, prefs})

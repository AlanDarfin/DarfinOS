"""Protocol rules for apps that remain running without a window."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "notebook_tray", Path(__file__).resolve().parents[1] / "themes/i3-notebook/tray.py"
)
tray = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tray)


class TrayTests(unittest.TestCase):
    def test_registration_accepts_service_names_object_paths_and_canonical_items(self):
        self.assertEqual(tray.address("org.example.Steam").key, "org.example.Steam/StatusNotifierItem")
        self.assertEqual(tray.address("/Item", ":1.44").key, ":1.44/Item")
        self.assertEqual(tray.address(":1.44/Items/one").key, ":1.44/Items/one")
        for value in ("", "steam", "org.example.bad-name/with space", "org.example.Steam/../Item",
                      "org.example.Steam//Item", "/Item", "org.example.Steam/Item/", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                tray.address(value)

    def test_registry_keeps_multiple_paths_deduplicates_and_checks_ownership(self):
        entries = tray.Registry()
        owners = {":1.4": ":1.4", "org.example.Steam": ":1.4", "org.example.Other": ":1.8"}
        self.assertEqual(entries.register("org.example.Steam", ":1.4", owners.get),
                         "org.example.Steam/StatusNotifierItem")
        self.assertIsNone(entries.register("org.example.Steam", ":1.4", owners.get))
        self.assertEqual(entries.register("/First", ":1.4", owners.get), ":1.4/First")
        self.assertEqual(entries.register("/Second", ":1.4", owners.get), ":1.4/Second")
        for service in ("org.example.Other", "org.example.Missing"):
            with self.subTest(service=service), self.assertRaises(ValueError):
                entries.register(service, ":1.4", owners.get)
        self.assertEqual(len(entries.items), 3)

    def test_service_transfer_and_disappearing_unique_owner_remove_exact_items(self):
        entries = tray.Registry()
        owners = {":1.4": ":1.4", "org.example.Steam": ":1.4", "org.example.Connect": ":1.8"}
        for service in ("org.example.Steam", "/Other"):
            entries.register(service, ":1.4", owners.get)
        entries.register("org.example.Connect", ":1.8", owners.get)
        self.assertEqual(entries.owner_changed("org.example.Steam", ":1.4", ":1.9"),
                         ["org.example.Steam/StatusNotifierItem"])
        self.assertEqual(entries.owner_changed(":1.4", ":1.4", ""), [":1.4/Other"])
        self.assertEqual(list(entries.items), ["org.example.Connect/StatusNotifierItem"])
        self.assertEqual(entries.owner_changed("org.example.Connect", "", ":1.8"), [])
        self.assertEqual(entries.owner_changed("org.example.Connect", ":1.8", ":1.8"), [])

    def test_dbusmenu_preserves_hierarchy_checkmarks_disabled_state_and_hides_entries(self):
        menu = tray.menu_nodes((0, {}, [
            (1, {"label": "_Biblioteca"}, []),
            (2, {"type": "separator"}, []),
            (3, {"label": "Disponível", "toggle-type": "checkmark", "toggle-state": 1}, []),
            (4, {"label": "Indisponível", "enabled": False}, []),
            (5, {"label": "Dispositivos", "children-display": "submenu"}, [(6, {"label": "Telefone teste"}, [])]),
            (7, {"label": "Oculto", "visible": False}, []),
        ]))
        self.assertEqual([node["id"] for node in menu["children"]], [1, 2, 3, 4, 5])
        self.assertTrue(menu["children"][1]["separator"])
        self.assertEqual((menu["children"][2]["toggle"], menu["children"][2]["state"]), ("checkmark", 1))
        self.assertFalse(menu["children"][3]["enabled"])
        self.assertEqual(menu["children"][4]["children"][0]["label"], "Telefone teste")
        self.assertTrue(menu["children"][4]["submenu"])
        dynamic = tray.menu_nodes((9, {"label": "Dispositivos", "children-display": "submenu"}, []))
        self.assertTrue(dynamic["submenu"])
        self.assertEqual(dynamic["children"], [])

    def test_menu_size_and_nesting_are_bounded(self):
        large = tray.menu_nodes((0, {}, [(identifier, {"label": "App"}, []) for identifier in range(2000)]))
        self.assertEqual(len(large["children"]), 511)
        nested = (0, {}, [])
        for number in range(25):
            nested = (number, {"label": "Nested"}, [nested])
        parsed = tray.menu_nodes(nested)
        depth = 0
        while parsed["children"]:
            parsed = parsed["children"][0]
            depth += 1
        self.assertEqual(depth, 8)
        for bad in (None, (), ("bad", {}, []), (1, [], [])):
            self.assertIsNone(tray.menu_nodes(bad))

    def test_icon_pixmaps_are_bounded_and_argb_is_converted_to_rgba(self):
        self.assertEqual(tray.icon_pixels([(1, 1, bytes([128, 255, 10, 0]))]),
                         (1, 1, bytes([255, 10, 0, 128])))
        self.assertIsNone(tray.icon_pixels([(10000, 10000, b""), (1, 1, b"bad"), (-1, 1, b"bad")]))
        icon = tray.icon_pixels([(1, 1, bytes([255, 1, 2, 3])), (2, 2, bytes([255, 4, 5, 6]) * 4)], size=2)
        self.assertEqual(icon[:2], (2, 2))

    def test_plain_labels_are_text_only_and_truncated(self):
        self.assertEqual(tray.plain(" Steam\n\t Connect "), "Steam Connect")
        self.assertEqual(tray.plain("<b>Steam</b>"), "<b>Steam</b>")
        self.assertEqual(len(tray.plain("a" * 1000)), 120)


if __name__ == "__main__":
    unittest.main()

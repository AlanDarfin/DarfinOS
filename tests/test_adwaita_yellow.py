"""Pinned theme data is installed without touching settings or user themes."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "adwaita_yellow", Path(__file__).resolve().parents[1] / "scripts/adwaita_yellow.py"
)
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


class AdwaitaYellowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="DarfinOS theme ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / "theme.tar.gz"
        self.themes = self.root / "home/.themes"
        self.make_archive()

    def make_archive(self, unsafe=None, incomplete=False):
        with tarfile.open(self.archive, "w:gz") as archive:
            for name in theme.THEMES:
                for file, content in (("gtk.css", b'@import url("gtk-contained.css");\n'),
                                      ("gtk-contained.css", b"/* upstream fixture */\n")):
                    if incomplete and name.endswith("dark") and file == "gtk-contained.css":
                        continue
                    info = tarfile.TarInfo(f"{theme.ARCHIVE_ROOT}/{name}/gtk-3.0/{file}")
                    info.size = len(content)
                    archive.addfile(info, io.BytesIO(content))
            if unsafe:
                info = tarfile.TarInfo(unsafe)
                if "link" in unsafe:
                    info.type = tarfile.SYMTYPE
                    info.linkname = "/etc/passwd"
                archive.addfile(info)
        self.sha = hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def install(self):
        return theme.install_archive(self.archive, self.themes, self.sha)

    def test_installs_both_upstream_variants_and_credits_without_selecting_theme(self):
        states = self.install()
        self.assertEqual(set(states.values()), {"instalado"})
        for name in theme.THEMES:
            installed = self.themes / name
            self.assertEqual((installed / "gtk-3.0/gtk-contained.css").read_text(), "/* upstream fixture */\n")
            self.assertIn(f"GtkTheme={name}", (installed / "index.theme").read_text())
            self.assertEqual(json.loads((installed / theme.MARKER).read_text())["revision"], theme.REVISION)
        self.assertFalse((self.themes.parent / ".config").exists())
        self.assertFalse(list(self.themes.glob(".darfinos-adwaita-*")))

    def test_reinstall_preserves_existing_customized_theme(self):
        self.install()
        custom = self.themes / "Adwaita-yellow-dark/gtk-3.0/gtk-contained.css"
        custom.write_text("user modified style")
        self.assertEqual(set(self.install().values()), {"preservado"})
        self.assertEqual(custom.read_text(), "user modified style")

    def test_bad_checksum_never_creates_theme_directory(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            theme.install_archive(self.archive, self.themes)
        self.assertFalse(self.themes.exists())

    def test_incomplete_or_linked_personal_destination_is_preserved(self):
        self.themes.mkdir(parents=True)
        target = self.themes / "Adwaita-yellow"
        target.mkdir()
        marker = target / "my-file"
        marker.write_text("keep")
        with self.assertRaisesRegex(ValueError, "preservado"):
            self.install()
        self.assertEqual(marker.read_text(), "keep")
        marker.unlink()
        target.rmdir()
        target.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "preservado"):
            self.install()

    def test_unsafe_archive_paths_and_links_are_rejected_before_publication(self):
        for unsafe in (f"{theme.ARCHIVE_ROOT}/../outside", "/absolute", f"{theme.ARCHIVE_ROOT}/Adwaita-yellow/link"):
            with self.subTest(path=unsafe):
                self.make_archive(unsafe=unsafe)
                with self.assertRaisesRegex(ValueError, "inesperado"):
                    self.install()
                self.assertFalse((self.themes / "Adwaita-yellow").exists())
                self.assertFalse((self.themes / "Adwaita-yellow-dark").exists())
        self.assertFalse(list(self.themes.glob(".darfinos-adwaita-*")))

    def test_incomplete_upstream_variant_does_not_publish_either_theme(self):
        self.make_archive(incomplete=True)
        with self.assertRaisesRegex(ValueError, "incompleto"):
            self.install()
        self.assertFalse((self.themes / "Adwaita-yellow").exists())
        self.assertFalse((self.themes / "Adwaita-yellow-dark").exists())


if __name__ == "__main__":
    unittest.main()

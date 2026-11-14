"""Offline coverage for portable assets and launch-scoped Flatpak theming."""
import importlib.util
import json
import io
import shlex
from contextlib import redirect_stdout
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "notebook_flatpak", Path(__file__).resolve().parents[1] / "themes/i3-notebook/flatpak.py"
)
flatpak = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flatpak)


class FlatpakThemeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="DarfinOS Flatpak home ")
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.profile = self.home / ".config/darfinos/i3-notebook"
        self.data = self.profile / "flatpak/share"
        self.icons = self.home / "system-icons"
        self.exports = self.home / "system-exports"
        context = patch.multiple(flatpak, HOME=self.home, PROFILE=self.profile, DATA=self.data,
                                 SYSTEM_ICONS=self.icons, SYSTEM_EXPORTS=self.exports)
        context.start()
        self.addCleanup(context.stop)
        environment = patch.dict(os.environ, {"XDG_DATA_HOME": str(self.home / ".local/share")})
        environment.start()
        self.addCleanup(environment.stop)

    def theme(self, root, name):
        theme = root / name
        (theme / "16x16/places").mkdir(parents=True)
        (theme / "index.theme").write_text("[Icon Theme]\nName=" + name + "\n")
        return theme

    def test_absolute_host_icon_alias_becomes_portable_and_parent_theme_is_cached(self):
        parent = self.theme(self.icons, "Papirus")
        icon = parent / "16x16/places/folder-yellow.svg"
        icon.write_text("<svg/>")
        yellow = self.theme(self.home / ".icons", "Papirus-Yellow")
        (yellow / "16x16/places/folder.svg").symlink_to(icon)
        cursor = self.theme(self.home / ".local/share/icons", "Bibata-Modern-Ice")
        (cursor / "cursors").mkdir()
        (cursor / "cursors/left_ptr").write_bytes(b"cursor")
        # A strange alias must not expose an unrelated host file to apps.
        unrelated = self.home / "private-file"
        unrelated.write_text("private")
        (yellow / "16x16/places/secret.svg").symlink_to(unrelated)
        flatpak.refresh_assets((cursor.name, 24, cursor))
        cached = self.data / "icons/Papirus-Yellow/16x16/places/folder.svg"
        self.assertTrue(cached.is_symlink())
        self.assertFalse(cached.readlink().is_absolute())
        self.assertEqual(cached.read_text(), "<svg/>")
        self.assertTrue(cached.resolve().is_relative_to(self.data / "icons"))
        self.assertFalse((cached.parent / "secret.svg").exists())
        self.assertEqual((self.data / "icons/Bibata-Modern-Ice/cursors/left_ptr").read_bytes(), b"cursor")
        before = cached.lstat().st_ino
        flatpak.refresh_assets((cursor.name, 24, cursor))
        self.assertEqual(cached.lstat().st_ino, before)
        self.assertFalse(list(self.data.glob(".icons-*")))

    def test_package_theme_update_invalidates_cache(self):
        source = self.theme(self.icons, "Papirus")
        flatpak.refresh_assets(("Bibata-Modern-Ice", 24, None))
        (source / "index.theme").write_text("[Icon Theme]\nName=Updated Papirus\n")
        flatpak.refresh_assets(("Bibata-Modern-Ice", 24, None))
        self.assertIn("Updated Papirus", (self.data / "icons/Papirus/index.theme").read_text())

    def test_generated_desktop_preserves_flatpak_flags_actions_and_field_codes(self):
        original = '''[Desktop Entry]
Name=Calculator
DBusActivatable=true
Exec=/usr/bin/flatpak run --branch=stable --file-forwarding org.gnome.Calculator @@u %U @@
Icon=org.gnome.Calculator
Actions=New;

[Desktop Action New]
Name=New
Exec=flatpak run --command=gnome-calculator org.gnome.Calculator --new-window
'''
        wrapped = flatpak.wrap_desktop(original)
        self.assertTrue(wrapped.startswith(flatpak.GENERATED))
        self.assertIn('"/usr/bin/python3" "' + str(self.profile / "flatpak.py") + '" run --branch=stable', wrapped)
        self.assertIn("@@u %U @@", wrapped)
        self.assertIn("run --command=gnome-calculator org.gnome.Calculator --new-window", wrapped)
        self.assertIn("DBusActivatable=false", wrapped)
        self.assertEqual(wrapped.count(str(self.profile / "flatpak.py")), 2)
        self.assertIsNone(flatpak.wrap_desktop("[Desktop Entry]\nExec=thunar %U\n"))
        self.assertIsNone(flatpak.wrap_desktop("[Desktop Entry]\nExec=/usr/bin/flatpakish run app\n"))

    def test_launchers_user_export_wins_and_only_owned_obsolete_files_are_removed(self):
        self.exports.mkdir()
        user_exports = self.home / ".local/share/flatpak/exports/share/applications"
        user_exports.mkdir(parents=True)
        system = self.exports / "org.example.App.desktop"
        system.write_text("[Desktop Entry]\nName=System\nExec=/usr/bin/flatpak run org.example.App\n")
        user = user_exports / system.name
        user.write_text(system.read_text().replace("Name=System", "Name=User"))
        self.assertEqual(flatpak.refresh_launchers(), 1)
        cached = self.data / "applications" / system.name
        self.assertIn("Name=User", cached.read_text())
        personal = cached.with_name("personal.desktop")
        personal.write_text("[Desktop Entry]\nName=Personal\n")
        system.unlink()
        user.unlink()
        flatpak.refresh_launchers()
        self.assertFalse(cached.exists())
        self.assertTrue(personal.is_file())

    def test_personal_flatpak_override_keeps_keyring_flags_without_changing_original(self):
        self.exports.mkdir()
        exported = self.exports / "com.vivaldi.Vivaldi.desktop"
        exported.write_text("[Desktop Entry]\nExec=/usr/bin/flatpak run com.vivaldi.Vivaldi %U\n")
        personal = self.home / ".local/share/applications" / exported.name
        personal.parent.mkdir(parents=True)
        original = exported.read_text().replace("com.vivaldi.Vivaldi %U", "com.vivaldi.Vivaldi --password-store=kwallet6 %U")
        personal.write_text(original)
        flatpak.refresh_launchers()
        cached = self.data / "applications" / exported.name
        self.assertIn("--password-store=kwallet6 %U", cached.read_text())
        self.assertEqual(personal.read_text(), original)
        personal.write_text("[Desktop Entry]\nExec=native-browser %U\n")
        flatpak.refresh_launchers()
        self.assertFalse(cached.exists())

    def test_dispatch_preserves_personal_flags_and_native_argv_without_shell(self):
        arguments = ["/usr/bin/flatpak", "run", "com.vivaldi.Vivaldi", "--password-store=kwallet6", "file with spaces"]
        with patch.object(flatpak, "launch") as launch, patch.object(flatpak.os, "execvpe") as native:
            flatpak.dispatch(arguments)
            launch.assert_called_once_with(arguments[1:])
            native.assert_not_called()
        arguments = ["native-browser", "file with spaces", "$(no-shell)"]
        with patch.object(flatpak, "launch") as launch, patch.object(flatpak.os, "execvpe") as native:
            flatpak.dispatch(arguments)
            launch.assert_not_called()
            self.assertEqual(native.call_args.args[:2], ("native-browser", arguments))

    def test_desktop_fallback_uses_original_id_and_file_arguments(self):
        with patch.object(flatpak, "refresh_launchers"), \
             patch.object(flatpak.shutil, "which", return_value="/usr/bin/gtk-launch"), \
             patch.object(flatpak.os, "execvpe") as execute:
            flatpak.launch_desktop("native.desktop", ["/folder with spaces"])
            self.assertEqual(execute.call_args.args[1], ["/usr/bin/gtk-launch", "--", "native.desktop", "/folder with spaces"])
        with self.assertRaises(ValueError):
            flatpak.launch_desktop("../../other.desktop", [])

    def test_launch_is_scoped_read_only_and_keeps_application_config_home(self):
        theme = self.home / ".themes/DarfinOS-Notebook"
        theme.mkdir(parents=True)
        (self.profile / "appearance").mkdir(parents=True)
        fonts = self.home / ".local/share/fonts"
        fonts.mkdir(parents=True)
        app_config_home = "/preserve/application/config"
        with patch.object(flatpak.shutil, "which", return_value="/usr/bin/flatpak"), \
             patch.object(flatpak, "cursor_choice", return_value=("Bibata-Modern-Ice", 32, None)), \
             patch.object(flatpak, "refresh_assets"), \
             patch.object(flatpak, "qt_style", return_value=("Fusion", "org.gnome.Platform/x86_64/49")), \
             patch.dict(os.environ, {"XDG_CONFIG_HOME": app_config_home,
                       "QT_QPA_PLATFORMTHEME": "gtk3", "QT_PLUGIN_PATH": "/host/plugins"}), \
             patch.object(flatpak.os, "execve") as execute:
            flatpak.launch(["run", "--branch=stable", "org.gnome.Calculator", "file with spaces.txt"])
        executable, command, environment = execute.call_args.args
        self.assertEqual(executable, "/usr/bin/flatpak")
        self.assertEqual(command[-3:], ["--branch=stable", "org.gnome.Calculator", "file with spaces.txt"])
        self.assertIn("--env=GTK_THEME=DarfinOS-Notebook", command)
        self.assertIn("--env=QT_STYLE_OVERRIDE=Fusion", command)
        self.assertIn("--env=XCURSOR_SIZE=32", command)
        self.assertIn(f"--filesystem={theme}:ro", command)
        self.assertIn(f"--filesystem={fonts}:ro", command)
        self.assertEqual(environment["XDG_CONFIG_HOME"], app_config_home)
        self.assertNotIn("QT_QPA_PLATFORMTHEME", environment)
        self.assertNotIn("QT_PLUGIN_PATH", environment)
        self.assertFalse(any(item.startswith("--env=XDG_CONFIG_HOME=") for item in command))
        self.assertNotIn("override", command)
        self.assertNotIn("--filesystem=home", command)
        self.assertNotIn("--filesystem=host", command)

    def test_qt_uses_only_matching_runtime_kvantum_extension(self):
        extension = self.home / "Kvantum"
        plugin = extension / "files/plugins/styles/libkvantum.so"
        plugin.parent.mkdir(parents=True)
        plugin.touch()
        success = subprocess.CompletedProcess([], 0, str(extension) + "\n", "")
        with patch.object(flatpak, "app_runtime", return_value="org.kde.Platform/x86_64/6.9"), \
             patch.object(flatpak.subprocess, "run", return_value=success) as command:
            self.assertEqual(flatpak.qt_style("flatpak", "org.kde.App"), ("kvantum", "org.kde.Platform/x86_64/6.9"))
            self.assertEqual(command.call_args.args[0][-1], "org.kde.KStyle.Kvantum/x86_64/6.9")
            plugin.unlink()
            self.assertEqual(flatpak.qt_style("flatpak", "org.kde.App")[0], "Fusion")
        with patch.object(flatpak, "app_runtime", return_value="org.gnome.Platform/x86_64/49"), \
             patch.object(flatpak.subprocess, "run") as command:
            self.assertEqual(flatpak.qt_style("flatpak", "org.gnome.App")[0], "Fusion")
            command.assert_not_called()

    def test_qt_runtime_detection_uses_run_branch_arch_and_installation_selectors(self):
        for options in (["--user", "--arch=aarch64", "--branch=beta", "--installation=test"],
                        ["--user", "--arch", "aarch64", "--branch", "beta", "--installation", "test"]):
            with self.subTest(options=options):
                context = flatpak.run_context(["run", *options, "--command", "org.example.Binary", "org.example.App", "--system"])
                self.assertEqual(context, {"options": ["--user", "--arch=aarch64", "--installation=test"], "branch": "beta"})
                response = subprocess.CompletedProcess([], 0, "org.kde.Platform/aarch64/6.9\n", "")
                with patch.object(flatpak.subprocess, "run", return_value=response) as command:
                    self.assertEqual(flatpak.app_runtime("flatpak", "org.example.App", context), "org.kde.Platform/aarch64/6.9")
                    self.assertEqual(command.call_args.args[0], ["flatpak", "info", "--show-runtime", "--user", "--arch=aarch64", "--installation=test", "org.example.App", "beta"])
        context = flatpak.run_context(["run", "--system", "org.example.App"])
        self.assertEqual(context["options"], ["--system"])
        response = subprocess.CompletedProcess([], 1, "", "no extension")
        with patch.object(flatpak, "app_runtime", return_value="org.kde.Platform/x86_64/6.9") as runtime, \
             patch.object(flatpak.subprocess, "run", return_value=response) as command:
            self.assertEqual(flatpak.qt_style("flatpak", "org.example.App", context)[0], "Fusion")
            runtime.assert_called_once_with("flatpak", "org.example.App", context)
            self.assertIn("--system", command.call_args.args[0])

    def test_metadata_timeout_falls_back_without_preventing_launch(self):
        with patch.object(flatpak, "app_runtime", side_effect=subprocess.TimeoutExpired("flatpak", 8)):
            self.assertEqual(flatpak.qt_style("flatpak", "org.example.App"), ("Fusion", ""))

    def test_optional_qt_extension_install_preserves_confirmation_and_matches_runtime(self):
        with patch.object(flatpak.shutil, "which", return_value="/usr/bin/flatpak"), \
             patch.object(flatpak, "app_runtime", return_value="org.kde.Platform/aarch64/6.9"), \
             patch.object(flatpak.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as command:
            self.assertEqual(flatpak.install_qt_style("org.kde.App"), 0)
            args = command.call_args.args[0]
            self.assertEqual(args, ["/usr/bin/flatpak", "install", "--user", "--arch=aarch64", "flathub", "org.kde.KStyle.Kvantum//6.9"])
            self.assertNotIn("--noninteractive", args)
            self.assertNotIn("-y", args)
        with patch.object(flatpak.shutil, "which", return_value="/usr/bin/flatpak"), \
             patch.object(flatpak, "app_runtime", return_value="org.gnome.Platform/x86_64/49"), \
             patch.object(flatpak.subprocess, "run") as command:
            with self.assertRaises(ValueError):
                flatpak.install_qt_style("org.gnome.App")
            command.assert_not_called()

    def test_rofi_command_preserves_spaces_and_apostrophes_in_home(self):
        with patch.object(flatpak, "PROFILE", self.home / "Alan's Notebook"), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(flatpak.main(["rofi-command"]), 0)
        command = output.getvalue().strip()
        self.assertTrue(command.endswith(" {cmd}"))
        args = shlex.split(command.replace("{cmd}", "native-app 'file with spaces'"))
        self.assertEqual(args, ["/usr/bin/python3", str(self.home / "Alan's Notebook/flatpak.py"), "dispatch", "native-app", "file with spaces"])

    def test_app_id_parsing_preserves_flatpak_command_values(self):
        self.assertEqual(flatpak.app_id(["run", "--command", "org.example.Command", "--branch=stable", "org.example.App", "argument"]), "org.example.App")
        self.assertEqual(flatpak.app_id(["run", "--file-forwarding", "org.example.App", "@@", "file", "@@"]), "org.example.App")

    def test_runtime_gtk_defaults_follow_chosen_cursor_and_preserve_app_preferences(self):
        app = self.home / ".var/app/org.example.App/config/gtk-4.0/settings.ini"
        app.parent.mkdir(parents=True)
        app.write_text("[Settings]\ncustom-preference=keep\n")
        config = flatpak.refresh_cursor_settings(("Bibata-Modern-Ice", 32, None))
        for version in ("gtk-3.0", "gtk-4.0"):
            text = (config / version / "settings.ini").read_text()
            self.assertIn("gtk-cursor-theme-name=Bibata-Modern-Ice", text)
            self.assertIn("gtk-cursor-theme-size=32", text)
            self.assertIn("gtk-font-name=DejaVu Sans 10", text)
            self.assertIn("gtk-application-prefer-dark-theme=true", text)
        self.assertIn(f"--filesystem={config}:ro", flatpak.sandbox_arguments(("Bibata-Modern-Ice", 32, None)))
        self.assertIn(f"--env=XDG_CONFIG_DIRS={config}:", "\n".join(flatpak.sandbox_arguments(("Bibata-Modern-Ice", 32, None))))
        self.assertIn("custom-preference=keep", app.read_text())
        flatpak.refresh_cursor_settings(("Bibata-Modern-Ice", 24, None))
        self.assertIn("gtk-cursor-theme-size=24", (config / "gtk-4.0/settings.ini").read_text())

    def test_desktop_helper_escapes_exec_field_codes_in_its_own_path(self):
        with patch.object(flatpak, "PROFILE", self.home / "100% profile"):
            wrapped = flatpak.wrap_desktop("[Desktop Entry]\nExec=flatpak run org.example.App %U\n")
            self.assertIn("100%% profile/flatpak.py", wrapped)
            self.assertTrue(wrapped.endswith("org.example.App %U\n"))

    def test_non_run_commands_are_not_accepted_and_no_package_changes_are_made(self):
        with patch.object(flatpak.shutil, "which", return_value="/usr/bin/flatpak"), \
             patch.object(flatpak.os, "execve") as execute:
            for arguments in ([], ["override", "--user", "--filesystem=home"], ["run"]):
                with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                    flatpak.launch(arguments)
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()

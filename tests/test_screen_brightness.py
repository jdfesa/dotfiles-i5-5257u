"""Validate the screen helper without writing to backlight hardware."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/sway-tools.sh"
SPEC = importlib.util.spec_from_file_location("brightness", ROOT / "scripts/screen-brightness-popup.py")
popup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(popup)


class ScreenBrightnessTests(unittest.TestCase):
    def test_repeated_activations_toggle_only_the_brightness_window(self):
        app, gdk, glib, gtk = Mock(), Mock(), Mock(), Mock()
        with patch.object(popup, "build_window") as build:
            for _ in range(3):
                app.get_active_window.return_value = None
                popup.activate(app, gdk, glib, gtk)
                app.get_active_window.return_value = build.return_value
                popup.activate(app, gdk, glib, gtk)
        self.assertEqual(build.call_count, 3)
        self.assertEqual(build.return_value.show_all.call_count, 3)
        self.assertEqual(build.return_value.destroy.call_count, 3)

    def test_fixed_values_target_only_the_internal_screen(self):
        with tempfile.TemporaryDirectory() as path:
            mock = Path(path) / "brightnessctl"
            mock.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
            mock.chmod(0o755)
            env = {**os.environ, "PATH": path + os.pathsep + os.defpath}
            for action, value in (("up", "+5%"), ("down", "5%-")):
                with self.subTest(action=action):
                    result = subprocess.run([str(HELPER), f"screen-brightness-{action}"],
                                            env=env, capture_output=True, text=True, timeout=3)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.splitlines(), ["-q", "-d", "intel_backlight", "set", value])
            result = subprocess.run([str(HELPER), "screen-brightness-panel", "100%"],
                                    env=env, capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(result.stdout)


    def test_reads_hardware_percentage_from_raw_values(self):
        with patch.object(popup.subprocess, "run") as run:
            run.return_value.stdout = "intel_backlight,backlight,555,40%,1388\n"
            self.assertEqual(popup.read_level(), 40)
            self.assertEqual(run.call_args.args[0],
                             ["brightnessctl", "-m", "-d", "intel_backlight", "info"])
            for invalid in ("bad", "other,backlight,1,10%,10", "intel_backlight,backlight,0,0%,0",
                            "intel_backlight,backlight,120,120%,100"):
                run.return_value.stdout = invalid
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    popup.read_level()

    def test_panel_sets_only_safe_absolute_values(self):
        with patch.object(popup.subprocess, "run") as run:
            for invalid in (0, 101, True, "40", 50.5):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    popup.write_level(invalid)
            run.assert_not_called()
            popup.write_level(37)
            self.assertEqual(run.call_args.args[0],
                             ["brightnessctl", "-q", "-d", "intel_backlight", "set", "37%"])

    def test_left_click_helper_launches_user_popup(self):
        with tempfile.TemporaryDirectory() as path:
            bindir = Path(path) / ".local/bin"
            bindir.mkdir(parents=True)
            mock = bindir / "mbp-screen-brightness"
            mock.write_text("#!/bin/sh\nprintf 'opened\\n' >&2\n")
            mock.chmod(0o755)
            result = subprocess.run([str(HELPER), "screen-brightness-panel"],
                                    env={**os.environ, "HOME": path, "XDG_RUNTIME_DIR": path, "SWAYSOCK": "unavailable"},
                                    capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "opened\n")
            self.assertFalse(result.stdout)

"""Keyboard backlight dispatch with mocked D-Bus; never writes real hardware."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/sway-tools.sh"
PREFIX = ["--system", "--timeout=2s", "call", "org.freedesktop.UPower",
          "/org/freedesktop/UPower/KbdBacklight",
          "org.freedesktop.UPower.KbdBacklight"]


class KeyboardBacklightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.log = self.root / "calls.jsonl"
        stub = self.root / "busctl"
        stub.write_text("""#!/usr/bin/python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ["KBD_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
method = args[6]
if method == os.environ.get("KBD_FAIL"):
    raise SystemExit(1)
if method == "GetMaxBrightness":
    print(os.environ.get("KBD_MAX", "i 255"))
elif method == "GetBrightness":
    print(os.environ.get("KBD_CURRENT", "i 0"))
elif method != "SetBrightness":
    raise SystemExit(2)
""")
        stub.chmod(0o755)
        self.env = {**os.environ, "PATH": str(self.root) + ":/usr/bin:/bin",
                    "XDG_RUNTIME_DIR": str(self.runtime), "KBD_LOG": str(self.log)}

    def run_action(self, action="keyboard-brightness-up", extra=(), **env):
        self.log.unlink(missing_ok=True)
        result = subprocess.run(["sh", str(HELPER), action, *extra],
                                env={**self.env, **env}, capture_output=True,
                                text=True, timeout=4)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        for call in calls:
            self.assertEqual(call[:6], PREFIX)
        return result, calls

    def test_up_uses_rounded_ten_percent_step(self):
        result, calls = self.run_action()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[6] for call in calls],
                         ["GetMaxBrightness", "GetBrightness", "SetBrightness"])
        self.assertEqual(calls[-1][7:], ["i", "26"])

    def test_down_uses_same_step(self):
        result, calls = self.run_action("keyboard-brightness-down", KBD_CURRENT="i 128")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[-1][7:], ["i", "102"])

    def test_up_clamps_to_maximum(self):
        result, calls = self.run_action(KBD_CURRENT="i 250")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[-1][7:], ["i", "255"])

    def test_down_can_turn_keyboard_completely_off(self):
        result, calls = self.run_action("keyboard-brightness-down", KBD_CURRENT="i 2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[-1][7:], ["i", "0"])

    def test_boundaries_do_not_write(self):
        for action, current in [("keyboard-brightness-up", "i 255"),
                                ("keyboard-brightness-down", "i 0")]:
            with self.subTest(action=action):
                result, calls = self.run_action(action, KBD_CURRENT=current)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(any(call[6] == "SetBrightness" for call in calls))

    def test_small_range_has_at_least_one_step(self):
        result, calls = self.run_action(KBD_MAX="i 3", KBD_CURRENT="i 1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[-1][7:], ["i", "2"])

    def test_invalid_maximum_never_writes(self):
        for value in ["", "u 255", "i -1", "i 0", "i 0255", "i 1; echo bad",
                      "i 2147483648", "i " + "9" * 80, "i 255\nextra"]:
            with self.subTest(value=value):
                result, calls = self.run_action(KBD_MAX=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(call[6] == "SetBrightness" for call in calls))

    def test_invalid_current_never_writes(self):
        for value in ["", "u 0", "i -1", "i 256", "i 00", "i 1+1",
                      "i 2147483648", "i " + "9" * 80]:
            with self.subTest(value=value):
                result, calls = self.run_action(KBD_CURRENT=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(call[6] == "SetBrightness" for call in calls))

    def test_read_errors_never_write(self):
        for method in ["GetMaxBrightness", "GetBrightness"]:
            with self.subTest(method=method):
                result, calls = self.run_action(KBD_FAIL=method)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(call[6] == "SetBrightness" for call in calls))

    def test_write_failure_is_not_hidden(self):
        result, calls = self.run_action(KBD_FAIL="SetBrightness")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls[-1][6], "SetBrightness")

    def test_lock_bounds_concurrent_actions(self):
        with (self.runtime / "mbp-keyboard-backlight.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result, calls = self.run_action()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_extra_arguments_and_unknown_action_never_call_bus(self):
        for action, extra in [("keyboard-brightness-up", ("unexpected",)),
                              ("keyboard-brightness-down", ("; touch unwanted",)),
                              ("keyboard-brightness-anything", ())]:
            with self.subTest(action=action):
                result, calls = self.run_action(action, extra=extra)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(calls, [])

    def test_bindings_and_help_preserve_screen_brightness(self):
        config = (ROOT / "config/sway/config").read_text()
        self.assertIn("bindsym XF86KbdBrightnessDown exec $tools keyboard-brightness-down", config)
        self.assertIn("bindsym XF86KbdBrightnessUp exec $tools keyboard-brightness-up", config)
        self.assertIn("bindsym XF86MonBrightnessDown exec brightnessctl -d intel_backlight set 5%-", config)
        self.assertIn("bindsym XF86MonBrightnessUp exec brightnessctl -d intel_backlight set +5%", config)
        self.assertIn("F5/F6 (or Fn+F5/F6)", (ROOT / "config/sway/keybindings-help.txt").read_text())
        self.assertIn("F5 / F6", (ROOT / "docs/keybindings.md").read_text())


if __name__ == "__main__":
    unittest.main()

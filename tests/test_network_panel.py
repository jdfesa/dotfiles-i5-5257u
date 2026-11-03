import json
import os
from pathlib import Path
import subprocess
import tempfile
import signal
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/open-networks.sh"


class NetworkPanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        binary = self.root / "bin"
        binary.mkdir()
        runtime = self.root / "runtime"
        runtime.mkdir(mode=0o700)
        self.log = self.root / "calls.jsonl"
        self.env = {**os.environ, "PATH": str(binary) + ":/usr/bin:/bin",
                    "CALL_LOG": str(self.log), "WAYLAND_DISPLAY": "fixture-wayland",
                    "SWAYSOCK": "fixture-sway", "XDG_RUNTIME_DIR": str(runtime)}
        program = '''#!/usr/bin/env python3
import json,os,pathlib,sys
name=pathlib.Path(sys.argv[0]).name
with open(os.environ["CALL_LOG"],"a") as stream: stream.write(json.dumps([name,*sys.argv[1:]])+"\\n")
args=sys.argv[1:]
if name=="nmcli":
 if "RUNNING" in args: print(os.environ.get("NM_RUNNING","running"))
 elif "WIFI" in args: print("enabled")
 elif "--rescan" in args: sys.exit(int(os.environ.get("SCAN_EXIT","0")))
elif name=="flock": sys.exit(int(os.environ.get("LOCK_EXIT","0")))
elif name=="kitty":
 import subprocess
 if not os.environ.get("KITTY_SKIP_CLIENT"): subprocess.run(args[2:],check=False)
 # Match real Kitty: its own success does not propagate a failed child.
 sys.exit(int(os.environ.get("KITTY_EXIT","0")))
elif name=="nmtui":
 import time
 time.sleep(float(os.environ.get("NMTUI_SLEEP","0")))
 sys.exit(int(os.environ.get("NMTUI_EXIT","0")))
'''
        # Fake every command that could open UI or touch networking. No real scan.
        for name in ("nmcli", "kitty", "nmtui", "flock", "swaymsg", "notify-send", "nm-connection-editor"):
            path = binary / name
            path.write_text(program)
            path.chmod(0o755)

    def run_panel(self, *args, **extra):
        result = subprocess.run(["sh", str(SCRIPT), *args], env={**self.env, **extra},
                                capture_output=True, text=True, timeout=10)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def test_connect_scans_once_and_uses_non_login_nmtui(self):
        result, calls = self.run_panel()
        self.assertEqual(result.returncode, 0, result.stderr)
        kitty = next(c for c in calls if c[0] == "kitty")
        self.assertEqual(kitty[1:3], ["--class=mbp-networks", "--title=Wi-Fi networks"])
        self.assertEqual(kitty[3:5], ["sh", "-c"])
        self.assertIn("nmtui connect", kitty[5])
        self.assertFalse(list((self.root / "runtime").glob("mbp-networks.*/*")))
        self.assertEqual(sum("--rescan" in c for c in calls), 1)
        for call in calls:
            self.assertFalse(any(word in call for word in ("disconnect", "down", "up", "sudo", "password")))

    def test_check_is_read_only_without_ui_or_scan(self):
        result, calls = self.run_panel("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Wi-Fi radio: enabled", result.stdout)
        self.assertTrue(all(c[0] == "nmcli" and "--rescan" not in c for c in calls))

    def test_second_open_focuses_existing_panel_without_scan(self):
        result, calls = self.run_panel(LOCK_EXIT="1")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(any(c[0] == "kitty" or "--rescan" in c for c in calls))
        self.assertIn(["swaymsg", '[app_id="^mbp-networks$"] focus'], calls)

    def test_scan_failure_still_opens_cached_connections(self):
        result, calls = self.run_panel(SCAN_EXIT="1")
        self.assertEqual(result.returncode, 0)
        self.assertIn("cached", result.stderr)
        self.assertTrue(any(c[0] == "kitty" for c in calls))

    def test_manager_unavailable_fails_without_opening_ui(self):
        result, calls = self.run_panel(NM_RUNNING="not-running")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(c[0] == "kitty" or "--rescan" in c for c in calls))

    def test_edit_uses_existing_graphical_editor_without_scan(self):
        result, calls = self.run_panel("--edit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["nm-connection-editor"], calls)
        self.assertFalse(any(c[0] == "kitty" or "--rescan" in c for c in calls))

    def test_kitty_failure_is_reported(self):
        result, _ = self.run_panel(KITTY_EXIT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("panel failed", result.stderr)

    def test_successful_terminal_does_not_hide_failed_client(self):
        result, _ = self.run_panel(NMTUI_EXIT="7")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("panel failed", result.stderr)

    def test_missing_client_status_is_reported(self):
        result, _ = self.run_panel(KITTY_SKIP_CLIENT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("panel failed", result.stderr)

    def test_no_native_context_does_not_launch_or_scan(self):
        result, calls = self.run_panel(WAYLAND_DISPLAY="")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(c[0] == "kitty" or "--rescan" in c for c in calls))

    def test_arbitrary_arguments_are_not_interpreted(self):
        result, calls = self.run_panel("fixture; arbitrary-command")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(calls, [])

    def test_launcher_and_bar_share_network_front_door(self):
        helper = (ROOT / "scripts/sway-tools.sh").read_text()
        desktop = (ROOT / "config/network/mbp-networks.desktop").read_text()
        config = (ROOT / "config/sway/config").read_text()
        self.assertIn('exec "$HOME/.local/bin/mbp-open-networks"', helper)
        self.assertIn("Exec=/home/jd/.local/bin/mbp-open-networks", desktop)
        self.assertIn("bindsym $mod+space exec fuzzel", config)

    def tui_command(self):
        _, calls = self.run_panel()
        kitty = next(c for c in calls if c[0] == "kitty")
        self.log.unlink()
        return [*kitty[3:-1], str(self.root / "client-status")]

    def test_tui_normal_exit_is_success(self):
        result = subprocess.run(self.tui_command(), env=self.env, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual((self.root / "client-status").read_text().strip(), "0")

    def test_tui_real_error_remains_nonzero(self):
        result = subprocess.run(self.tui_command(), env={**self.env, "NMTUI_EXIT": "7"}, timeout=5)
        self.assertEqual(result.returncode, 7)
        self.assertEqual((self.root / "client-status").read_text().strip(), "7")

    def test_tui_window_hangup_is_clean_cancellation(self):
        command = self.tui_command()
        process = subprocess.Popen(command, env={**self.env, "NMTUI_SLEEP": "10"},
                                   start_new_session=True, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if self.log.exists() and any(json.loads(line)[0] == "nmtui" for line in self.log.read_text().splitlines()):
                    break
                time.sleep(.02)
            else:
                self.fail("TUI fixture did not start")
            os.killpg(process.pid, signal.SIGHUP)
            self.assertEqual(process.wait(timeout=3), 0)
            self.assertEqual((self.root / "client-status").read_text().strip(), "0")
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()


if __name__ == "__main__":
    unittest.main()

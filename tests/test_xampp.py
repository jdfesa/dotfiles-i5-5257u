"""Test the launcher without sudo privileges or a live graphical session."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


LAUNCHER = Path(__file__).resolve().parents[1] / "scripts/xampp/xampp"
MOCK = '''#!/usr/bin/python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
with open(os.environ["TEST_LOG"], "a") as log:
    log.write(json.dumps([name, *sys.argv[1:]]) + "\\n")
if name == "xauth":
    if os.environ.get("TEST_COOKIE") == "1":
        print("mock-authorization-record")
elif name == "xhost":
    if len(sys.argv) == 1:
        if os.environ.get("TEST_NO_DISPLAY") == "1":
            print("cannot open display", file=sys.stderr)
            sys.exit(1)
        print("access control enabled, only authorized clients can connect")
        if os.environ.get("TEST_ROOT_ALLOWED") == "1":
            print("SI:localuser:root")
    elif sys.argv[1].startswith("+"):
        sys.exit(int(os.environ.get("TEST_GRANT_EXIT", "0")))
    else:
        sys.exit(int(os.environ.get("TEST_REVOKE_EXIT", "0")))
elif name == "sudo":
    sys.exit(int(os.environ.get("TEST_SUDO_EXIT", "0")))
'''


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="xampp-tests-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.auth = self.home / ".Xauthority"
        self.auth.write_text("mock authorization file, not a real cookie")
        for name in ("sudo", "xhost", "xauth"):
            stub = self.root / name
            stub.write_text(MOCK)
            stub.chmod(0o755)
        self.log = self.root / "calls.jsonl"
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("TEST_") and key != "XAUTHORITY"}
        self.env.update(PATH=f"{self.root}:{os.environ['PATH']}",
                        HOME=str(self.home), DISPLAY=":0",
                        TEST_LOG=str(self.log))

    def run_launcher(self, *args, **env):
        result = subprocess.run([str(LAUNCHER), *args],
                                env={**self.env, **env},
                                capture_output=True, text=True, timeout=10)
        calls = ([json.loads(line) for line in self.log.read_text().splitlines()]
                 if self.log.exists() else [])
        return result, calls

    def test_default_start(self):
        result, calls = self.run_launcher()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls, [["sudo", "/opt/lampp/lampp", "start"]])

    def test_native_actions_and_arguments(self):
        for action in ("stop", "status", "restart", "startmysql", "stopmysql",
                       "startapache", "stopapache", "startftp", "stopftp"):
            with self.subTest(action=action):
                self.log.unlink(missing_ok=True)
                result, calls = self.run_launcher(action, "argument with spaces")
                self.assertEqual(result.returncode, 0)
                self.assertEqual(calls, [["sudo", "/opt/lampp/lampp", action,
                                         "argument with spaces"]])

    def test_help_needs_no_privileges(self):
        result, calls = self.run_launcher("--help", DISPLAY="")
        self.assertEqual(result.returncode, 0)
        self.assertIn("xampp gui", result.stdout)
        self.assertEqual(calls, [])

    def test_cookie_from_home(self):
        result, calls = self.run_launcher("gui", TEST_COOKIE="1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls[-1], ["sudo", "/usr/bin/env", "DISPLAY=:0",
                         f"XAUTHORITY={self.auth}",
                         "/opt/lampp/manager-linux-x64.run"])
        self.assertFalse(any(call[0] == "xhost" for call in calls))

    def test_explicit_cookie_with_spaces_and_gui_arguments(self):
        auth = self.home / "authority with spaces"
        auth.write_text("mock authorization")
        result, calls = self.run_launcher("gui", "--argument with spaces",
                                          TEST_COOKIE="1", XAUTHORITY=str(auth))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls[-1][3], f"XAUTHORITY={auth}")
        self.assertEqual(calls[-1][-1], "--argument with spaces")

    def test_root_access_is_temporary(self):
        result, calls = self.run_launcher("gui")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls[1:3], [["xhost"], ["xhost", "+SI:localuser:root"]])
        self.assertEqual(calls[-2], ["sudo", "/usr/bin/env", "DISPLAY=:0",
                         "XAUTHORITY=/dev/null", "/opt/lampp/manager-linux-x64.run"])
        self.assertEqual(calls[-1], ["xhost", "-SI:localuser:root"])
        self.assertNotIn(["xhost", "+"], calls)

    def test_existing_root_access_is_not_removed(self):
        result, calls = self.run_launcher("panel", TEST_ROOT_ALLOWED="1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual([call for call in calls if call[0] == "xhost"], [["xhost"]])

    def test_no_authority_file(self):
        self.auth.unlink()
        result, calls = self.run_launcher("gui")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(any(call[0] == "xauth" for call in calls))
        self.assertEqual(calls[-1], ["xhost", "-SI:localuser:root"])

    def test_failed_sudo_still_revokes_access_and_preserves_status(self):
        result, calls = self.run_launcher("gui", TEST_SUDO_EXIT="42")
        self.assertEqual(result.returncode, 42)
        self.assertEqual(calls[-1], ["xhost", "-SI:localuser:root"])

    def test_missing_display_does_not_change_permissions(self):
        result, calls = self.run_launcher("gui", DISPLAY="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No X11 display", result.stderr)
        self.assertEqual(calls, [])

    def test_unavailable_display_does_not_call_sudo(self):
        result, calls = self.run_launcher("gui", TEST_NO_DISPLAY="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls[-1], ["xhost"])
        self.assertFalse(any(call[0] == "sudo" for call in calls))

    def test_failed_grant_does_not_call_sudo(self):
        result, calls = self.run_launcher("gui", TEST_GRANT_EXIT="3")
        self.assertEqual(result.returncode, 3)
        self.assertFalse(any(call[0] == "sudo" for call in calls))

    def test_failed_revoke_is_reported(self):
        result, calls = self.run_launcher("gui", TEST_REVOKE_EXIT="3")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Could not revoke temporary access", result.stderr)
        self.assertEqual(calls[-1], ["xhost", "-SI:localuser:root"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

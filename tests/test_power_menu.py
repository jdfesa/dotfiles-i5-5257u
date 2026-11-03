"""Adapted from i3-2310m (MIT); fake commands only, never real power actions."""
import configparser
import json
import os
from pathlib import Path
import pty
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MENU = ROOT / "scripts/power-menu"
ACTION = ROOT / "scripts/power-action.sh"


class PowerTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.jsonl"
        self.choices = self.root / "choices"
        self.env = {**os.environ, "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
                    "POWER_TEST_LOG": str(self.log), "POWER_TEST_CHOICES": str(self.choices),
                    "SWAYSOCK": "fixture-sway", "XDG_SESSION_TYPE": "wayland"}
        fake = '''#!/usr/bin/env python3
import json,os,pathlib,sys
name=pathlib.Path(sys.argv[0]).name
record={"command":name,"args":sys.argv[1:]}
if name=="fuzzel":
    record["input"]=sys.stdin.read()
with open(os.environ["POWER_TEST_LOG"],"a") as stream:
    stream.write(json.dumps(record)+"\\n")
if name=="fuzzel":
    path=pathlib.Path(os.environ["POWER_TEST_CHOICES"])
    choices=path.read_text().splitlines()
    if not choices: sys.exit(1)
    path.write_text("\\n".join(choices[1:])+"\\n" if len(choices)>1 else "")
    print(choices[0])
elif name=="swaylock" and os.environ.get("FAIL_LOCK"): sys.exit(1)
elif name=="sudo":
    sys.exit(99)  # Never escalate or fall back to sudo.
elif name=="busctl":
    if os.environ.get("FAIL_BUS"): sys.exit(1)
    print(os.environ.get("CAPABILITY", 's "yes"'))
elif name=="systemctl":
    if sys.argv[1:]==["--version"]:
        print(os.environ.get("SYSTEMD_VERSION", "systemd 257 (257.13-1~deb13u1)"))
    elif os.environ.get("FAIL_SYSTEMCTL"): sys.exit(1)
'''
        for command in ("fuzzel", "kitty", "swaylock", "swaymsg", "sudo", "systemctl", "busctl"):
            path = self.bin / command
            path.write_text(fake)
            path.chmod(0o755)

    def tearDown(self):
        self.folder.cleanup()

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def menu(self, *choices, args=()):
        self.choices.write_text("\n".join(choices) + "\n" if choices else "")
        return subprocess.run(["sh", str(MENU), *args], env=self.env, text=True, capture_output=True, timeout=5)

    def action(self, choice, args=(), **extra):
        master, slave = pty.openpty()
        try:
            os.write(master, b"\n")
            return subprocess.run(["sh", str(ACTION), *args, choice], env={**self.env, **extra},
                                  stdin=slave, text=True, capture_output=True, timeout=5)
        finally:
            os.close(master)
            os.close(slave)

    def test_all_dry_runs_execute_nothing(self):
        for choice in ("Cancel", "Lock", "Suspend", "Log out", "Reboot", "Power off"):
            result = self.menu(args=("--dry-run", choice))
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [])

    def test_unknown_command_is_not_executed(self):
        self.assertEqual(self.menu("Power off; touch /tmp/unsafe").returncode, 2)
        self.assertEqual([x["command"] for x in self.calls()], ["fuzzel"])

    def test_cancel_and_escape_execute_no_action(self):
        choices = [(), ("Cancel",)] + [(action, answer) for action in
                   ("Power off", "Reboot", "Suspend", "Log out") for answer in ("", "No")]
        for choice in choices:
            self.log.unlink(missing_ok=True)
            self.assertEqual(self.menu(*choice).returncode, 0)
            self.assertTrue(all(x["command"] == "fuzzel" for x in self.calls()))

    def test_menu_and_confirmation_lists_match_reference(self):
        for choice in ("Power off", "Reboot", "Suspend", "Log out"):
            self.log.unlink(missing_ok=True)
            self.assertEqual(self.menu(choice, "Yes").returncode, 0)
            calls = self.calls()
            self.assertEqual(calls[0]["input"], "Power off\nReboot\nSuspend\nLog out\nLock\nCancel\n")
            self.assertEqual(calls[1]["input"], "Yes\nNo\n")
            for call in calls[:2]:
                for option in ("--dmenu", "--anchor=center", "--no-sort", "--cache=/dev/null"):
                    self.assertIn(option, call["args"])

    def test_poweroff_runs_only_after_yes(self):
        self.assertEqual(self.menu("Power off", "Yes").returncode, 0)
        calls = self.calls()
        self.assertEqual(calls[1]["input"], "Yes\nNo\n")
        self.assertEqual(calls[2]["command"], "kitty")
        self.assertEqual(calls[2]["args"][-1], "poweroff")

    def test_logout_targets_only_current_sway_session(self):
        self.assertEqual(self.menu("Log out", "Yes").returncode, 0)
        self.assertEqual(self.calls()[-1], {"command": "swaymsg", "args": ["exit"]})

    def test_suspend_checks_authorization_then_locks_then_sleeps(self):
        self.assertEqual(self.action("suspend").returncode, 0)
        calls = self.calls()
        self.assertEqual([x["command"] for x in calls], ["systemctl", "busctl", "swaylock", "systemctl"])
        self.assertEqual(calls[0]["args"], ["--version"])
        self.assertEqual(calls[1]["args"][-1], "CanSuspend")
        self.assertEqual(calls[-1]["args"], ["--no-ask-password", "--check-inhibitors=auto", "suspend"])

    def test_lock_failure_prevents_suspend(self):
        self.assertEqual(self.action("suspend", FAIL_LOCK="1").returncode, 1)
        self.assertFalse(any(x["command"] == "systemctl" and x["args"] != ["--version"] for x in self.calls()))

    def test_non_yes_authorization_prevents_lock_and_action(self):
        for capability in ('s "challenge"', 's "no"', 's "na"', '', 'yes'):
            self.log.unlink(missing_ok=True)
            self.assertEqual(self.action("suspend", CAPABILITY=capability).returncode, 1)
            self.assertEqual([x["command"] for x in self.calls()], ["systemctl", "busctl"])

    def test_bus_failure_prevents_lock_and_action(self):
        self.assertEqual(self.action("suspend", FAIL_BUS="1").returncode, 1)
        self.assertEqual([x["command"] for x in self.calls()], ["systemctl", "busctl"])

    def test_helper_dry_run_checks_policy_without_lock_or_real_action(self):
        for choice in ("poweroff", "reboot", "suspend"):
            self.log.unlink(missing_ok=True)
            self.assertEqual(self.action(choice, args=("--dry-run",)).returncode, 0)
            calls = self.calls()
            self.assertEqual([x["command"] for x in calls], ["systemctl", "busctl", "systemctl"])
            self.assertEqual(calls[-1]["args"], ["--dry-run", "--no-ask-password", "--check-inhibitors=auto", choice])

    def test_old_or_unknown_systemd_prevents_auth_and_action(self):
        for version in ("systemd 256", "unrecognized", "systemd 257x"):
            self.log.unlink(missing_ok=True)
            self.assertEqual(self.action("poweroff", SYSTEMD_VERSION=version).returncode, 1)
            self.assertEqual(self.calls(), [{"command": "systemctl", "args": ["--version"]}])

    def test_poweroff_and_reboot_use_auto_without_override(self):
        for choice in ("poweroff", "reboot"):
            self.log.unlink(missing_ok=True)
            self.assertEqual(self.action(choice).returncode, 0)
            self.assertEqual(self.calls()[-1], {"command": "systemctl", "args": ["--no-ask-password", "--check-inhibitors=auto", choice]})
            self.assertEqual(self.calls()[1]["args"][-1], "CanPowerOff" if choice == "poweroff" else "CanReboot")
            self.assertFalse(any(x["command"] == "swaylock" for x in self.calls()))

    def test_inhibited_action_has_no_force_retry(self):
        result = self.action("poweroff", FAIL_SYSTEMCTL="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("failed or was inhibited", result.stderr)
        actions = [x for x in self.calls() if x["command"] == "systemctl" and x["args"] != ["--version"]]
        self.assertEqual(actions, [{"command": "systemctl", "args": ["--no-ask-password", "--check-inhibitors=auto", "poweroff"]}])

    def test_invalid_helper_action_executes_nothing(self):
        self.assertEqual(self.action("poweroff; reboot").returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_helper_without_terminal_refuses_action(self):
        result = subprocess.run(["sh", str(ACTION), "poweroff"], env=self.env,
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])


    def test_non_wayland_context_refuses_confirmation_and_action(self):
        self.env["XDG_SESSION_TYPE"] = ""
        self.assertEqual(self.menu("Power off", "Yes").returncode, 1)
        self.assertEqual([x["command"] for x in self.calls()], ["fuzzel"])

    def test_fuzzel_entry_calls_menu_not_destructive_action(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ROOT / "config/power/mbp-power-menu.desktop")
        entry = parser["Desktop Entry"]
        self.assertEqual(entry["Exec"], "/home/jd/.local/bin/mbp-power-menu")
        self.assertEqual(entry["TryExec"], entry["Exec"])
        self.assertEqual(entry["Terminal"], "false")
        self.assertIn("apagar;", entry["Keywords"])
        self.assertNotIn("Actions", entry)
        self.assertIn("fields=filename,name,generic,keywords",
                      (ROOT / "config/fuzzel/fuzzel.ini").read_text())

if __name__ == "__main__":
    unittest.main()

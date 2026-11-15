"""Exercise the optional lid guard without scheduling or requesting system power actions."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, call, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lid_poweroff", ROOT / "scripts/lid-poweroff.py")
lid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lid)

ELIGIBLE = {
    "LidClosed": True,
    "Docked": False,
    "PreparingForSleep": True,
    "HandleLidSwitch": "suspend",
    "HandleLidSwitchExternalPower": "suspend",
    "OnExternalPower": False,
}


class LidPolicyTests(unittest.TestCase):
    def test_optional_settings_default_to_safe_trial(self):
        self.assertEqual(lid.settings({}), ("dry-run", 1200))
        self.assertEqual(lid.settings({"MBP_LID_MODE": "poweroff", "MBP_LID_SECONDS": "30"}),
                         ("poweroff", 30))
        for env in ({"MBP_LID_MODE": "anything"}, *(
                {"MBP_LID_SECONDS": value} for value in ("0", "29", "20min", "86401", "1200\n", "-20"))):
            with self.subTest(env=env), self.assertRaises(ValueError):
                lid.settings(env)

    def test_requires_both_readings_and_expected_logind_phase(self):
        self.assertTrue(lid.lid_allows_action(ELIGIBLE, True, [], preparing=True))
        self.assertFalse(lid.lid_allows_action(ELIGIBLE, True, [], preparing=False))
        self.assertFalse(lid.lid_allows_action(ELIGIBLE, False, [], preparing=True))
        for key in ELIGIBLE:
            with self.subTest(missing=key):
                if key == "HandleLidSwitchExternalPower":
                    # The override is not relevant on battery.
                    continue
                self.assertFalse(lid.lid_allows_action(
                    {k: v for k, v in ELIGIBLE.items() if k != key}, True, [], preparing=True))
        for override in ({"LidClosed": False}, {"Docked": True}, {"HandleLidSwitch": "ignore"},
                         {"OnExternalPower": True, "HandleLidSwitchExternalPower": "ignore"}):
            with self.subTest(override=override):
                self.assertFalse(lid.lid_allows_action(ELIGIBLE | override, True, [], preparing=True))
        self.assertTrue(lid.lid_allows_action(ELIGIBLE | {"OnExternalPower": True}, True, [], preparing=True))

    def test_manual_suspend_is_excluded_when_lid_is_owned_by_the_desktop(self):
        inhibitors = [("idle:handle-lid-switch", "fixture", "test", "block", 1000, 1)]
        self.assertFalse(lid.lid_allows_action(ELIGIBLE, True, inhibitors, preparing=True))

    def test_physical_lid_defaults_open_on_missing_or_invalid_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state"
            self.assertFalse(lid.physical_lid_closed(state))
            for value in (b"state:      open\n", b"", b"closed", b"state: closed open", b"\xff"):
                state.write_bytes(value)
                self.assertFalse(lid.physical_lid_closed(state))
            state.write_text("state:      closed\n")
            self.assertTrue(lid.physical_lid_closed(state))

    def test_reopen_or_invalidated_lid_is_not_rearmed_by_a_close_event(self):
        self.assertTrue(lid.lid_signal_cancels(lid.MANAGER, {"LidClosed": False}, []))
        self.assertTrue(lid.lid_signal_cancels(lid.MANAGER, {}, ["LidClosed"]))
        self.assertFalse(lid.lid_signal_cancels(lid.MANAGER, {"LidClosed": True}, []))
        self.assertFalse(lid.lid_signal_cancels("other", {"LidClosed": False}, []))

    def test_boottime_alone_does_not_count_awake_time_as_suspension(self):
        self.assertFalse(lid.slept_since((500, 400), (1700, 1600)))
        self.assertTrue(lid.slept_since((500, 400), (1700, 403)))

    def test_alarm_does_not_fall_back_to_a_clock_that_cannot_wake(self):
        with patch.object(lid.os, "timerfd_create", side_effect=PermissionError) as create:
            with self.assertRaises(PermissionError):
                lid.arm_alarm(1200)
            create.assert_called_once_with(lid.CLOCK_BOOTTIME_ALARM,
                                           flags=os.TFD_CLOEXEC | os.TFD_NONBLOCK)
        with patch.object(lid.os, "timerfd_create", return_value=17), \
                patch.object(lid.os, "timerfd_settime", side_effect=OSError), \
                patch.object(lid.os, "close") as close, self.assertRaises(OSError):
            lid.arm_alarm(1200)
        close.assert_called_once_with(17)

    def test_poweroff_request_checks_root_inhibitors(self):
        login = lid.Logind.__new__(lid.Logind)
        login.owner = ":1.10"
        login.call = Mock()
        login.variant = Mock(return_value="checked flags")
        login.poweroff()
        login.variant.assert_called_once_with("(t)", 1)
        login.call.assert_called_once_with(":1.10", lid.LOGIN_PATH, lid.MANAGER,
                                           "PowerOffWithFlags", "checked flags", "()")


class GuardFlowTests(unittest.TestCase):
    def exercise(self, *, mode="poweroff", eligible=True, closed_at_expiry=True,
                 slept=True, reopen=False, change_owner=False, inhibitor_error=False):
        gio, glib = Mock(), Mock()
        glib.Error = type("BusError", (Exception,), {})
        glib.IOCondition.IN, glib.IOCondition.ERR, glib.IOCondition.HUP = 1, 8, 16
        loop = glib.MainLoop.return_value
        login = Mock(owner=":1.10")
        login.lid_allows.side_effect = [eligible, closed_at_expiry]
        login.bus.signal_subscribe.side_effect = [10, 20]
        if inhibitor_error:
            login.poweroff.side_effect = glib.Error("inhibited")

        def dispatch():
            if reopen:
                receive = login.bus.signal_subscribe.call_args_list[1].args[-1]
                for closed in (False, True):
                    receive(None, ":1.10", None, None, None,
                            Mock(**{"unpack.return_value": (lid.MANAGER, {"LidClosed": closed}, [])}))
            if change_owner:
                receive = login.bus.signal_subscribe.call_args_list[0].args[-1]
                receive(None, None, None, None, None,
                        Mock(**{"unpack.return_value": (lid.LOGIN, ":1.10", ":1.11")}))
            # Even a queued timeout must not proceed after either cancellation.
            glib.unix_fd_add_full.call_args.args[-1](17, glib.IOCondition.IN)
            glib.timeout_add.call_args.args[1]()

        loop.run.side_effect = dispatch
        with patch.object(lid, "Logind", return_value=login), \
                patch.object(lid, "arm_alarm", return_value=17) as arm, \
                patch.object(lid, "boot_and_active", side_effect=[(500, 400), (1700, 405 if slept else 1600)]), \
                patch.object(lid, "notify_ready") as notify, \
                patch.object(lid.os, "read", return_value=b"\0" * 8), \
                patch.object(lid.os, "close") as close, patch.object(lid, "log") as log:
            lid.run_guard(mode, 1200, gio, glib)
        notify.assert_called_once_with()
        self.assertEqual(login.bus.signal_unsubscribe.call_args_list, [call(10), call(20)])
        if eligible:
            arm.assert_called_once_with(1200)
            close.assert_called_once_with(17)
        else:
            arm.assert_not_called()
            close.assert_not_called()
            loop.run.assert_not_called()
        return login, [args.args[0] for args in log.call_args_list]

    def test_guard_does_not_arm_with_open_lid(self):
        login, _ = self.exercise(eligible=False)
        login.poweroff.assert_not_called()

    def test_guard_only_requests_normal_poweroff_after_suspend_with_lid_closed(self):
        login, _ = self.exercise()
        self.assertEqual(login.lid_allows.call_args_list, [call(preparing=True), call(preparing=False)])
        login.poweroff.assert_called_once_with()
        for scenarios in (dict(reopen=True), dict(change_owner=True), dict(slept=False),
                          dict(closed_at_expiry=False), dict(mode="dry-run")):
            with self.subTest(scenarios=scenarios):
                self.exercise(**scenarios)[0].poweroff.assert_not_called()

    def test_inhibited_shutdown_is_not_retried_or_forced(self):
        login, messages = self.exercise(inhibitor_error=True)
        login.poweroff.assert_called_once_with()
        self.assertIn("Could not request a normal poweroff: inhibited", messages)

    def test_optional_units_do_not_enable_any_resident_service(self):
        options = ROOT / "config/power/lid-poweroff"
        unit = (options / "mbp-lid-poweroff.service").read_text()
        self.assertNotIn("[Install]", unit)
        self.assertIn("ConditionPathExists=/etc/default/mbp-lid-poweroff", unit)
        self.assertIn("MBP_LID_MODE=dry-run", (options / "settings.conf").read_text())
        self.assertIn("LidSwitchIgnoreInhibited=no", (options / "lid-switch.conf").read_text())
        main = (ROOT / "config/manifest.json").read_text()
        self.assertNotIn("lid-poweroff", main)

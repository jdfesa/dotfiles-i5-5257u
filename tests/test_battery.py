"""Battery presentation is pure; all hardware/UPower failures are simulated."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("battery_adapter", ROOT / "scripts/status-adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class BatteryIconTests(unittest.TestCase):
    def test_discharging_levels_and_percentage(self):
        for level, icon in enumerate(adapter.BATTERY_LEVEL_ICONS):
            value = level * 10
            with self.subTest(value=value):
                text, _ = adapter.format_battery((value, "discharging"))
                self.assertIn(">" + icon + "</span>", text)
                self.assertTrue(text.endswith(f" {value}%"))
        self.assertIn(adapter.BATTERY_LEVEL_ICONS[7], adapter.format_battery((79.9, "discharging"))[0])

    def test_charging_levels_are_distinct_even_at_100_percent(self):
        for level, icon in enumerate(adapter.BATTERY_CHARGING_ICONS):
            value = level * 10
            text, _ = adapter.format_battery((value, "charging"))
            self.assertIn(icon, text)
            self.assertNotIn(adapter.BATTERY_FULL_MARK, text)
            self.assertTrue(text.endswith(f" {value}%"))
        self.assertNotEqual(adapter.format_battery((100, "charging")),
                            adapter.format_battery((100, "fully-charged")))

    def test_full_state_does_not_invent_100_percent(self):
        text, _ = adapter.format_battery((97, "fully-charged"))
        self.assertIn(adapter.BATTERY_FULL_MARK, text)
        self.assertTrue(text.endswith(" 97%"))
        self.assertNotIn("100%", text)

    def test_pending_states_do_not_claim_active_charging(self):
        for state in ("pending-charge", "pending-discharge"):
            text, _ = adapter.format_battery((58, state))
            self.assertIn(adapter.BATTERY_PENDING_MARK, text)
            self.assertFalse(any(icon in text for icon in adapter.BATTERY_CHARGING_ICONS))
            self.assertTrue(text.endswith(" 58%"))

    def test_unknown_state_keeps_known_charge(self):
        for state in ("unknown", "future-state", "<unsafe>"):
            text, _ = adapter.format_battery((57, state))
            self.assertIn(adapter.BATTERY_UNKNOWN_ICON, text)
            self.assertTrue(text.endswith(" 57%"))
            self.assertNotIn(state, text)

    def test_missing_or_invalid_readings_are_not_zero_percent(self):
        for reading in (None, (), "50", (True, "charging"), (-1, "discharging"),
                        (101, "charging"), (10 ** 1000, "charging"), (float("nan"), "charging"),
                        (float("inf"), "charging"), ("57", "charging")):
            with self.subTest(reading=reading):
                text, color = adapter.format_battery(reading)
                self.assertIn(adapter.BATTERY_UNKNOWN_ICON, text)
                self.assertTrue(text.endswith(" --%"))
                self.assertNotIn(" 0%", text)
                self.assertEqual(color, adapter.MUTED)

    def test_low_battery_colors_and_existing_warning_thresholds(self):
        for value in (0, 10, 20):
            self.assertEqual(adapter.format_battery((value, "discharging"))[1], adapter.RED)
        self.assertNotEqual(adapter.format_battery((20, "charging"))[1], adapter.RED)
        self.assertEqual(adapter.battery.warning_level((20, "discharging")), 1)
        self.assertEqual(adapter.battery.warning_level((10, "discharging")), 2)
        self.assertEqual(adapter.battery.warning_level((10, "charging")), 0)

    def test_rendering_and_collapse_do_not_query_upower(self):
        with patch.object(adapter.subprocess, "run") as run:
            view = adapter.StatusView()
            compact = view.update([], charge=(57, "discharging"))
            text = next(b for b in compact if b["name"] == "battery")["full_text"]
            self.assertTrue(text.endswith(" 57%"))
            adapter.handle_click(dict(name="stats_toggle", instance="secondary", button=1), view)
            expanded = view.render()
            self.assertEqual(next(b for b in expanded if b["name"] == "battery")["full_text"], text)
            run.assert_not_called()

    def test_missing_backend_battery_still_shows_unavailable_indicator(self):
        frame = adapter.StatusView().update([])
        self.assertTrue(next(b for b in frame if b["name"] == "battery")["full_text"].endswith(" --%"))

    @unittest.skipUnless(shutil.which("fc-query"), "fontconfig not available")
    def test_all_battery_icons_are_in_the_existing_managed_font(self):
        charset = subprocess.check_output([
            "fc-query", "--format", "%{charset}",
            str(ROOT / "config/fonts/JetBrainsMonoNerdFontMono-Regular.ttf")], text=True)
        ranges = [tuple(int(p, 16) for p in chunk.split("-")) for chunk in charset.split()]
        icons = (adapter.BATTERY_LEVEL_ICONS + adapter.BATTERY_CHARGING_ICONS +
                 (adapter.BATTERY_UNKNOWN_ICON, adapter.BATTERY_FULL_MARK, adapter.BATTERY_PENDING_MARK))
        self.assertEqual([f"U+{ord(icon):X}" for icon in icons
                          if not any(r[0] <= ord(icon) <= r[-1] for r in ranges)], [])


class BatteryReaderTests(unittest.TestCase):
    def test_malformed_percentage_never_crashes_the_bar(self):
        for value in ("40..0", ".", "101", "NaN", "inf"):
            self.assertIsNone(adapter.battery.parse_battery(
                f"state: discharging\npercentage: {value}%\ncapacity: 62.9%\n"))

    def test_one_bounded_query_reads_percentage_not_health_or_cycles(self):
        result = Mock(stdout="state: charging\npercentage: 79.5%\ncapacity: 62.9%\ncharge-cycles: 900\n")
        with patch.object(adapter.battery.subprocess, "run", return_value=result) as run:
            self.assertEqual(adapter.battery.read_battery(), (79.5, "charging"))
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0],
                         ["upower", "-i", "/org/freedesktop/UPower/devices/DisplayDevice"])
        self.assertEqual(run.call_args.kwargs["timeout"], 5)
        self.assertEqual(run.call_args.kwargs["env"]["LC_ALL"], "C")

    def test_upower_timeout_or_missing_command_is_unavailable(self):
        for error in (OSError("fixture"), subprocess.TimeoutExpired("upower", 5)):
            with patch.object(adapter.battery.subprocess, "run", side_effect=error):
                self.assertIsNone(adapter.battery.read_battery())


if __name__ == "__main__":
    unittest.main()

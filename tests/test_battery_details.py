"""Battery snapshot formatting and UPower integration without a live session."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("battery_details", ROOT / "scripts/battery-details-popup.py")
details = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(details)


class BatteryDetailsTests(unittest.TestCase):
    def test_reads_one_present_system_battery_not_a_peripheral(self):
        sources = {
            "/external": {"Type": 2, "PowerSupply": False, "IsPresent": True},
            "/missing": {"Type": 2, "PowerSupply": True, "IsPresent": False},
            "/system": {"Type": 2, "PowerSupply": True, "IsPresent": True},
            "/unused": {"Type": 2, "PowerSupply": True, "IsPresent": True},
        }
        get_properties = Mock(side_effect=sources.__getitem__)
        self.assertIs(details.system_battery(reversed(sources), get_properties), sources["/system"])
        self.assertEqual([call.args[0] for call in get_properties.call_args_list],
                         ["/external", "/missing", "/system"])
        self.assertIsNone(details.system_battery(["/missing"], get_properties))

    def test_upower_snapshot_queries_devices_and_properties_with_timeout(self):
        gio, glib = Mock(), Mock()
        bus = gio.bus_get_sync.return_value
        props = {"Type": 2, "PowerSupply": True, "IsPresent": True}
        bus.call_sync.side_effect = [Mock(**{"unpack.return_value": (["/system"],)}),
                                     Mock(**{"unpack.return_value": (props,)})]
        self.assertEqual(details.read_snapshot(gio, glib), props)
        self.assertEqual([c.args[3] for c in bus.call_sync.call_args_list],
                         ["EnumerateDevices", "GetAll"])
        for call in bus.call_sync.call_args_list:
            self.assertEqual(call.args[6], gio.DBusCallFlags.NO_AUTO_START)
            self.assertTrue(0 < call.args[7] <= 900)

    def test_reports_charge_and_health_separately(self):
        rows = dict(details.format_rows({
            "Percentage": 84.0, "State": 2, "Capacity": 63.0, "ChargeCycles": 150,
            "EnergyFull": 31.5, "EnergyFullDesign": 50.0, "Temperature": 30.5,
            "EnergyRate": 6.0, "TimeToEmpty": 4200,
        }))
        self.assertEqual(rows, {
            "Charge": "84.0%", "State": "Discharging", "Battery health": "63.0%",
            "Full capacity": "31.5 Wh", "Design capacity": "50.0 Wh",
            "Charge cycles": "150", "Temperature": "30.5 °C", "Battery draw": "6.0 W",
            "Estimated time left": "1 h 10 min",
        })

    def test_estimate_depends_on_power_state(self):
        fields = {"TimeToFull": 180, "TimeToEmpty": 180, "EnergyRate": 10}
        charging = dict(details.format_rows(fields | {"State": 1}))
        self.assertEqual(charging["Estimated time to full"], "3 min")
        for state in (1, 4, 5, 6):
            rows = dict(details.format_rows(fields | {"State": state}))
            self.assertNotIn("Battery draw", rows)
            self.assertNotIn("Estimated time left", rows)
            if state != 1:
                self.assertNotIn("Estimated time to full", rows)

    def test_missing_sentinel_and_invalid_values_are_not_invented(self):
        rows = dict(details.format_rows({
            "State": 2, "Percentage": 120, "Capacity": float("nan"), "ChargeCycles": -1,
            "EnergyFull": 0, "Temperature": 0, "EnergyRate": float("inf"), "TimeToEmpty": 0,
        }))
        self.assertEqual(rows.pop("State"), "Discharging")
        self.assertEqual(set(rows.values()), {details.UNAVAILABLE})
        self.assertEqual(dict(details.format_rows({"Percentage": 0, "ChargeCycles": 0}))["Charge"], "0.0%")

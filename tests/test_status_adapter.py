import importlib.util
import json
from pathlib import Path
import select
import subprocess
import sys
import time
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("adapter", ROOT / "scripts/status-adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class AdapterTests(unittest.TestCase):
    def test_notification_failure_does_not_crash_the_bar(self):
        with patch.object(adapter.subprocess, "run", side_effect=OSError("fixture unavailable")):
            self.assertFalse(adapter.notify_low_battery(2))

    def test_battery_uses_upower_not_native_health_value(self):
        blocks = adapter.adapt_status([dict(name="battery", full_text="BAT 63%")], charge=(97, "discharging"))
        text = next(b for b in blocks if b["name"] == "battery")["full_text"]
        self.assertTrue(text.endswith(" 97%"))
        self.assertNotIn("63%", text)

    def test_wireless_keeps_icon_only(self):
        block = next(b for b in adapter.adapt_status([dict(name="wireless", instance=adapter.WIRELESS, full_text="78%")]) if b["name"] == "wireless")
        self.assertNotIn("78", block["full_text"])
        self.assertIn("BGH Status Icons", block["full_text"])

    def test_clicks_are_fixed_sway_actions_not_shell_interpolation(self):
        with patch.object(adapter.subprocess, "run") as run:
            adapter.handle_click(dict(name="wireless", instance=adapter.WIRELESS, button=1))
            self.assertEqual(run.call_args.args[0], ["swaymsg", "exec ~/.local/bin/mbp-sway-tools networks"])
            run.reset_mock()
            adapter.handle_click(dict(name="wireless; arbitrary-command", instance=adapter.WIRELESS, button=1))
            run.assert_not_called()

    def test_cpu_click_is_left_button_only_and_targets_the_aggregate_block(self):
        block = adapter.adapt_status([dict(name="cpu_usage", full_text="42%")])[0]
        self.assertEqual(block["instance"], "aggregate")
        event = dict(name=block["name"], instance=block["instance"], button=1)
        with patch.object(adapter.subprocess, "run") as run:
            self.assertFalse(adapter.handle_click(event))
            run.assert_called_once()
            self.assertEqual(run.call_args.args[0],
                             ["swaymsg", "exec ~/.local/bin/mbp-sway-tools resource-monitor"])
            run.reset_mock()
            for change in (dict(button=3), dict(button=4), dict(button=True),
                           dict(instance=None), dict(instance="aggregate; exec unwanted"),
                           dict(name="cpu_temperature")):
                self.assertFalse(adapter.handle_click(dict(event, **change)))
            run.assert_not_called()

    def test_screen_brightness_only_dispatches_fixed_actions(self):
        event = dict(name="screen_brightness", instance="intel_backlight")
        with patch.object(adapter.subprocess, "run") as run:
            for button, action in ((1, "panel"), (4, "up"), (5, "down")):
                self.assertFalse(adapter.handle_click(dict(event, button=button)))
                self.assertEqual(run.call_args.args[0], [
                    "swaymsg", f"exec ~/.local/bin/mbp-sway-tools screen-brightness-{action}"])
            run.reset_mock()
            for event in (dict(event, button=3), dict(event, button=True),
                          dict(event, button=4, instance="other"),
                          dict(name="wireless", instance=adapter.WIRELESS, button=4)):
                self.assertFalse(adapter.handle_click(event))
            run.assert_not_called()

    def test_popups_anchor_to_block_not_cursor_using_logical_pixels(self):
        coordinates = dict(x=1028, y=10, relative_x=8, relative_y=10,
                           width=28, height=28, scale=2)
        with patch.object(adapter.subprocess, "run") as run:
            for name, instance, helper in (
                    ("screen_brightness", "intel_backlight", "screen-brightness-panel"),
                    ("tztime", "local", "calendar"),
                    ("cpu_usage", "aggregate", "resource-monitor")):
                adapter.handle_click(dict(coordinates, name=name, instance=instance, button=1))
                self.assertEqual(run.call_args.args[0], [
                    "swaymsg", f"exec ~/.local/bin/mbp-sway-tools {helper} 1034 28"])
            adapter.handle_click(dict(coordinates, name="screen_brightness",
                                      instance="intel_backlight", button=4))
            self.assertEqual(run.call_args.args[0],
                             ["swaymsg", "exec ~/.local/bin/mbp-sway-tools screen-brightness-up"])

    def test_invalid_popup_coordinates_preserve_fixed_launch(self):
        event = dict(name="tztime", instance="local", button=1, x=1028, y=10,
                     relative_x=8, relative_y=10, width=28, height=28)
        with patch.object(adapter.subprocess, "run") as run:
            for invalid in (dict(x="1; exec unwanted"), dict(x=True), dict(width=0),
                            dict(relative_x=29), dict(height=400), dict(relative_y=11)):
                adapter.handle_click(dict(event, **invalid))
                self.assertEqual(run.call_args.args[0],
                                 ["swaymsg", "exec ~/.local/bin/mbp-sway-tools calendar"])

    def test_calendar_click_is_allowlisted_and_left_button_only(self):
        with patch.object(adapter.subprocess, "run") as run:
            adapter.handle_click(dict(name="tztime", instance="local", button=1))
            self.assertEqual(run.call_args.args[0],
                             ["swaymsg", "exec ~/.local/bin/mbp-sway-tools calendar"])
            run.reset_mock()
            for event in (dict(name="tztime", instance="local; exec bad", button=1),
                          dict(name="tztime", instance="local", button=3),
                          dict(name="tztime", instance="local", button=True)):
                adapter.handle_click(event)
            run.assert_not_called()


class CollapseTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [dict(name="read_file", instance="/fixture/weather.txt", full_text="☁ 22°C"),
                       dict(name="memory", full_text="60%"),
                       dict(name="cpu_usage", full_text="2%"),
                       dict(name="cpu_temperature", full_text="45°C"),
                       dict(name="disk_info", full_text="100 GB"),
                       dict(name="read_file", instance="/fixture/updates.txt", full_text="137"),
                       dict(name="volume", instance="default.Master.0", full_text="40%"),
                       dict(name="wireless", instance=adapter.WIRELESS, full_text="78%"),
                       dict(name="battery", full_text="native health ignored"),
                       dict(name="tztime", instance="local", full_text="Tue Nov 03 12:00")]
        self.click = dict(name="stats_toggle", instance="secondary", button=1)
        self.traffic = Mock()
        self.traffic.sample.return_value = "↑0K ↓0K/s"

    def test_compact_by_default_with_all_essential_blocks(self):
        view = adapter.StatusView()
        frame = view.update(self.blocks, self.traffic, (75, "discharging"))
        self.assertFalse(adapter.SECONDARY_BLOCKS & {b["name"] for b in frame})
        self.assertEqual([b["name"] for b in frame],
                         ["read_file", "stats_toggle", "read_file", "screen_brightness",
                          "volume", "wireless", "battery", "tztime"])
        self.assertEqual(next(b for b in frame if b["name"] == "battery")["full_text"],
                         adapter.format_battery((75, "discharging"))[0])
        self.assertEqual(frame[1]["full_text"], "\uf054")

    def test_expand_and_collapse_without_processes_or_resampling(self):
        view = adapter.StatusView()
        first = view.update(self.blocks, self.traffic, (75, "discharging"))
        with patch.object(adapter.subprocess, "run") as run, \
                patch.object(adapter.battery, "read_battery") as charge:
            self.assertTrue(adapter.handle_click(self.click, view))
            expanded = view.render()
            self.assertTrue(adapter.SECONDARY_BLOCKS <= {b["name"] for b in expanded})
            self.assertEqual(next(b for b in expanded if b["name"] == "stats_toggle")["full_text"], "\uf053")
            self.assertTrue(adapter.handle_click(self.click, view))
            self.assertEqual(view.render(), first)
            run.assert_not_called()
            charge.assert_not_called()
        self.traffic.sample.assert_called_once_with()

    def test_invalid_clicks_cannot_change_visibility(self):
        view = adapter.StatusView()
        for event in (dict(self.click, instance="secondary; arbitrary-command"),
                      dict(self.click, name="stats_toggle; bad"),
                      dict(self.click, button=3), dict(self.click, button=True)):
            with self.subTest(event=event):
                self.assertFalse(adapter.handle_click(event, view))
                self.assertFalse(view.expanded)
        self.assertFalse(adapter.handle_click(self.click))

    def test_click_before_first_frame_does_not_emit_or_fetch_data(self):
        view = adapter.StatusView()
        self.assertTrue(adapter.handle_click(self.click, view))
        self.assertIsNone(view.render())
        frame = view.update(self.blocks, self.traffic)
        self.assertTrue(adapter.SECONDARY_BLOCKS <= {b["name"] for b in frame})

    def test_urgent_secondary_block_is_not_hidden(self):
        self.blocks[3]["urgent"] = True
        frame = adapter.StatusView().update(self.blocks)
        self.assertIn("cpu_temperature", {b["name"] for b in frame})
        self.assertNotIn("cpu_usage", {b["name"] for b in frame})

    def test_cached_frame_does_not_reformat_and_raw_input_is_untouched(self):
        view = adapter.StatusView(expanded=True)
        first = view.update(self.blocks, self.traffic)
        self.assertEqual(self.blocks[1]["full_text"], "60%")
        with patch.object(adapter, "adapt_status") as adapt:
            self.assertEqual(view.render(), first)
            self.assertEqual(view.render(), first)
            adapt.assert_not_called()
        second = view.update(self.blocks, self.traffic)
        self.assertEqual(second, first)
        self.assertEqual(self.traffic.sample.call_count, 2)

    def test_new_view_resets_to_compact(self):
        view = adapter.StatusView(expanded=True)
        view.update(self.blocks)
        self.assertFalse(adapter.StatusView().expanded)

    def test_real_loop_redraws_cached_frame_before_next_producer_tick(self):
        blocks = [dict(name="cpu_usage", full_text="2%"),
                  dict(name="memory", full_text="60%"),
                  dict(name="battery", full_text="unused"),
                  dict(name="tztime", instance="local", full_text="Tue Nov 03 12:00")]
        producer = ("import json,time; print('{\"version\":1}',flush=True); "
                    "print('[',flush=True); print(" + repr(json.dumps(blocks)) + ",flush=True); time.sleep(60)")
        runner = f'''import importlib.util,subprocess,sys
spec=importlib.util.spec_from_file_location("loop_adapter",{str(ROOT / "scripts/status-adapter.py")!r})
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
child=subprocess.Popen([sys.executable,"-u","-c",{producer!r}],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,bufsize=0)
module.subprocess.Popen=lambda *args,**kwargs:child
reads=[0]
def charge():
 reads[0]+=1
 return 75+reads[0],"discharging"
module.battery.read_battery=charge
module.notify_low_battery=lambda level:False
module.main()
'''
        process = subprocess.Popen([sys.executable, "-u", "-c", runner], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

        def line():
            self.assertTrue(select.select([process.stdout], [], [], 3)[0], "No protocol output within 3 s")
            value = process.stdout.readline()
            self.assertTrue(value, "Adapter exited before the next frame")
            return value.decode().strip().lstrip(",")

        try:
            self.assertTrue(json.loads(line())["click_events"])
            self.assertEqual(line(), "[")
            first = json.loads(line())
            self.assertNotIn("cpu_usage", {b["name"] for b in first})
            for expanded in (True, False):
                started = time.monotonic()
                process.stdin.write((json.dumps(self.click) + "\n").encode())
                process.stdin.flush()
                frame = json.loads(line())
                self.assertLess(time.monotonic() - started, 3)
                self.assertEqual("cpu_usage" in {b["name"] for b in frame}, expanded)
                # A redraw must not query UPower again or format the cached text twice.
                self.assertEqual(next(b for b in frame if b["name"] == "battery")["full_text"],
                                 adapter.format_battery((76, "discharging"))[0])
                if expanded:
                    text = next(b for b in frame if b["name"] == "cpu_usage")["full_text"]
                    self.assertNotIn("CPU", text)
                    self.assertTrue(text.endswith(" 2%"))
        finally:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()


if __name__ == "__main__":
    unittest.main()

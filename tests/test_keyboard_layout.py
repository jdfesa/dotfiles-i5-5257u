"""US/Spain ES state, bounded Sway IPC and cached bar redraws; no real keyboard I/O."""
import copy
import importlib.util
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("layout_adapter", ROOT / "scripts/status-adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
Layout = adapter.KeyboardLayout


def keyboard(index=0, identifier="fixture", names=None):
    return {"identifier": identifier, "type": "keyboard",
            "xkb_layout_names": Layout.NAMES if names is None else names,
            "xkb_active_layout_index": index}


class KeyboardLayoutTests(unittest.TestCase):
    def controller(self, items=None, command_reply=None):
        state = copy.deepcopy([keyboard()] if items is None else items)
        calls = []
        def request(kind, payload):
            calls.append((kind, payload))
            if kind == 100:
                return copy.deepcopy(state)
            self.assertEqual(kind, 0)
            self.assertIn(payload, ["input type:keyboard xkb_switch_layout 0",
                                    "input type:keyboard xkb_switch_layout 1"])
            if command_reply is not None:
                return command_reply
            for item in state:
                if item.get("type") == "keyboard":
                    item["xkb_active_layout_index"] = int(payload[-1])
            return [{"success": True}]
        control = Layout(request=request)
        return control, state, calls

    def test_labels_are_actual_us_and_spain_es(self):
        for index, label in [(0, "US"), (1, "ES"), (True, "--"), (2, "--")]:
            with self.subTest(index=index):
                control, _, _ = self.controller([keyboard(index)])
                control.refresh()
                self.assertEqual(control.label, label)

    def test_empty_mixed_and_unsupported_are_not_guessed(self):
        for items in [[], [keyboard(0, "a"), keyboard(1, "b")],
                      [keyboard(names=["English (US)"])], [keyboard(names=["English (US)", "Spanish (Latin American)"])]]:
            with self.subTest(items=items):
                control, _, _ = self.controller(items)
                control.refresh()
                self.assertEqual(control.label, "--")

    def test_pointer_is_not_a_keyboard(self):
        control, _, _ = self.controller([keyboard(), {"type": "pointer"}])
        control.refresh()
        self.assertEqual(control.label, "US")

    def test_toggle_uses_only_fixed_indices_and_confirms_result(self):
        control, _, calls = self.controller()
        self.assertTrue(control.toggle())
        self.assertEqual(control.label, "ES")
        self.assertEqual(calls, [(100, ""), (0, "input type:keyboard xkb_switch_layout 1"), (100, "")])
        calls.clear()
        control.toggle()
        self.assertEqual(control.label, "US")
        self.assertEqual(calls[1], (0, "input type:keyboard xkb_switch_layout 0"))

    def test_mixed_keyboards_are_unified_to_us(self):
        control, _, calls = self.controller([keyboard(0, "a"), keyboard(1, "b")])
        control.toggle()
        self.assertEqual(control.label, "US")
        self.assertIn((0, "input type:keyboard xkb_switch_layout 0"), calls)

    def test_unsupported_keyboard_never_sends_command(self):
        control, _, calls = self.controller([keyboard(names=["English (US)"])])
        control.toggle()
        self.assertFalse(any(kind == 0 for kind, _ in calls))
        self.assertEqual(control.label, "--")

    def test_command_failures_do_not_fabricate_success(self):
        for reply in [[{"success": False}], [], {}, [{"success": 1}], [{"success": True}, {"success": False}]]:
            with self.subTest(reply=reply):
                control, _, _ = self.controller(command_reply=reply)
                control.toggle()
                self.assertEqual(control.label, "US")

    def test_read_failure_is_unknown_and_does_not_crash(self):
        control = Layout(request=Mock(side_effect=OSError("fixture unavailable")))
        control.inputs = {"fixture": 1}
        self.assertTrue(control.toggle())
        self.assertEqual(control.label, "--")
        control.start()
        self.assertIsNone(control.events)

    def test_invalid_input_list_is_rejected(self):
        for items in [{}, [None], [dict(type="keyboard", identifier="")]]:
            with self.subTest(items=items):
                control = Layout(request=Mock(return_value=items))
                with self.assertRaises(ValueError):
                    control.refresh()

    def test_fragmented_and_batched_events(self):
        control, _, calls = self.controller()
        control.refresh()
        calls.clear()
        event = {"change": "xkb_layout", "input": keyboard(1)}
        packet = Layout._packet(Layout.INPUT_EVENT, json.dumps(event))
        control.feed(packet[:7])
        self.assertEqual(control.label, "US")
        control.feed(packet[7:])
        self.assertEqual(control.label, "ES")
        removed = Layout._packet(Layout.INPUT_EVENT, json.dumps({"change": "removed", "input": keyboard(1)}))
        added = Layout._packet(Layout.INPUT_EVENT, json.dumps({"change": "added", "input": keyboard(0, "new")}))
        control.feed(removed + added)
        self.assertEqual(control.label, "US")
        self.assertEqual(calls, [])

    def test_bad_event_headers_and_payloads_are_rejected(self):
        for packet in [Layout.HEADER.pack(b"badipc", 0, Layout.INPUT_EVENT),
                       Layout.HEADER.pack(b"i3-ipc", Layout.MAX_PAYLOAD + 1, Layout.INPUT_EVENT),
                       Layout._packet(Layout.INPUT_EVENT, "[]")]:
            with self.subTest(packet=packet[:14]):
                control = Layout()
                with self.assertRaises(ValueError):
                    control.feed(packet)

    def test_socket_eof_degrades_to_unknown(self):
        control, _, _ = self.controller()
        control.refresh()
        left, right = socket.socketpair()
        control.events = left
        right.close()
        self.assertTrue(control.read_events())
        self.assertEqual(control.label, "--")
        self.assertIsNone(control.events)

    def test_real_socket_event_read_does_not_spawn_or_sample(self):
        control, _, calls = self.controller()
        control.refresh()
        left, right = socket.socketpair()
        control.events = left
        self.addCleanup(control.close)
        self.addCleanup(right.close)
        right.sendall(Layout._packet(Layout.INPUT_EVENT, json.dumps({"change": "xkb_layout", "input": keyboard(1)})))
        with patch.object(adapter.subprocess, "run") as run, patch.object(adapter.battery, "read_battery") as charge:
            self.assertTrue(control.read_events())
            self.assertEqual(control.label, "ES")
            run.assert_not_called()
            charge.assert_not_called()

    def test_framed_reply_accepts_fragments_and_rejects_wrong_kind(self):
        payload = json.dumps([keyboard()])
        class Stream:
            def __init__(self, response):
                self.response = bytearray(response)
            def settimeout(self, value):
                self.timeout = value
            def recv(self, size):
                chunk = bytes(self.response[:1])
                del self.response[:1]
                return chunk
        import time
        stream = Stream(Layout._packet(100, payload))
        self.assertEqual(Layout._reply(stream, 100, time.monotonic() + 1), [keyboard()])
        with self.assertRaises(ValueError):
            Layout._reply(Stream(Layout._packet(0, payload)), 100, time.monotonic() + 1)
        with self.assertRaises(OSError):
            Layout._reply(Stream(b""), 100, time.monotonic() + 1)

    def test_cached_button_is_adjacent_to_clock_and_always_visible(self):
        control, _, calls = self.controller()
        control.refresh()
        view = adapter.StatusView(keyboard=control)
        traffic = Mock()
        traffic.sample.return_value = "fixture"
        view.update([{"name": "cpu_usage", "full_text": "2%"},
                     {"name": "tztime", "instance": "local", "full_text": "12:00"}], traffic)
        calls.clear()
        with patch.object(adapter.subprocess, "run") as run, patch.object(adapter.battery, "read_battery") as charge:
            for expanded in [False, True, False]:
                view.expanded = expanded
                frame = view.render()
                names = [block["name"] for block in frame]
                self.assertEqual(names.index("keyboard_layout") + 1, names.index("tztime"))
                self.assertEqual(frame[names.index("keyboard_layout")]["full_text"], "US")
            run.assert_not_called()
            charge.assert_not_called()
        self.assertEqual(calls, [])
        traffic.sample.assert_called_once()

    def test_click_allowlist_and_left_button(self):
        control = Mock()
        control.toggle.return_value = True
        view = adapter.StatusView(keyboard=control)
        event = dict(name="keyboard_layout", instance="us-es", button=1)
        self.assertTrue(adapter.handle_click(event, view))
        control.toggle.assert_called_once_with()
        control.reset_mock()
        for bad in [dict(event, button=True), dict(event, button=3),
                    dict(event, instance="us-es; exec bad"), dict(event, name="keyboard_layout; exec bad")]:
            self.assertFalse(adapter.handle_click(bad, view))
        control.toggle.assert_not_called()
        self.assertFalse(adapter.handle_click(event))

    def test_default_configuration_overrides_legacy_private_us(self):
        config = (ROOT / "config/sway/config").read_text()
        self.assertGreater(config.index("xkb_layout us,es"), config.index("include ~/.config/sway/local.conf"))
        self.assertNotIn("input type:keyboard xkb_layout us", (ROOT / "config/sway/local.conf.example").read_text())


if __name__ == "__main__":
    unittest.main()

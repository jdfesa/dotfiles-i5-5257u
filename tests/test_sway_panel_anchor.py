"""Verify popup geometry and IPC selection without a running compositor."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, call, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("panel_anchor", ROOT / "scripts/sway-panel-anchor.py")
anchor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anchor)


class PanelAnchorTests(unittest.TestCase):
    def test_btop_uses_a_standalone_terminal_with_the_dedicated_app_id(self):
        for default, available, options in (
                ("kitty", {"btop", "kitty", "foot"},
                 ["kitty", "--class=mbp-btop", "--override=tab_bar_min_tabs=2"]),
                ("foot", {"btop", "kitty", "foot"}, ["foot", "--app-id=mbp-btop"]),
                ("footclient", {"btop", "kitty", "foot"}, ["foot", "--app-id=mbp-btop"]),
                ("xterm", {"btop", "foot"}, ["foot", "--app-id=mbp-btop"])):
            with self.subTest(default=default, available=available), \
                    patch.object(anchor.os.path, "realpath", return_value=f"/usr/bin/{default}"), \
                    patch.object(anchor.shutil, "which",
                                 side_effect=lambda name: name if name in available else None):
                self.assertEqual(anchor.resource_monitor_command("mbp-btop"), [*options, "btop"])

    def test_btop_requires_the_package_and_a_supported_terminal(self):
        for available, message in ((set(), "btop is not installed"), ({"btop"}, "No supported terminal")):
            with self.subTest(available=available), \
                    patch.object(anchor.shutil, "which",
                                 side_effect=lambda name: name if name in available else None), \
                    self.assertRaisesRegex(RuntimeError, message):
                anchor.resource_monitor_command("mbp-btop")

    def test_resource_toggle_closes_only_its_dedicated_window(self):
        panel = dict(id=42, app_id="mbp-btop", type="floating_con")
        tree = dict(floating_nodes=[
            dict(id=20, app_id="kitty", type="floating_con", name="btop"),
            dict(id=21, app_id="local.mbp.Calendar", type="floating_con"), panel])
        with patch.dict(os.environ, SWAYSOCK="fixture"), \
                patch.object(anchor.socket, "socket"), patch.object(anchor, "IPC") as factory, \
                patch.object(anchor.subprocess, "Popen") as launch, \
                patch.object(anchor, "close_panel") as close:
            ipc = factory.return_value
            ipc.request.side_effect = [dict(success=True), tree]
            anchor.open_panel("resource-monitor")
            launch.assert_not_called()
            close.assert_called_once_with(ipc, panel)

    def test_locks_are_private_per_panel_and_never_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, XDG_RUNTIME_DIR=directory), \
                patch.object(anchor, "open_panel") as open_panel:
            for name in anchor.PANELS:
                anchor.toggle_panel(name, 1100, 28)
                lock = Path(directory) / f"mbp-panel-{name}.lock"
                self.assertEqual(lock.stat().st_mode & 0o777, 0o600)
                open_panel.assert_called_with(name, 1100, 28)
            lock.unlink()
            lock.symlink_to(Path(directory) / "untouched")
            with self.assertRaises(OSError):
                anchor.toggle_panel(name, 1100, 28)
            self.assertFalse((Path(directory) / "untouched").exists())

    def test_close_targets_only_its_id_and_waits_for_primary_exit(self):
        ipc = Mock()
        ipc.deadline = anchor.time.monotonic() + 1
        ipc.next_window.side_effect = [dict(change="close", container=dict(id=99)),
                                      dict(change="close", container=dict(id=42))]
        with patch.object(anchor.os, "pidfd_open", return_value=7) as pidfd, \
                patch.object(anchor.os, "close") as close, \
                patch.object(anchor.select, "select", return_value=([7], [], [])) as wait:
            anchor.close_panel(ipc, dict(id=42, pid=123))
        ipc.request.assert_called_once_with(0, "[con_id=42] kill")
        pidfd.assert_called_once_with(123)
        self.assertEqual(wait.call_args.args[:3], ([7], [], []))
        close.assert_called_once_with(7)

    def test_cli_rejects_partial_or_untrusted_geometry_and_actions(self):
        for args in (("other",), ("calendar", "12"),
                     ("calendar", "1; exec unwanted", "28"),
                     ("calendar", "-1", "28"), ("calendar", "12", "300")):
            with self.subTest(args=args), patch("sys.argv", ["anchor", *args]), \
                    patch.object(anchor, "toggle_panel") as toggle, \
                    patch("sys.stderr"), self.assertRaises(SystemExit):
                anchor.main()
            toggle.assert_not_called()

    def test_aligns_to_the_block_and_stays_on_screen(self):
        output = dict(x=200, y=-20, width=1280, height=800)
        panel = dict(width=320, height=140)
        self.assertEqual(anchor.target_position(output, panel, 600, 28), (640, 12))
        self.assertEqual(anchor.target_position(output, panel, 20, 28), (200, 12))
        self.assertEqual(anchor.target_position(output, panel, 1250, 28), (1160, 12))

    def test_selects_focused_or_only_compatible_output(self):
        internal = dict(active=True, focused=False, rect=dict(width=1280, height=800))
        external = dict(active=True, focused=True, rect=dict(width=960, height=800))
        outputs = [internal, external]
        self.assertEqual(anchor.choose_output(outputs, 500, 28), external["rect"])
        self.assertEqual(anchor.choose_output(outputs, 1100, 28), internal["rect"])
        self.assertIsNone(anchor.choose_output(outputs, 1300, 28))

    def test_moves_only_matching_floating_container_after_new_event(self):
        app_id = anchor.PANELS["calendar"][1]
        output = dict(x=0, y=0, width=1280, height=800)
        panel = dict(id=42, app_id=app_id, type="floating_con",
                     rect=dict(width=360, height=320), deco_rect=dict(height=20))
        other = dict(nodes=[dict(app_id=app_id, type="con", id=7)],
                     floating_nodes=[dict(app_id="other", type="floating_con", id=9)])
        tree = dict(floating_nodes=[panel])
        with patch.dict(os.environ, SWAYSOCK="fixture"), \
                patch.object(anchor.socket, "socket"), patch.object(anchor, "IPC") as factory, \
                patch.object(anchor.subprocess, "Popen") as launch:
            ipc = factory.return_value
            ipc.request.side_effect = [dict(success=True),
                                       [dict(active=True, focused=True, rect=output)],
                                       other, tree, [dict(success=True)]]
            ipc.next_window.side_effect = [dict(change="new", container=dict(app_id="other")),
                                          dict(change="focus", container=panel),
                                          dict(change="new", container=panel)]
            anchor.open_panel("calendar", 1200, 28)
            self.assertTrue(launch.call_args.args[0][0].endswith("/.local/bin/mbp-calendar"))
            self.assertEqual(ipc.request.call_args_list,
                             [call(2, '["window"]'), call(3), call(4), call(4),
                              call(0, "[con_id=42] move absolute position 920 32")])

    def test_existing_panel_closes_without_launching_or_moving(self):
        panel = dict(app_id=anchor.PANELS["calendar"][1], type="floating_con")
        with patch.dict(os.environ, SWAYSOCK="fixture"), \
                patch.object(anchor.socket, "socket"), patch.object(anchor, "IPC") as factory, \
                patch.object(anchor.subprocess, "Popen") as launch, \
                patch.object(anchor, "close_panel") as close:
            ipc = factory.return_value
            ipc.request.side_effect = [dict(success=True), [], panel]
            anchor.open_panel("calendar", 1200, 28)
            launch.assert_not_called()
            close.assert_called_once_with(ipc, panel)
            ipc.next_window.assert_not_called()
            self.assertEqual(ipc.request.call_count, 3)

    def test_failed_ipc_still_launches_once_without_hiding(self):
        for failure in (OSError("unavailable"), TimeoutError(), ValueError("bad reply")):
            with self.subTest(failure=failure), patch.dict(os.environ, SWAYSOCK="fixture"), \
                    patch.object(anchor.socket, "socket") as socket, \
                    patch.object(anchor.subprocess, "Popen") as launch:
                socket.return_value.__enter__.return_value.connect.side_effect = failure
                anchor.open_panel("screen-brightness-panel", 1100, 28)
                launch.assert_called_once()

    def test_failure_after_activation_never_launches_again(self):
        with patch.dict(os.environ, SWAYSOCK="fixture"), \
                patch.object(anchor.socket, "socket"), patch.object(anchor, "IPC") as factory, \
                patch.object(anchor.subprocess, "Popen") as launch:
            ipc = factory.return_value
            ipc.request.side_effect = [dict(success=True),
                                       [dict(active=True, focused=True,
                                             rect=dict(width=1280, height=800))], {}]
            ipc.next_window.side_effect = TimeoutError()
            anchor.open_panel("calendar", 1200, 28)
            launch.assert_called_once()

    def test_fragmented_ipc_and_interleaved_events(self):
        def packet(kind, value):
            payload = json.dumps(value).encode()
            return anchor.HEADER.pack(b"i3-ipc", len(payload), kind) + payload
        data = bytearray(packet(anchor.WINDOW_EVENT, dict(change="new")) +
                         packet(2, dict(success=True)))
        def receive(size):
            chunk = data[:min(3, size)]
            del data[:len(chunk)]
            return chunk
        stream = Mock()
        stream.recv.side_effect = receive
        ipc = anchor.IPC(stream)
        self.assertEqual(ipc.request(2, '["window"]'), dict(success=True))
        self.assertEqual(ipc.next_window(), dict(change="new"))

    def test_ipc_deadline_disconnect_and_oversize_are_bounded(self):
        for packet in (b"", anchor.HEADER.pack(b"i3-ipc", 4 * 1024 * 1024 + 1, 2),
                       anchor.HEADER.pack(b"badipc", 0, 2)):
            stream = Mock()
            stream.recv.return_value = packet
            with self.subTest(packet=packet), self.assertRaises((OSError, ValueError)):
                anchor.IPC(stream).receive()
        ipc = anchor.IPC(Mock())
        ipc.deadline = 0
        with self.assertRaises(TimeoutError):
            ipc.receive()
        ipc.stream.recv.assert_not_called()

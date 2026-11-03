#!/usr/bin/python3
"""Swaybar adapter based on i3-2310m; see licenses/i3-reference-MIT.txt."""
import html
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import struct
import subprocess
import sys
import time

_battery_spec = importlib.util.spec_from_file_location("battery", Path(__file__).resolve().with_name("sway-status.py"))
battery = importlib.util.module_from_spec(_battery_spec)
_battery_spec.loader.exec_module(battery)
WIRELESS = next((p.parent.name for p in sorted(Path("/sys/class/net").glob("*/wireless"))), "unavailable")
TEXT = "#cdd6f4"
RED = "#f38ba8"
YELLOW = "#f9e2af"
LAVENDER = "#b4befe"
GREEN = "#a6e3a1"
PEACH = "#fab387"
MUTED = "#7f849c"
ICON_FONT = "JetBrainsMono Nerd Font Propo 12"
BATTERY_FONT = "JetBrainsMono Nerd Font Mono 12"
# Material Design code points verified against Nerd Fonts v3.5.1.
BATTERY_LEVEL_ICONS = ("\U000f008e", "\U000f007a", "\U000f007b", "\U000f007c",
                       "\U000f007d", "\U000f007e", "\U000f007f", "\U000f0080",
                       "\U000f0081", "\U000f0082", "\U000f0079")
BATTERY_CHARGING_ICONS = ("\U000f089f", "\U000f089c", "\U000f0086", "\U000f0087",
                          "\U000f0088", "\U000f089d", "\U000f0089", "\U000f089e",
                          "\U000f008a", "\U000f008b", "\U000f0085")
BATTERY_UNKNOWN_ICON = "\U000f0091"
BATTERY_FULL_MARK = "\uf00c"
BATTERY_PENDING_MARK = "\uf04c"
WEATHER_ICONS = {"☀": "\uf185", "☾": "\uf186", "☁": "\uf0c2", "≋": "\ue313",
                 "☂": "\ue318", "❄": "\U000f0598", "ϟ": "\U000f0593", "?": "\ue370"}
SECONDARY_BLOCKS = frozenset(("traffic", "memory", "cpu_usage", "cpu_temperature", "disk_info"))


def labeled(icon, text, color):
    return f'<span font_desc="{ICON_FONT}" foreground="{color}">{icon}</span> {html.escape(text)}'


def format_weather(text):
    """Restyle cached text only; preserve stale/unavailable markers and units."""
    match = re.fullmatch(r"(~?)([☀☾☁≋☂❄ϟ?])\s+(.+)", text)
    if match:
        return match[1] + labeled(WEATHER_ICONS[match[2]], match[3], TEXT)
    return html.escape(text)


def format_battery(charge):
    """Pure presentation of UPower's validated charge/state; never read hardware."""
    valid = (isinstance(charge, (tuple, list)) and len(charge) == 2 and
             type(charge[0]) in (int, float) and 0 <= charge[0] <= 100 and
             math.isfinite(charge[0]))
    icon, text, icon_color, text_color = BATTERY_UNKNOWN_ICON, "--%", MUTED, MUTED
    if valid:
        percentage, state = charge
        level = int(percentage // 10)
        text, text_color = f"{percentage:.0f}%", TEXT
        if state == "charging":
            icon, icon_color = BATTERY_CHARGING_ICONS[level], GREEN
        elif state == "fully-charged":
            icon, icon_color = BATTERY_LEVEL_ICONS[-1] + " " + BATTERY_FULL_MARK, GREEN
        elif state in ("pending-charge", "pending-discharge"):
            icon, icon_color = BATTERY_LEVEL_ICONS[level] + " " + BATTERY_PENDING_MARK, YELLOW
        elif state in ("discharging", "empty"):
            icon = BATTERY_LEVEL_ICONS[level]
            icon_color = RED if percentage <= 20 or state == "empty" else PEACH if percentage <= 40 else GREEN
            if icon_color == RED:
                text_color = RED
    return (f'<span font_desc="{BATTERY_FONT}" foreground="{icon_color}">{icon}</span> {text}',
            text_color)


def notify_low_battery(level):
    try:
        subprocess.run(["notify-send", "-a", "Battery", "-u",
                        "critical" if level == 2 else "normal", "Low battery",
                        "Save your work and connect the charger."], timeout=3, check=False)
    except (OSError, subprocess.SubprocessError):
        # A stopped notification service must never take down the status bar.
        return False
    return True


class Traffic:
    """Two sysfs reads per existing status tick; no socket/polling daemon."""
    def __init__(self, root=None, clock=time.monotonic):
        root = Path("/sys/class/net") / WIRELESS / "statistics" if root is None else root
        self.root, self.clock, self.previous = root, clock, None

    @staticmethod
    def rate(value):
        if value >= 1024 * 1024:
            return f"{value / (1024 * 1024):.1f}M"
        return f"{value / 1024:.0f}K"

    def sample(self):
        try:
            now = self.clock()
            received = int((self.root / "rx_bytes").read_text())
            sent = int((self.root / "tx_bytes").read_text())
            if min(received, sent) < 0:
                raise ValueError("invalid counters")
        except (OSError, ValueError):
            self.previous = None
            return "↑-- ↓--"
        previous, self.previous = self.previous, (now, received, sent)
        if previous is None or now <= previous[0] or received < previous[1] or sent < previous[2]:
            return "↑-- ↓--"
        seconds = now - previous[0]
        return f"↑{self.rate((sent - previous[2]) / seconds)} ↓{self.rate((received - previous[1]) / seconds)}/s"


def adapt_status(blocks, traffic=None, charge=None):
    if not any(block.get("name") == "volume" for block in blocks):
        index = next((i for i, block in enumerate(blocks) if block.get("name") == "wireless"), len(blocks))
        blocks.insert(index, {"name": "volume", "instance": "default.Master.0", "full_text": "unavailable"})
    if not any(block.get("name") == "battery" for block in blocks):
        index = next((i for i, block in enumerate(blocks) if block.get("name") == "tztime"), len(blocks))
        blocks.insert(index, {"name": "battery", "instance": "upower", "full_text": ""})
    for block in blocks:
        name, text = block.get("name"), block.get("full_text", "")
        if name == "wireless" and block.get("instance") in (WIRELESS, "_first_"):
            quality = re.fullmatch(r"\s*(\d{1,3})%\s*", text)
            value = min(100, int(quality[1])) if quality else None
            level = max(1, min(4, (value + 24) // 25)) if value is not None else 0
            block["full_text"] = f'<span font_desc="BGH Status Icons 12">{chr(0xE000 + level)}</span>'
            block["min_width"], block["align"] = 28, "center"
            block["color"] = RED if value is None or value <= 25 else YELLOW if value <= 50 else "#f2cdcd"
        elif name == "cpu_usage":
            block["full_text"] = labeled("\uf2db", text, YELLOW)
        elif name == "cpu_temperature":
            block["full_text"] = labeled("\U000f050f", text, "#fab387")
        elif name == "memory":
            block["full_text"] = labeled("\uefc5", text, RED)
        elif name == "disk_info":
            block["full_text"] = labeled("\uf0a0", text.replace(" GB", "G"), "#a6e3a1")
        elif name == "volume":
            volume = re.fullmatch(r"(muted )?(\d+)%", text.strip())
            if volume:
                icon = "\ueee8" if volume[1] else "\uf028" if int(volume[2]) > 50 else "\uf027" if int(volume[2]) else "\uf026"
                block["full_text"] = f'<span font_desc="{ICON_FONT}" foreground="{YELLOW}">{icon}</span>'
            else:
                block["full_text"] = labeled("\ueee8", "No audio", "#7f849c")
            block["min_width"], block["align"] = 24, "center"
        elif name == "read_file" and block.get("instance", "").endswith("/weather.txt"):
            block["full_text"] = format_weather(text)
        elif name == "read_file" and block.get("instance", "").endswith("/updates.txt"):
            block["full_text"] = labeled("\U000f03d7", text, "#f5c2e7")
        elif name == "battery":
            block["full_text"], block["color"] = format_battery(charge)
        elif name == "tztime":
            block["color"] = LAVENDER
        block.setdefault("color", TEXT)
        block["markup"] = "pango"
        block["short_text"] = block["full_text"]
        block["separator"] = False
        block["separator_block_width"] = 4 if name == "volume" else 12
    if traffic is not None:
        blocks.insert(1, {"name": "traffic", "instance": WIRELESS, "full_text": traffic.sample(),
                          "color": "#7f849c", "separator": False, "separator_block_width": 12})
    return blocks



class KeyboardLayout:
    """Sway input events on the existing event loop: no polling or subprocess."""
    HEADER = struct.Struct("=6sII")
    MAX_PAYLOAD = 1024 * 1024
    INPUT_EVENT = 0x80000015
    NAMES = ["English (US)", "Spanish"]

    def __init__(self, path=None, request=None):
        self.path = path if path is not None else os.environ.get("SWAYSOCK")
        self.request = request if request is not None else self._request
        self.inputs = {}
        self.events = None
        self.buffer = bytearray()

    @property
    def label(self):
        values = set(self.inputs.values())
        return "US" if values == {0} else "ES" if values == {1} else "--"

    @staticmethod
    def _timeout(stream, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Sway IPC deadline exceeded")
        stream.settimeout(remaining)

    def _connect(self, deadline):
        if not self.path:
            raise OSError("No Sway IPC socket")
        stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self._timeout(stream, deadline)
            stream.connect(self.path)
        except BaseException:
            stream.close()
            raise
        return stream

    @classmethod
    def _packet(cls, kind, payload):
        data = payload.encode("utf-8")
        if len(data) > cls.MAX_PAYLOAD:
            raise ValueError("Oversized Sway IPC request")
        return cls.HEADER.pack(b"i3-ipc", len(data), kind) + data

    @classmethod
    def _read_exact(cls, stream, size, deadline):
        data = bytearray()
        while len(data) < size:
            cls._timeout(stream, deadline)
            chunk = stream.recv(size - len(data))
            if not chunk:
                raise OSError("Sway IPC disconnected")
            data.extend(chunk)
        return bytes(data)

    @classmethod
    def _reply(cls, stream, kind, deadline):
        magic, size, response = cls.HEADER.unpack(cls._read_exact(stream, cls.HEADER.size, deadline))
        if magic != b"i3-ipc" or size > cls.MAX_PAYLOAD or response != kind:
            raise ValueError("Invalid Sway IPC reply")
        return json.loads(cls._read_exact(stream, size, deadline))

    def _request(self, kind, payload):
        deadline = time.monotonic() + 1
        with self._connect(deadline) as stream:
            self._timeout(stream, deadline)
            stream.sendall(self._packet(kind, payload))
            return self._reply(stream, kind, deadline)

    @classmethod
    def _index(cls, item):
        index = item.get("xkb_active_layout_index")
        if item.get("xkb_layout_names") == cls.NAMES and type(index) is int and index in (0, 1):
            return index
        return None

    def refresh(self):
        items = self.request(100, "")
        if not isinstance(items, list) or len(items) > 1024:
            raise ValueError("Invalid Sway keyboard list")
        keyboards = {}
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Invalid Sway input")
            if item.get("type") == "keyboard":
                identifier = item.get("identifier")
                if not isinstance(identifier, str) or not identifier or len(identifier) > 512:
                    raise ValueError("Invalid Sway keyboard identifier")
                keyboards[identifier] = self._index(item)
        self.inputs = keyboards

    def start(self, listen=True):
        try:
            if listen:
                deadline = time.monotonic() + 1
                self.events = self._connect(deadline)
                self._timeout(self.events, deadline)
                self.events.sendall(self._packet(2, '["input"]'))
                if self._reply(self.events, 2, deadline) != {"success": True}:
                    raise ValueError("Sway input subscription refused")
                self.events.setblocking(False)
            self.refresh()
        except (OSError, ValueError):
            self.inputs.clear()
            self.close()

    def toggle(self):
        try:
            # Read the actual state before choosing a fixed index; do not assume US.
            self.refresh()
            if not self.inputs or None in self.inputs.values():
                raise ValueError("US/ES are not configured for every keyboard")
            target = 1 if self.label == "US" else 0
            reply = self.request(0, f"input type:keyboard xkb_switch_layout {target}")
            if not isinstance(reply, list) or not reply or not all(
                    isinstance(item, dict) and item.get("success") is True for item in reply):
                raise ValueError("Sway keyboard layout change failed")
            self.refresh()
        except (OSError, ValueError):
            try:
                self.refresh()
            except (OSError, ValueError):
                self.inputs.clear()
            print("Could not change keyboard layout", file=sys.stderr)
        return True

    def feed(self, chunk):
        self.buffer.extend(chunk)
        while len(self.buffer) >= self.HEADER.size:
            magic, size, kind = self.HEADER.unpack(self.buffer[:self.HEADER.size])
            if magic != b"i3-ipc" or size > self.MAX_PAYLOAD:
                raise ValueError("Invalid Sway input event")
            end = self.HEADER.size + size
            if len(self.buffer) < end:
                break
            data = bytes(self.buffer[self.HEADER.size:end])
            del self.buffer[:end]
            if kind != self.INPUT_EVENT:
                continue
            event = json.loads(data)
            if not isinstance(event, dict):
                raise ValueError("Invalid Sway input event payload")
            item = event.get("input")
            if not isinstance(item, dict) or item.get("type") != "keyboard":
                continue
            identifier = item.get("identifier")
            if not isinstance(identifier, str) or not identifier or len(identifier) > 512:
                raise ValueError("Invalid Sway input event identifier")
            if event.get("change") == "removed":
                self.inputs.pop(identifier, None)
            elif event.get("change") in ("added", "xkb_keymap", "xkb_layout"):
                self.inputs[identifier] = self._index(item)

    def read_events(self):
        previous = self.label
        try:
            chunk = self.events.recv(65536)
            if not chunk:
                raise OSError("Sway input events disconnected")
            self.feed(chunk)
        except BlockingIOError:
            return False
        except (OSError, ValueError):
            self.inputs.clear()
            self.close()
        return self.label != previous

    def block(self):
        label = self.label
        return {"name": "keyboard_layout", "instance": "us-es",
                "full_text": label, "short_text": label,
                "color": LAVENDER if label != "--" else MUTED,
                "min_width": 28, "align": "center", "markup": "pango",
                "separator": False, "separator_block_width": 12}

    def close(self):
        if self.events is not None:
            self.events.close()
            self.events = None
        self.buffer.clear()


class StatusView:
    """Format only on producer ticks; toggle a cached frame without any I/O."""
    def __init__(self, expanded=False, keyboard=None):
        self.keyboard = keyboard
        self.expanded = expanded
        self.snapshot = None

    def update(self, blocks, traffic=None, charge=None):
        self.snapshot = adapt_status([dict(block) for block in blocks], traffic, charge)
        return self.render()

    def render(self):
        if self.snapshot is None:
            return None
        blocks = [block for block in self.snapshot
                  if self.expanded or block.get("name") not in SECONDARY_BLOCKS
                  or block.get("urgent") is True]
        index = next((i for i, block in enumerate(blocks)
                      if (block.get("name") == "read_file" and
                          block.get("instance", "").endswith("/updates.txt")) or
                      block.get("name") in ("volume", "wireless", "battery", "tztime")), len(blocks))
        icon = "\uf053" if self.expanded else "\uf054"
        blocks.insert(index, {"name": "stats_toggle", "instance": "secondary",
                              "full_text": icon, "short_text": icon, "color": LAVENDER,
                              "min_width": 28, "align": "center", "markup": "pango",
                              "separator": False, "separator_block_width": 12})
        if self.keyboard is not None:
            clock = next((i for i, block in enumerate(blocks) if block.get("name") == "tztime"), len(blocks))
            blocks.insert(clock, self.keyboard.block())
        return blocks


def handle_click(event, view=None):
    if type(event.get("button")) is not int or event["button"] != 1:
        return False
    if event.get("name") == "keyboard_layout" and event.get("instance") == "us-es":
        return view.keyboard.toggle() if view is not None and view.keyboard is not None else False
    if event.get("name") == "stats_toggle" and event.get("instance") == "secondary":
        if view is not None:
            view.expanded = not view.expanded
            return True
        return False
    helper = None
    if event.get("name") == "wireless" and event.get("instance") in (WIRELESS, "_first_"):
        helper = "networks"
    elif event.get("name") == "volume" and event.get("instance") == "default.Master.0":
        helper = "audio"
    elif event.get("name") == "read_file" and event.get("instance") == str(Path.home() / ".cache/mbp-sway/updates.txt"):
        helper = "updates"
    elif event.get("name") == "tztime" and event.get("instance") == "local":
        helper = "calendar"
    if helper:
        # Only allowlisted helper names; never interpret event strings/SSID.
        subprocess.run(["swaymsg", f"exec ~/.local/bin/mbp-sway-tools {helper}"],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=3, check=True)
    return False


def main(run_once=False):
    source = Path(__file__).resolve().with_name("status-bar.sh")
    child = subprocess.Popen([str(source)] + (["--run-once"] if run_once else []),
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, bufsize=0)
    def terminate(*_):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    # i3bar signals the entire status_command process group, including its
    # /bin/sh launcher and i3status. Keep the protocol defaults (SIGSTOP /
    # SIGCONT): custom USR signals kill other group members, not just Python.
    print(json.dumps({"version": 1, "click_events": True}), flush=True)
    print("[", flush=True)
    poller = selectors.DefaultSelector()
    buffers = {}
    poller.register(child.stdout, selectors.EVENT_READ, "status")
    if not run_once:
        poller.register(sys.stdin, selectors.EVENT_READ, "click")
    first = True
    keyboard = KeyboardLayout()
    keyboard.start(listen=not run_once)
    if keyboard.events is not None:
        poller.register(keyboard.events, selectors.EVENT_READ, "keyboard")
    view = StatusView(keyboard=keyboard)
    traffic = Traffic()
    previous_warning = 0

    def emit(blocks):
        nonlocal first
        print(("" if first else ",") + json.dumps(blocks, ensure_ascii=False), flush=True)
        first = False

    try:
        while True:
            for key, _ in poller.select():
                if key.data == "keyboard":
                    changed = keyboard.read_events()
                    if keyboard.events is None:
                        poller.unregister(key.fd)
                    if changed:
                        frame = view.render()
                        if frame is not None:
                            emit(frame)
                    continue
                fd = key.fd
                chunk = os.read(fd, 65536)
                if not chunk:
                    if key.data == "status":
                        return child.wait()
                    poller.unregister(key.fileobj)
                    continue
                buffers[fd] = buffers.get(fd, b"") + chunk
                while b"\n" in buffers[fd]:
                    line, buffers[fd] = buffers[fd].split(b"\n", 1)
                    line = line.strip().lstrip(b",").strip()
                    if line in (b"", b"[", b"]"):
                        continue
                    try:
                        value = json.loads(line)
                    except (ValueError, UnicodeError):
                        continue
                    if key.data == "click" and isinstance(value, dict):
                        try:
                            if handle_click(value, view):
                                frame = view.render()
                                if frame is not None:
                                    emit(frame)
                        except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                            print("Could not open status panel", file=sys.stderr)
                    elif key.data == "status" and isinstance(value, list):
                        charge = battery.read_battery()
                        level = battery.warning_level(charge)
                        if not run_once and level > previous_warning:
                            notify_low_battery(level)
                        previous_warning = level
                        emit(view.update(value, traffic, charge))
    finally:
        poller.close()
        keyboard.close()
        if child.poll() is None:
            child.send_signal(signal.SIGCONT)
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    sys.exit(main("--run-once" in sys.argv[1:]))

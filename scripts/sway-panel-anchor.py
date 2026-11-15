#!/usr/bin/python3
"""Toggle one allowlisted panel and anchor it on its Sway window event."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import shutil
import socket
import stat
import struct
import subprocess
import time

PANELS = {
    "calendar": ("mbp-calendar", "local.mbp.Calendar"),
    "resource-monitor": ("btop", "mbp-btop"),
    "screen-brightness-panel": ("mbp-screen-brightness", "local.mbp.ScreenBrightness"),
}
GAP = 4
HEADER = struct.Struct("=6sII")
WINDOW_EVENT = 0x80000003


class IPC:
    """One bounded, short-lived connection; never poll the compositor."""
    def __init__(self, stream):
        self.stream = stream
        self.deadline = time.monotonic() + 1.5
        self.events = []

    def read_exact(self, size):
        data = bytearray()
        while len(data) < size:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Panel IPC deadline exceeded")
            self.stream.settimeout(remaining)
            chunk = self.stream.recv(size - len(data))
            if not chunk:
                raise OSError("Sway IPC disconnected")
            data.extend(chunk)
        return data

    def receive(self):
        magic, size, kind = HEADER.unpack(self.read_exact(HEADER.size))
        if magic != b"i3-ipc" or size > 4 * 1024 * 1024:
            raise ValueError("Invalid Sway IPC packet")
        return kind, json.loads(self.read_exact(size))

    def request(self, kind, payload=""):
        data = payload.encode()
        self.stream.sendall(HEADER.pack(b"i3-ipc", len(data), kind) + data)
        while True:
            response, value = self.receive()
            if response == kind:
                return value
            if response == WINDOW_EVENT:
                self.events.append(value)

    def next_window(self):
        if self.events:
            return self.events.pop(0)
        while True:
            kind, value = self.receive()
            if kind == WINDOW_EVENT:
                return value


def find_panel(node, app_id):
    if node.get("app_id") == app_id and node.get("type") == "floating_con":
        return node
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        panel = find_panel(child, app_id)
        if panel is not None:
            return panel
    return None


def choose_output(outputs, anchor_x, bar_bottom):
    # Swaybar sends output-local logical coordinates, but no output name.
    possible = [o for o in outputs if o["active"] and anchor_x < o["rect"]["width"]
                and bar_bottom < o["rect"]["height"]]
    return next((o["rect"] for o in possible if o["focused"]),
                possible[0]["rect"] if len(possible) == 1 else None)


def target_position(output, panel, anchor_x, bar_bottom):
    left, top = output["x"], output["y"]
    right = left + output["width"]
    bottom = top + output["height"]
    x = left + anchor_x - panel["width"] // 2
    y = top + bar_bottom + GAP
    return (max(left, min(x, right - panel["width"])),
            max(top, min(y, bottom - panel["height"])))


def close_panel(ipc, panel):
    """Wait for this primary to exit before another click can reopen it."""
    pidfd = None
    try:
        pid = panel.get("pid")
        if type(pid) is int and pid > 0:
            try:
                pidfd = os.pidfd_open(pid)
            except OSError:
                pass
        container = int(panel["id"])
        ipc.request(0, f"[con_id={container}] kill")
        while True:
            event = ipc.next_window()
            if (event.get("change") == "close" and
                    event.get("container", {}).get("id") == container):
                break
        if pidfd is not None:
            select.select([pidfd], [], [], max(0, ipc.deadline - time.monotonic()))
    finally:
        if pidfd is not None:
            os.close(pidfd)


def resource_monitor_command(app_id):
    """Use a standalone Wayland terminal with a panel-specific app ID."""
    btop = shutil.which("btop")
    if btop is None:
        raise RuntimeError("btop is not installed.")

    # Respect a supported Debian default; otherwise use the Sway profile's Kitty.
    default = os.path.realpath("/usr/bin/x-terminal-emulator").rsplit("/", 1)[-1]
    terminals = ("foot", "kitty") if default in ("foot", "footclient") else ("kitty", "foot")
    for name in terminals:
        terminal = shutil.which(name)
        if terminal is not None:
            if name == "kitty":
                return [terminal, f"--class={app_id}", "--override=tab_bar_min_tabs=2", btop]
            return [terminal, f"--app-id={app_id}", btop]
    raise RuntimeError("No supported terminal found (Kitty or Foot).")


def open_panel(name, anchor_x=None, bar_bottom=None):
    executable, app_id = PANELS[name]
    launched = False
    existing = None

    def launch():
        nonlocal launched
        command = (resource_monitor_command(app_id) if name == "resource-monitor"
                   else [str(Path.home() / ".local/bin" / executable)])
        subprocess.Popen(command,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        launched = True

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(0.4)
            stream.connect(os.environ["SWAYSOCK"])
            ipc = IPC(stream)
            # Subscribe before activation: even a very fast map cannot be missed.
            if not ipc.request(2, '["window"]').get("success"):
                raise ValueError("Sway window subscription failed")
            output = (choose_output(ipc.request(3), anchor_x, bar_bottom)
                      if anchor_x is not None else None)
            existing = find_panel(ipc.request(4), app_id)
            if existing is not None:
                close_panel(ipc, existing)
                return
            launch()
            while True:
                event = ipc.next_window()
                if (event.get("change") != "new" or
                        event.get("container", {}).get("app_id") != app_id):
                    continue
                if output is None:
                    return
                # 'new' precedes for_window in Sway 1.10.1: get the final size.
                panel = find_panel(ipc.request(4), app_id)
                if panel is None:
                    return  # A second activation or Escape already closed it.
                size = dict(panel["rect"])
                size["height"] += panel.get("deco_rect", {}).get("height", 0)
                x, y = target_position(output, size, anchor_x, bar_bottom)
                container = int(panel["id"])
                ipc.request(0, f"[con_id={container}] move absolute position {x} {y}")
                return
    except (KeyError, OSError, ValueError):
        # Never hide the window; direct/failed IPC launches remain usable.
        # A failed close must not turn into an accidental reopening.
        if not launched and existing is None:
            launch()


def toggle_panel(name, anchor_x=None, bar_bottom=None):
    # One lock per allowlisted panel, shared by anchored and direct helper calls.
    # Blocking flock sleeps in the kernel; no retry loop or resident process.
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        return open_panel(name, anchor_x, bar_bottom)
    path = Path(runtime) / f"mbp-panel-{name}.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "rb") as lock:
        info = os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise OSError("Unsafe panel lock")
        fcntl.flock(lock, fcntl.LOCK_EX)
        open_panel(name, anchor_x, bar_bottom)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel", choices=PANELS)
    parser.add_argument("anchor_x", type=int, nargs="?")
    parser.add_argument("bar_bottom", type=int, nargs="?")
    args = parser.parse_args()
    if ((args.anchor_x is None) != (args.bar_bottom is None) or
            args.anchor_x is not None and
            (not 0 <= args.anchor_x <= 32767 or not 1 <= args.bar_bottom <= 256)):
        parser.error("Invalid Swaybar coordinates.")
    try:
        toggle_panel(args.panel, args.anchor_x, args.bar_bottom)
    except RuntimeError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()

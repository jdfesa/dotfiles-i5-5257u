#!/usr/bin/env python3
"""Small text status, UPower's charge (not BAT0/capacity), 30-second refresh."""
import argparse
import datetime
import os
import re
import subprocess
import time


def parse_battery(text):
    percentage = re.search(r"^\s*percentage:\s*([\d.]+)%", text, re.M)
    state = re.search(r"^\s*state:\s*(\S+)", text, re.M)
    if not percentage or not state:
        return None
    try:
        value = float(percentage.group(1))
    except ValueError:
        return None
    if not 0 <= value <= 100:
        return None
    return value, state.group(1)


def read_battery():
    try:
        result = subprocess.run(
            ["upower", "-i", "/org/freedesktop/UPower/devices/DisplayDevice"],
            capture_output=True, text=True, timeout=5, check=True,
            env={**os.environ, "LC_ALL": "C"})
        return parse_battery(result.stdout)
    except (OSError, subprocess.SubprocessError):
        return None


def warning_level(battery):
    if battery is None or battery[1] != "discharging":
        return 0
    return 2 if battery[0] <= 10 else 1 if battery[0] <= 20 else 0


def format_status(battery):
    if battery is None:
        status = "Battery unavailable"
    else:
        percentage, state = battery
        label = {"charging": "Charging", "discharging": "Battery",
                 "fully-charged": "Full", "pending-charge": "Plugged"}.get(state, "Battery")
        status = f"{label} {percentage:.0f}%"
    return f"{status} | {datetime.datetime.now():%Y-%m-%d %H:%M}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Print once, without notifications")
    args = parser.parse_args()
    previous_level = 0
    while True:
        battery = read_battery()
        print(format_status(battery), flush=True)
        if args.once:
            return
        level = warning_level(battery)
        if level > previous_level:
            try:
                subprocess.run(["notify-send", "-a", "Battery", "-u",
                                "critical" if level == 2 else "normal",
                                "Low battery", "Save your work and connect the charger."],
                               timeout=5, check=False, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            except (OSError, subprocess.SubprocessError):
                pass
        previous_level = level
        time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass

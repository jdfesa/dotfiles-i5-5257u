#!/usr/bin/python3
"""On-demand lid guard for normal systemd suspend on the MacBookPro12,1."""
import os
from pathlib import Path
import re
import subprocess
import sys
import time

LOGIN = "org.freedesktop.login1"
MANAGER = LOGIN + ".Manager"
LOGIN_PATH = "/org/freedesktop/login1"
DBUS = "org.freedesktop.DBus"
PROPERTIES = DBUS + ".Properties"
DBUS_PATH = "/org/freedesktop/DBus"
ACPI_LID = Path("/proc/acpi/button/lid/LID0/state")
# Linux UAPI clock 9 (include/uapi/linux/time.h); Python does not always export it.
CLOCK_BOOTTIME_ALARM = getattr(time, "CLOCK_BOOTTIME_ALARM", 9)
SD_LOGIND_ROOT_CHECK_INHIBITORS = 1
RESUME_SETTLE_MS = 3000


def log(message):
    print(message, flush=True)


def settings(env):
    mode = env.get("MBP_LID_MODE", "dry-run")
    value = env.get("MBP_LID_SECONDS", "1200")
    if mode not in ("dry-run", "poweroff"):
        raise ValueError("MBP_LID_MODE must be dry-run or poweroff.")
    if not re.fullmatch(r"[0-9]{2,5}", value) or not 30 <= int(value) <= 86400:
        raise ValueError("MBP_LID_SECONDS must be an integer from 30 to 86400.")
    return mode, int(value)


def physical_lid_closed(path=ACPI_LID):
    try:
        return path.read_text(encoding="ascii").split() == ["state:", "closed"]
    except (OSError, UnicodeError):
        return False


def lid_allows_action(props, hardware_closed, inhibitors, preparing):
    """Unknown or conflicting lid/dock/power policy information is unsafe."""
    if (not hardware_closed or props.get("LidClosed") is not True
            or props.get("Docked") is not False
            or props.get("PreparingForSleep") is not preparing
            or props.get("HandleLidSwitch") != "suspend"):
        return False
    on_ac = props.get("OnExternalPower")
    if on_ac is not False and (on_ac is not True
                              or props.get("HandleLidSwitchExternalPower") not in ("", "suspend")):
        return False
    return not any("handle-lid-switch" in what.split(":") for what, *_ in inhibitors)


def lid_signal_cancels(interface, changed, invalidated):
    return interface == MANAGER and (
        "LidClosed" in invalidated
        or ("LidClosed" in changed and changed["LidClosed"] is not True))


def boot_and_active():
    return time.clock_gettime(time.CLOCK_BOOTTIME), time.monotonic()


def slept_since(start, end):
    # The boot clock covers suspend; CLOCK_MONOTONIC does not.
    return (end[0] - start[0]) - (end[1] - start[1]) >= 0.1


def arm_alarm(seconds):
    fd = os.timerfd_create(CLOCK_BOOTTIME_ALARM, flags=os.TFD_CLOEXEC | os.TFD_NONBLOCK)
    try:
        os.timerfd_settime(fd, initial=seconds)
    except OSError:
        os.close(fd)
        raise
    return fd


def notify_ready():
    subprocess.run(["/usr/bin/systemd-notify", "--ready"], check=True, timeout=2)


class Logind:
    def __init__(self, Gio, GLib):
        self.Gio, self.GLib = Gio, GLib
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.owner = self.call(DBUS, DBUS_PATH, DBUS, "GetNameOwner",
                               self.variant("(s)", LOGIN), "(s)")[0]

    def variant(self, signature, *args):
        return self.GLib.Variant(signature, args)

    def call(self, name, path, interface, method, args, signature):
        return self.bus.call_sync(name, path, interface, method, args,
                                  self.GLib.VariantType.new(signature),
                                  self.Gio.DBusCallFlags.NO_AUTO_START, 1000, None).unpack()

    def lid_allows(self, *, preparing):
        if not physical_lid_closed():
            return False
        inhibitors, = self.call(self.owner, LOGIN_PATH, MANAGER, "ListInhibitors",
                                None, "(a(ssssuu))")
        props, = self.call(self.owner, LOGIN_PATH, PROPERTIES, "GetAll",
                           self.variant("(s)", MANAGER), "(a{sv})")
        return lid_allows_action(props, physical_lid_closed(), inhibitors, preparing)

    def poweroff(self):
        # No interactive/policy override, no fallback to direct poweroff.target.
        self.call(self.owner, LOGIN_PATH, MANAGER, "PowerOffWithFlags",
                  self.variant("(t)", SD_LOGIND_ROOT_CHECK_INHIBITORS), "()")


def run_guard(mode, seconds, Gio, GLib):
    login = Logind(Gio, GLib)
    loop = GLib.MainLoop()
    fd = None
    cancelled = False

    def cancel(reason):
        nonlocal cancelled
        cancelled = True
        log(reason)
        loop.quit()

    def properties(_, sender, path, interface, signal, parameters, *unused):
        if sender == login.owner and lid_signal_cancels(*parameters.unpack()):
            cancel("Lid opened or its state became unknown; shutdown cancelled.")

    def owner_changed(_, sender, path, interface, signal, parameters, *unused):
        name, old, new = parameters.unpack()
        if name == LOGIN and new != login.owner:
            cancel("logind changed owner; shutdown cancelled.")

    def confirm():
        try:
            if cancelled:
                return GLib.SOURCE_REMOVE
            if not slept_since(start, boot_and_active()) or not login.lid_allows(preparing=False):
                log("No confirmed suspend with the lid still closed; shutdown cancelled.")
            elif mode == "dry-run":
                log("Dry run: lid stayed closed; would request a normal poweroff.")
            else:
                login.poweroff()
                log("Lid deadline reached; normal poweroff requested.")
        except (OSError, GLib.Error) as error:
            log(f"Could not request a normal poweroff: {error}")
        finally:
            loop.quit()
        return GLib.SOURCE_REMOVE

    def timer_ready(fd, condition):
        try:
            if condition != GLib.IOCondition.IN or len(os.read(fd, 8)) != 8:
                raise OSError("Wake timer did not report expiry.")
            # Give queued lid events and logind's resume processing time to settle.
            GLib.timeout_add(RESUME_SETTLE_MS, confirm, priority=GLib.PRIORITY_LOW)
        except OSError as error:
            cancel(f"Wake timer failed; shutdown cancelled: {error}")
        return GLib.SOURCE_REMOVE

    subscriptions = [
        login.bus.signal_subscribe(DBUS, DBUS, "NameOwnerChanged", DBUS_PATH, LOGIN,
                                   Gio.DBusSignalFlags.NONE, owner_changed),
        login.bus.signal_subscribe(login.owner, PROPERTIES, "PropertiesChanged",
                                   LOGIN_PATH, MANAGER, Gio.DBusSignalFlags.NONE, properties),
    ]
    login.bus.connect("closed", lambda *_: cancel("System bus closed; shutdown cancelled."))
    try:
        if not login.lid_allows(preparing=True):
            log("No eligible closed lid on entry to suspend; no shutdown timer.")
            notify_ready()
            return
        start = boot_and_active()
        fd = arm_alarm(seconds)
        GLib.unix_fd_add_full(GLib.PRIORITY_DEFAULT, fd,
                              GLib.IOCondition.IN | GLib.IOCondition.ERR | GLib.IOCondition.HUP,
                              timer_ready)
        notify_ready()
        log(f"Lid guard armed for {seconds} seconds ({mode}).")
        loop.run()
    finally:
        for subscription in subscriptions:
            login.bus.signal_unsubscribe(subscription)
        if fd is not None:
            os.close(fd)


def main():
    if os.geteuid() != 0 or not os.environ.get("NOTIFY_SOCKET"):
        print("Run only as the installed system service.", file=sys.stderr)
        return 1
    try:
        from gi.repository import Gio, GLib
        mode, seconds = settings(os.environ)
        try:
            run_guard(mode, seconds, Gio, GLib)
        except GLib.Error as error:
            raise RuntimeError(str(error)) from error
    except (OSError, RuntimeError, ValueError, ImportError, subprocess.SubprocessError) as error:
        print(f"Lid guard unavailable; no automatic shutdown: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

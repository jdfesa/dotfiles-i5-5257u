#!/usr/bin/python3
"""Read-only snapshot of the system battery; no timer or background service."""
import math
import os
import sys
import time

APP_ID = "local.mbp.BatteryDetails"
SERVICE = "org.freedesktop.UPower"
ROOT = "/org/freedesktop/UPower"
DEVICE = SERVICE + ".Device"
UNAVAILABLE = "Unavailable"
STATES = {
    1: "Charging", 2: "Discharging", 3: "Empty", 4: "Fully charged",
    5: "Pending charge", 6: "Pending discharge",
}
STYLE = b"""
#mbp-battery-details {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
#battery-details-title {
    color: #cdd6f4;
    font-size: 15px;
    font-weight: bold;
}
#mbp-battery-details .snapshot-label {
    color: #a6adc8;
}
#mbp-battery-details separator {
    background-color: #313244;
}
"""


def system_battery(paths, get_properties):
    for path in sorted(paths):
        props = get_properties(path)
        if (props.get("Type") == 2 and props.get("PowerSupply") is True
                and props.get("IsPresent") is True):
            return props
    return None


def read_snapshot(Gio, GLib):
    """One bounded read of device metadata from the existing system service."""
    deadline = time.monotonic() + 0.9
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

    def call(path, interface, method, params, signature):
        timeout_ms = int((deadline - time.monotonic()) * 1000)
        if timeout_ms <= 0:
            raise TimeoutError("UPower snapshot deadline exceeded.")
        reply = bus.call_sync(SERVICE, path, interface, method, params,
                              GLib.VariantType.new(signature), Gio.DBusCallFlags.NO_AUTO_START,
                              timeout_ms, None)
        return reply.unpack()[0]

    paths = call(ROOT, SERVICE, "EnumerateDevices", None, "(ao)")
    return system_battery(paths, lambda path: call(
        path, "org.freedesktop.DBus.Properties", "GetAll",
        GLib.Variant("(s)", (DEVICE,)), "(a{sv})"))


def measurement(value, unit, minimum=None, maximum=None, places=1):
    if (type(value) not in (float, int) or not math.isfinite(value)
            or (minimum is not None and value < minimum)
            or (maximum is not None and value > maximum)):
        return UNAVAILABLE
    return f"{value:.{places}f}{unit}"


def duration(value):
    if type(value) is not int or value <= 0:
        return UNAVAILABLE
    hours, minutes = divmod((value + 59) // 60, 60)
    return f"{hours} h {minutes:02d} min" if hours else f"{minutes} min"


def format_rows(props):
    state = props.get("State")
    if type(state) is not int:
        state = None
    cycles = props.get("ChargeCycles")
    full, design = (measurement(props.get(key), " Wh", minimum=0.001)
                    for key in ("EnergyFull", "EnergyFullDesign"))
    health = measurement(props.get("Capacity"), "%", minimum=0.001, maximum=100)
    temp = props.get("Temperature")
    # UPower's default 0.0 does not establish a real reading on a laptop.
    temperature = measurement(temp, " °C") if temp != 0 else UNAVAILABLE
    rows = [
        ("Charge", measurement(props.get("Percentage"), "%", minimum=0, maximum=100)),
        ("State", STATES.get(state, UNAVAILABLE)),
        ("Battery health", health),
        ("Full capacity", full),
        ("Design capacity", design),
        ("Charge cycles", str(cycles) if type(cycles) is int and cycles >= 0 else UNAVAILABLE),
        ("Temperature", temperature),
    ]
    if state == 2:
        rows.extend((
            ("Battery draw", measurement(props.get("EnergyRate"), " W", minimum=0.001)),
            ("Estimated time left", duration(props.get("TimeToEmpty"))),
        ))
    elif state == 1:
        rows.append(("Estimated time to full", duration(props.get("TimeToFull"))))
    return rows


def build_window(application, Gdk, Gio, GLib, Gtk):
    window = Gtk.ApplicationWindow(application=application, title="Battery details")
    window.set_name("mbp-battery-details")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_default_size(320, -1)
    window.set_border_width(16)

    provider = Gtk.CssProvider()
    provider.load_from_data(STYLE)
    Gtk.StyleContext.add_provider_for_screen(window.get_screen(), provider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    title = Gtk.Label(label="Battery details", xalign=0)
    title.set_name("battery-details-title")
    content.pack_start(title, False, False, 0)
    content.pack_start(Gtk.Separator(), False, False, 0)

    try:
        props = read_snapshot(Gio, GLib)
    except (GLib.Error, TimeoutError):
        props = None
    if props is None:
        content.pack_start(Gtk.Label(label="Battery data is unavailable.", xalign=0),
                           False, False, 0)
    else:
        grid = Gtk.Grid(column_spacing=22, row_spacing=6)
        for row, (key, value) in enumerate(format_rows(props)):
            label = Gtk.Label(label=key, xalign=0)
            label.get_style_context().add_class("snapshot-label")
            grid.attach(label, 0, row, 1, 1)
            grid.attach(Gtk.Label(label=value, xalign=1, hexpand=True), 1, row, 1, 1)
        content.pack_start(grid, False, False, 0)

    footer = Gtk.Box(spacing=12)
    note = Gtk.Label(label="Snapshot on open", xalign=0)
    note.get_style_context().add_class("snapshot-label")
    close = Gtk.Button(label="Close")
    close.connect("clicked", lambda *_: window.destroy())
    footer.pack_start(note, True, True, 0)
    footer.pack_end(close, False, False, 0)
    content.pack_start(footer, False, False, 0)
    window.add(content)

    def key_press(_, event):
        if event.keyval == Gdk.KEY_Escape:
            window.destroy()
            return True
        return False

    window.connect("key-press-event", key_press)
    window.set_focus(close)
    return window


def activate(application, Gdk, Gio, GLib, Gtk):
    window = application.get_active_window()
    if window is not None:
        window.destroy()
        return
    window = build_window(application, Gdk, Gio, GLib, Gtk)
    window.show_all()
    window.present()


def main():
    if not os.environ.get("WAYLAND_DISPLAY"):
        print("A Wayland session is required to open battery details.", file=sys.stderr)
        return 1
    os.environ["GDK_BACKEND"] = "wayland"
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, Gio, GLib, Gtk
    except (ImportError, ValueError):
        print("Battery details require python3-gi and gir1.2-gtk-3.0.", file=sys.stderr)
        return 1
    GLib.set_application_name("Battery details")
    GLib.set_prgname(APP_ID)
    application = Gtk.Application(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
    application.connect("activate", activate, Gdk, Gio, GLib, Gtk)
    return application.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/python3
"""Read-only month calendar; one Wayland window, no background service."""
import datetime
import os
from pathlib import Path
import sys

APP_ID = "local.mbp.Calendar"


def offset_month(year, month, delta):
    """Return a one-based year/month, bounded to datetime's supported range."""
    if any(type(value) is not int for value in (year, month, delta)):
        raise ValueError("integer year, month and offset required")
    if not 1 <= year <= 9999 or not 1 <= month <= 12:
        raise ValueError("invalid year or month")
    index = max(0, min(9999 * 12 - 1, (year - 1) * 12 + month - 1 + delta))
    return index // 12 + 1, index % 12 + 1


def gtk_modules():
    # Keep pure date helpers importable on administration hosts without GTK.
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gio, GLib, Gtk
    return Gdk, Gio, GLib, Gtk


def build_window(application):
    Gdk, _, GLib, Gtk = gtk_modules()
    window = Gtk.ApplicationWindow(application=application, title="Calendar")
    window.set_name("mbp-calendar")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_default_size(360, 320)
    window.set_border_width(16)

    css = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "calendar/calendar.css"
    provider = Gtk.CssProvider()
    try:
        provider.load_from_path(str(css))
    except GLib.Error:
        print("Calendar theme unavailable; using the GTK fallback.", file=sys.stderr)
    else:
        Gtk.StyleContext.add_provider_for_screen(
            window.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    title = Gtk.Label(label="Calendar")
    title.set_name("calendar-title")
    box.pack_start(title, False, False, 0)
    calendar = Gtk.Calendar()
    calendar.set_display_options(Gtk.CalendarDisplayOptions.SHOW_HEADING |
                                 Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES)
    box.pack_start(calendar, True, True, 0)

    def mark_today(*_):
        today = datetime.date.today()
        year, month, _ = calendar.get_date()
        calendar.clear_marks()
        if (year, month + 1) == (today.year, today.month):
            calendar.mark_day(today.day)

    def show_today(*_):
        today = datetime.date.today()
        calendar.select_month(today.month - 1, today.year)
        calendar.select_day(today.day)
        mark_today()

    def key_press(_, event):
        if event.keyval == Gdk.KEY_Escape:
            window.destroy()
            return True
        if event.keyval == Gdk.KEY_Home:
            show_today()
            return True
        if event.keyval in (Gdk.KEY_Page_Up, Gdk.KEY_Page_Down):
            year, month, _ = calendar.get_date()
            year, month = offset_month(year, month + 1,
                                       -1 if event.keyval == Gdk.KEY_Page_Up else 1)
            calendar.select_month(month - 1, year)
            return True
        return False

    calendar.connect("month-changed", mark_today)
    window.connect("key-press-event", key_press)
    buttons = Gtk.Box(spacing=8)
    today_button = Gtk.Button(label="Today")
    today_button.connect("clicked", show_today)
    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _: window.destroy())
    buttons.pack_start(today_button, True, True, 0)
    buttons.pack_start(close_button, True, True, 0)
    box.pack_start(buttons, False, False, 0)
    hint = Gtk.Label(label="PgUp / PgDn: month   Home: today   Esc: close")
    hint.set_name("calendar-hint")
    box.pack_start(hint, False, False, 0)
    window.add(box)
    show_today()
    return window


def activate(application):
    window = application.get_active_window()
    if window is None:
        window = build_window(application)
        window.show_all()
    window.present()


def main():
    if not os.environ.get("WAYLAND_DISPLAY"):
        print("A Wayland session is required to open the calendar.", file=sys.stderr)
        return 1
    os.environ["GDK_BACKEND"] = "wayland"
    try:
        _, Gio, GLib, Gtk = gtk_modules()
    except (ImportError, ValueError):
        print("Calendar requires python3-gi and gir1.2-gtk-3.0.", file=sys.stderr)
        return 1
    GLib.set_application_name("Calendar")
    # GTK3's Wayland app_id follows the program name, not the D-Bus name.
    GLib.set_prgname(APP_ID)
    application = Gtk.Application(application_id=APP_ID,
                                  flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
    application.connect("activate", activate)
    return application.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

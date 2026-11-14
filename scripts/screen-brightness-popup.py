#!/usr/bin/python3
"""On-demand GTK3 control for the internal display, using brightnessctl."""
import os
from pathlib import Path
import subprocess
import sys

APP_ID = "local.mbp.ScreenBrightness"
DEVICE = "intel_backlight"
UPDATE_DELAY_MS = 75


def read_level():
    result = subprocess.run(["brightnessctl", "-m", "-d", DEVICE, "info"],
                            text=True, capture_output=True, timeout=1, check=True)
    device, kind, level, _, maximum = result.stdout.strip().split(",")
    level, maximum = int(level), int(maximum)
    if (device, kind) != (DEVICE, "backlight") or not 0 <= level <= maximum or maximum == 0:
        raise ValueError("Invalid backlight data")
    return round(100 * level / maximum)


def write_level(level):
    if type(level) is not int or not 1 <= level <= 100:
        raise ValueError("Expected an integer brightness between 1 and 100")
    subprocess.run(["brightnessctl", "-q", "-d", DEVICE, "set", f"{level}%"],
                   stdin=subprocess.DEVNULL, capture_output=True, timeout=1, check=True)


def build_window(application, Gdk, GLib, Gtk):
    window = Gtk.ApplicationWindow(application=application, title="Screen brightness")
    window.set_name("mbp-screen-brightness")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_default_size(320, -1)
    window.set_border_width(16)

    provider = Gtk.CssProvider()
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    try:
        provider.load_from_path(str(config / "brightness/popup.css"))
        Gtk.StyleContext.add_provider_for_screen(
            window.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    except GLib.Error:
        print("Brightness theme unavailable; using the GTK fallback.", file=sys.stderr)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    header = Gtk.Box(spacing=16)
    title = Gtk.Label(label="Screen brightness", xalign=0)
    title.set_name("brightness-title")
    header.pack_start(title, True, True, 0)
    level_label = Gtk.Label(label="--%")
    header.pack_end(level_label, False, False, 0)
    content.pack_start(header, False, False, 0)

    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
    scale.set_draw_value(False)
    scale.get_accessible().set_name("Screen brightness")
    content.pack_start(scale, False, False, 0)

    footer = Gtk.Box(spacing=12)
    hint = Gtk.Label(label="Drag or use arrow keys.", xalign=0)
    hint.set_name("brightness-hint")
    close = Gtk.Button(label="Close")
    close.connect("clicked", lambda *_: window.destroy())
    footer.pack_start(hint, True, True, 0)
    footer.pack_end(close, False, False, 0)
    content.pack_start(footer, False, False, 0)
    window.add(content)

    errors = (OSError, ValueError, subprocess.SubprocessError)
    try:
        applied = read_level()
    except errors:
        hint.set_text("Brightness is unavailable.")
        scale.set_sensitive(False)
    else:
        scale.set_value(max(1, applied))
        level_label.set_text(f"{applied}%")
        pending = None
        timer = 0

        def flush(update_widgets=True):
            nonlocal applied, pending, timer
            timer = 0
            if pending is not None and pending != applied:
                try:
                    write_level(pending)
                except errors:
                    if update_widgets:
                        hint.set_text("Could not set brightness.")
                        scale.handler_block(slider_handler)
                        try:
                            scale.set_value(max(1, applied))
                        finally:
                            scale.handler_unblock(slider_handler)
                        level_label.set_text(f"{applied}%")
                else:
                    applied = pending
                    if update_widgets:
                        hint.set_text("Drag or use arrow keys.")
            pending = None
            return GLib.SOURCE_REMOVE

        def change(widget):
            nonlocal pending, timer
            pending = round(widget.get_value())
            level_label.set_text(f"{pending}%")
            if not timer:
                timer = GLib.timeout_add(UPDATE_DELAY_MS, flush)

        def finish(*_):
            if timer:
                GLib.source_remove(timer)
                flush(update_widgets=False)

        slider_handler = scale.connect("value-changed", change)
        window.connect("destroy", finish)

    def key_press(_, event):
        if event.keyval == Gdk.KEY_Escape:
            window.destroy()
            return True
        return False

    window.connect("key-press-event", key_press)
    window.set_focus(scale if scale.get_sensitive() else close)
    return window


def activate(application, Gdk, GLib, Gtk):
    window = application.get_active_window()
    if window is not None:
        window.destroy()
        return
    window = build_window(application, Gdk, GLib, Gtk)
    window.show_all()
    window.present()


def main():
    if not os.environ.get("WAYLAND_DISPLAY"):
        print("A Wayland session is required to open the brightness control.", file=sys.stderr)
        return 1
    os.environ["GDK_BACKEND"] = "wayland"
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, Gio, GLib, Gtk
    except (ImportError, ValueError):
        print("Brightness control requires python3-gi and gir1.2-gtk-3.0.", file=sys.stderr)
        return 1

    GLib.set_application_name("Screen brightness")
    GLib.set_prgname(APP_ID)
    application = Gtk.Application(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
    application.connect("activate", activate, Gdk, GLib, Gtk)
    return application.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

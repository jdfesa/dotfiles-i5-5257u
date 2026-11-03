"""Offline calendar contracts; real GTK rendering is verified on Wayland."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("calendar_popup", ROOT / "scripts/calendar-popup.py")
popup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(popup)


class CalendarTests(unittest.TestCase):
    def test_month_navigation_across_years(self):
        self.assertEqual(popup.offset_month(2026, 12, 1), (2027, 1))
        self.assertEqual(popup.offset_month(2026, 1, -1), (2025, 12))
        self.assertEqual(popup.offset_month(2026, 11, -12), (2025, 11))

    def test_month_bounds(self):
        self.assertEqual(popup.offset_month(1, 1, -1), (1, 1))
        self.assertEqual(popup.offset_month(9999, 12, 1), (9999, 12))
        for values in ((0, 1, 1), (2026, 13, 0), (True, 1, 0), (2026, 1, "1")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                popup.offset_month(*values)

    def test_activation_reuses_existing_window(self):
        app = Mock()
        with patch.object(popup, "build_window") as build:
            popup.activate(app)
            build.assert_not_called()
        app.get_active_window.return_value.present.assert_called_once_with()

    def test_first_activation_builds_only_one_window(self):
        app = Mock()
        app.get_active_window.return_value = None
        with patch.object(popup, "build_window") as build:
            popup.activate(app)
        build.assert_called_once_with(app)
        build.return_value.show_all.assert_called_once_with()
        build.return_value.present.assert_called_once_with()

    def test_non_wayland_session_fails_without_importing_gtk(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(popup, "gtk_modules") as gtk:
            self.assertEqual(popup.main(), 1)
        gtk.assert_not_called()

    def test_wayland_identity_matches_single_instance_application_id(self):
        gdk, gio, glib, gtk = Mock(), Mock(), Mock(), Mock()
        gtk.Application.return_value.run.return_value = 0
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "fixture"}, clear=True), \
                patch.object(popup, "gtk_modules", return_value=(gdk, gio, glib, gtk)):
            self.assertEqual(popup.main(), 0)
            self.assertEqual(os.environ["GDK_BACKEND"], "wayland")
        glib.set_prgname.assert_called_once_with(popup.APP_ID)
        self.assertEqual(gtk.Application.call_args.kwargs["application_id"], popup.APP_ID)

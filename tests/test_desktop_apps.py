"""Public desktop application integration; no launches or user profile reads."""
import configparser
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DesktopAppsTests(unittest.TestCase):
    def test_browser_shortcut_matches_requested_map(self):
        config = (ROOT / "config/sway/config").read_text()
        self.assertIn("bindsym $mod+Shift+b exec $tools browser", config)
        self.assertNotIn("bindsym $mod+Shift+Return", config)
        self.assertFalse(any("bindsym" in line and "zed" in line for line in config.splitlines()))

    def test_browser_helper_resolves_current_default_without_shell_eval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "xdg-settings").write_text('#!/bin/sh\nprintf "%s\\n" "${FIXTURE_BROWSER:-}"\nexit "${FIXTURE_EXIT:-0}"\n')
            (root / "gtk-launch").write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$FIXTURE_LOG"\n')
            for name in ("xdg-settings", "gtk-launch"):
                (root / name).chmod(0o755)
            log = root / "launch.log"
            base = {**os.environ, "PATH": str(root) + ":/usr/bin:/bin", "FIXTURE_LOG": str(log)}
            for browser in ("helium.desktop", "firefox-esr.desktop", "fixture; not-a-command.desktop"):
                result = subprocess.run(["sh", str(ROOT / "scripts/sway-tools.sh"), "browser"],
                                        env={**base, "FIXTURE_BROWSER": browser}, capture_output=True, timeout=3)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(log.read_text().splitlines(), ["--", browser])
            for extra in ({"FIXTURE_BROWSER": ""}, {"FIXTURE_EXIT": "1"}):
                log.unlink(missing_ok=True)
                result = subprocess.run(["sh", str(ROOT / "scripts/sway-tools.sh"), "browser"],
                                        env={**base, **extra}, capture_output=True, timeout=3)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(log.exists())

    def test_browser_defaults_are_limited_to_web_types(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / "config/helium/mimeapps.list")
        self.assertEqual(config.sections(), ["Default Applications"])
        defaults = dict(config["Default Applications"])
        self.assertEqual(set(defaults), {"text/html", "application/xhtml+xml",
                                       "x-scheme-handler/http", "x-scheme-handler/https"})
        self.assertEqual(set(defaults.values()), {"helium.desktop;"})
        self.assertNotIn("application/pdf", defaults)

    def test_editor_has_reviewed_non_bootstrapping_settings(self):
        config = json.loads((ROOT / "config/zed/settings.json").read_text())
        self.assertFalse(config["auto_update"])
        self.assertFalse(config["telemetry"]["diagnostics"])
        self.assertFalse(config["telemetry"]["metrics"])
        self.assertFalse(config["auto_install_extensions"]["html"])
        self.assertTrue(config["disable_ai"])
        self.assertEqual(config["buffer_font_family"], "JetBrainsMono Nerd Font Mono")
        self.assertEqual(config["terminal"]["shell"]["with_arguments"],
                         {"program": "/usr/bin/zsh", "args": ["--login"]})

    def test_editor_entry_does_not_replace_file_manager(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / "config/zed/dev.zed.Zed.desktop")
        entry = config["Desktop Entry"]
        self.assertEqual(entry["Exec"], "/home/jd/.local/bin/zed %U")
        self.assertEqual(entry["Terminal"], "false")
        self.assertNotIn("inode/directory", entry["MimeType"])
        self.assertTrue(entry["Icon"].startswith("/home/jd/.local/zed.app/"))

    def test_public_app_files_are_individually_managed(self):
        manifest = json.loads((ROOT / "config/manifest.json").read_text())
        expected = {"config/helium/mimeapps.list": ".config/mimeapps.list",
                    "config/yazi/yazi.toml": ".config/yazi/yazi.toml",
                    "config/zathura/zathurarc": ".config/zathura/zathurarc",
                    "config/zed/settings.json": ".config/zed/settings.json",
                    "config/zed/dev.zed.Zed.desktop": ".local/share/applications/dev.zed.Zed.desktop"}
        for source, destination in expected.items():
            entry = next(e for e in manifest if e["source"] == source)
            self.assertEqual(entry["destination"], destination)
            self.assertEqual(entry["deployment"], "symlink")
            self.assertEqual(entry["mode"], 0o644)
        self.assertEqual({e["source"] for e in manifest if e["source"].startswith("config/helium/")},
                         {"config/helium/mimeapps.list"})


class YaziPdfTests(unittest.TestCase):
    def test_pdf_opener_leaves_only_the_focused_kitty_fullscreen(self):
        config = tomllib.loads((ROOT / "config/yazi/yazi.toml").read_text())
        rule = config["open"]["prepend_rules"][0]
        self.assertEqual(rule["mime"], "application/pdf")
        self.assertEqual(rule["use"], ["pdf-dark", "open", "reveal"])
        command = config["opener"]["pdf-dark"][0]["run"]
        self.assertEqual(command.count("%s1"), 1)
        command = command.replace("%s1", '"$1"')
        pdf = "- a 'quoted'; filename.pdf"
        expected_sway = ["timeout:1s", "swaymsg:-q",
                         "swaymsg:[con_id=__focused__ pid=123] fullscreen disable"]
        expected_pdf = ["zathura:--", f"zathura:{pdf}"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "calls"
            stubs = {
                "timeout": """printf 'timeout:%s\n' "$1" >> "$LOG"; shift; exec "$@" """,
                "swaymsg": """printf 'swaymsg:%s\n' "$@" >> "$LOG"; exit "$SWAY_STATUS" """,
                "zathura": """printf 'zathura:%s\n' "$@" >> "$LOG" """,
            }
            for name, script in stubs.items():
                stub = root / name
                stub.write_text("#!/bin/sh\n" + script + "\n")
                stub.chmod(0o755)
            for socket, pid, status, expect_sway in (
                ("/tmp/test-sway.sock", "123", "0", True),
                ("/tmp/test-sway.sock", "123", "2", True),
                ("/tmp/test-sway.sock", "123] kill", "0", False),
                ("/tmp/test-sway.sock", "", "0", False),
                ("", "123", "0", False),
            ):
                with self.subTest(socket=socket, pid=pid, status=status):
                    log.unlink(missing_ok=True)
                    subprocess.run(["sh", "-c", command, "pdf-test", pdf], timeout=3, check=True,
                                   env={"PATH": str(root) + ":/usr/bin:/bin", "LOG": str(log),
                                        "SWAYSOCK": socket, "KITTY_PID": pid, "SWAY_STATUS": status})
                    self.assertEqual(log.read_text().splitlines(),
                                     (expected_sway if expect_sway else []) + expected_pdf)


if __name__ == "__main__":
    unittest.main()

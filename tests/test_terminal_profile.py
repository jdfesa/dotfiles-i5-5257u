"""Source-level integration guards; Kitty's own parser runs on Debian."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TerminalProfileTests(unittest.TestCase):
    def test_kitty_files_are_individually_managed(self):
        manifest = json.loads((ROOT / "config/manifest.json").read_text())
        for name in ("kitty.conf", "theme.conf"):
            entry = next(e for e in manifest if e["source"] == f"config/kitty/{name}")
            self.assertEqual(entry["destination"], f".config/kitty/{name}")
            self.assertEqual(entry["mode"], 0o644)
            self.assertEqual(entry["deployment"], "symlink")

    def test_static_profile_preserves_recovery_and_disables_effects(self):
        options = {}
        for line in (ROOT / "config/kitty/kitty.conf").read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                key, value = line.split(None, 1)
                options[key] = value
        expected = {"linux_display_server": "auto", "shell": "/usr/bin/zsh --login",
                    "include": "theme.conf", "background_opacity": "1.0",
                    "background_blur": "0", "cursor_trail": "0",
                    "cursor_blink_interval": "0", "allow_remote_control": "no",
                    "confirm_os_window_close": "0", "kitty_mod": "ctrl+shift"}
        for key, value in expected.items():
            self.assertEqual(options[key], value)
        self.assertTrue({"listen_on", "startup_session", "geninclude", "watcher"}.isdisjoint(options))

    def test_kitty_tabs_use_the_active_directory_without_extra_services(self):
        config = (ROOT / "config/kitty/kitty.conf").read_text().splitlines()
        self.assertIn("tab_bar_edge top", config)
        self.assertIn("tab_bar_style powerline", config)
        self.assertIn("tab_bar_min_tabs 1", config)
        template = next(line for line in config if line.startswith("tab_title_template "))
        self.assertIn("tab.active_wd", template)
        self.assertIn(".rsplit('/', 1)[-1]", template)
        self.assertIn("map kitty_mod+t new_tab_with_cwd", config)
        self.assertFalse(any(line.startswith("map super+shift+t ") for line in config))

    def test_default_entrypoints_use_kitty(self):
        sway = (ROOT / "config/sway/config").read_text()
        fuzzel = (ROOT / "config/fuzzel/fuzzel.ini").read_text()
        self.assertIn("bindsym $mod+Return exec kitty", sway)
        self.assertIn("bindsym $mod+t floating toggle", sway)
        self.assertIn("terminal=kitty --override=tab_bar_min_tabs=2 -e", fuzzel)
        for source in ("scripts/sway-tools.sh", "scripts/power-menu"):
            content = (ROOT / source).read_text()
            self.assertIn("exec kitty --class=mbp-", content)
            for line in content.splitlines():
                if "exec kitty --class=mbp-" in line:
                    self.assertIn("--override=tab_bar_min_tabs=2", line)
            self.assertNotIn("exec foot", content)

    def test_foot_remains_a_managed_fallback(self):
        self.assertTrue((ROOT / "config/foot/foot.ini").is_file())
        manifest = json.loads((ROOT / "config/manifest.json").read_text())
        self.assertTrue(any(e["source"] == "config/foot/foot.ini" for e in manifest))


if __name__ == "__main__":
    unittest.main()

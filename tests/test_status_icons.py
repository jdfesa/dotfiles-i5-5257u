"""Static icon layout and managed-font coverage; no desktop or network required."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "config/fonts/jetbrains-mono-nerd-font-propo-regular.ttf"
spec = importlib.util.spec_from_file_location("icon_adapter", ROOT / "scripts/status-adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class StatusIconTests(unittest.TestCase):
    def test_font_is_official_pinned_unmodified_asset(self):
        self.assertEqual(hashlib.sha256(FONT.read_bytes()).hexdigest(),
                         "8a2803de76ad18ed82f465dfd17130032c34c031b263179d3047a547c7caa460")
        self.assertEqual(FONT.stat().st_size, 2571412)
        self.assertEqual(FONT.stat().st_mode & 0o777, 0o644)

    def test_font_is_linked_individually(self):
        entries = json.loads((ROOT / "config/manifest.json").read_text())
        entry = next(e for e in entries if e["source"] == str(FONT.relative_to(ROOT)))
        self.assertEqual(entry["destination"], ".local/share/fonts/" + FONT.name)
        self.assertEqual(entry["mode"], 0o644)
        self.assertEqual(entry["deployment"], "symlink")

    def test_cpu_ram_have_distinct_icons_and_values_without_legends(self):
        frame = adapter.adapt_status([dict(name="cpu_usage", full_text="2%"),
                                      dict(name="memory", full_text="60%")])
        cpu = next(b for b in frame if b["name"] == "cpu_usage")["full_text"]
        ram = next(b for b in frame if b["name"] == "memory")["full_text"]
        for text, value, legend in ((cpu, "2%", "CPU"), (ram, "60%", "RAM")):
            self.assertIn(adapter.ICON_FONT, text)
            self.assertNotIn(legend, text)
            self.assertTrue(text.endswith(" " + value))
        self.assertIn("\uf2db", cpu)
        self.assertIn("\uefc5", ram)

    def test_weather_matches_reference_shapes(self):
        for marker, icon in (("☀", "\uf185"), ("☾", "\uf186"), ("☁", "\uf0c2"),
                             ("❄", "\U000f0598"), ("ϟ", "\U000f0593")):
            text = adapter.format_weather(marker + " 22°C")
            self.assertIn(icon, text)
            self.assertIn(adapter.ICON_FONT, text)
            self.assertTrue(text.endswith(" 22°C"))

    def test_weather_stale_and_unavailable_are_preserved(self):
        self.assertTrue(adapter.format_weather("~☾ 15°C").startswith("~<span"))
        self.assertTrue(adapter.format_weather("☁ --°C").endswith(" --°C"))
        self.assertIn(adapter.WEATHER_ICONS["?"], adapter.format_weather("? 18°C"))

    def test_unexpected_weather_and_labels_are_escaped(self):
        self.assertEqual(adapter.format_weather("<unsafe>"), "&lt;unsafe&gt;")
        self.assertTrue(adapter.format_weather("☁ <unsafe>").endswith(" &lt;unsafe&gt;"))
        self.assertTrue(adapter.labeled("\uf2db", "<2%>", adapter.YELLOW).endswith(" &lt;2%&gt;"))

    def test_icon_font_does_not_replace_terminal_text_or_battery_font(self):
        text = adapter.format_battery((75, "discharging"))[0]
        self.assertIn(adapter.BATTERY_FONT, text)
        self.assertNotIn(adapter.ICON_FONT, text)
        self.assertNotIn("Propo", (ROOT / "config/kitty/kitty.conf").read_text())
        self.assertIn("font pango:JetBrainsMono Nerd Font Mono 10", (ROOT / "config/sway/config").read_text())

    def test_volume_states_use_the_same_proportional_icon_font(self):
        for value in ("100%", "40%", "0%", "muted 40%", "unavailable"):
            with self.subTest(value=value):
                frame = adapter.adapt_status([dict(name="volume", instance="default.Master.0", full_text=value)])
                block = next(b for b in frame if b["name"] == "volume")
                self.assertIn(adapter.ICON_FONT, block["full_text"])
                self.assertEqual(block["min_width"], 24)
                self.assertEqual(block["align"], "center")

    def test_only_volume_gap_is_reduced_and_wifi_style_is_unchanged(self):
        frame = adapter.adapt_status([dict(name="volume", instance="default.Master.0", full_text="40%"),
                                      dict(name="wireless", instance=adapter.WIRELESS, full_text="78%")])
        volume = next(b for b in frame if b["name"] == "volume")
        wifi = next(b for b in frame if b["name"] == "wireless")
        self.assertEqual(volume["separator_block_width"], 4)
        self.assertEqual(wifi["separator_block_width"], 12)
        self.assertEqual(wifi["min_width"], 28)
        self.assertIn("BGH Status Icons 12", wifi["full_text"])
        self.assertNotIn(adapter.ICON_FONT, wifi["full_text"])

    @unittest.skipUnless(shutil.which("fc-query"), "fontconfig not available")
    def test_all_proportional_status_icons_exist_in_managed_font(self):
        charset = subprocess.check_output(["fc-query", "--format", "%{charset}", str(FONT)], text=True)
        ranges = [tuple(int(p, 16) for p in part.split("-")) for part in charset.split()]
        icons = tuple(adapter.WEATHER_ICONS.values()) + ("\uf2db", "\uefc5", "\U000f050f", "\uf0a0", "\U000f03d7", "\ueee8", "\uf028", "\uf027", "\uf026")
        self.assertEqual([f"U+{ord(c):X}" for c in icons
                          if not any(r[0] <= ord(c) <= r[-1] for r in ranges)], [])


if __name__ == "__main__":
    unittest.main()

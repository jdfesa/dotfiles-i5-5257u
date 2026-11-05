"""Restore the real manifests into a new home, without installing packages."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("restore_links", ROOT / "tools/link-user-config.py")
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


class RestorationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.repo = self.base / "repo"
        self.home = self.base / "home"
        self.home.mkdir()
        for manifest in ("config/manifest.json", "config/xfce/manifest.json"):
            path = self.repo / manifest
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / manifest, path)
            for entry in json.loads(path.read_text()):
                dest = self.repo / entry["source"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                origin = ROOT / entry["source"]
                if entry["source"] == "private/sway/local.conf":
                    origin = ROOT / "config/sway/local.conf.example"
                shutil.copyfile(origin, dest)
                dest.chmod(entry["mode"])

    def test_main_profile_from_new_home_is_complete_and_reversible(self):
        plan = links.plan(self.repo, self.home)
        self.assertTrue(all(e["action"] == "create" for e in plan))
        journal = links.apply(plan, self.repo, self.home, self.base / "main-backup")
        for entry in plan:
            self.assertEqual(Path(entry["destination"]).resolve(), Path(entry["source"]))
        self.assertTrue(all(e["action"] == "unchanged" for e in links.plan(self.repo, self.home)))
        self.assertFalse((self.home / ".config/autostart/mbp2015-brightness.desktop").exists())
        links.rollback(journal)
        self.assertTrue(all(e["action"] == "create" for e in links.plan(self.repo, self.home)))

    def test_trackpad_module_is_linked_and_loaded_before_local_overrides(self):
        plan = links.plan(self.repo, self.home)
        links.apply(plan, self.repo, self.home, self.base / "main-backup")
        sway = self.home / ".config/sway"
        module = sway / "trackpad-gestures.conf"
        self.assertTrue(module.is_symlink())
        self.assertEqual(module.resolve(), self.repo / "config/sway/trackpad-gestures.conf")
        config = (sway / "config").read_text()
        self.assertLess(config.index("include ~/.config/sway/trackpad-gestures.conf"),
                        config.index("include ~/.config/sway/local.conf"))

    def test_optional_recovery_does_not_change_main_profile(self):
        before = links.plan(self.repo, self.home)
        recovery = links.plan(self.repo, self.home, "config/xfce/manifest.json")
        self.assertEqual(len(recovery), 2)
        links.apply(recovery, self.repo, self.home, self.base / "recovery-backup")
        self.assertEqual(links.plan(self.repo, self.home), before)
        desktop = self.home / ".config/autostart/mbp2015-brightness.desktop"
        self.assertIn("Exec=/home/jd/.local/bin/mbp-xfce-brightness", desktop.read_text())
        self.assertNotIn("github/mbp2015", desktop.read_text())

    def test_manifest_cannot_escape_checkout(self):
        for path in ("../manifest.json", "/tmp/manifest.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                links.plan(self.repo, self.home, path)

    def test_package_profiles_are_explicit_sorted_and_separated(self):
        main = (ROOT / "config/packages/debian.txt").read_text().splitlines()
        optional = (ROOT / "config/xfce/packages-debian.txt").read_text().splitlines()
        self.assertEqual(main, sorted(set(main)))
        self.assertEqual(optional, sorted(set(optional)))
        self.assertTrue(all(re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", name) for name in main + optional))
        self.assertFalse(any("xfce" in name for name in main))
        for name in ("libgtk-3-bin", "dbus-user-session", "firmware-brcm80211",
                     "nm-connection-editor", "gnome-keyring", "sway", "zsh",
                     "python3-gi", "gir1.2-gtk-3.0"):
            self.assertIn(name, main)
        self.assertNotIn("helium-bin", main)

    def test_declared_public_sources_have_deployable_modes(self):
        for manifest in ("config/manifest.json", "config/xfce/manifest.json"):
            for entry in json.loads((ROOT / manifest).read_text()):
                if entry["source"].startswith("private/"):
                    continue
                source = ROOT / entry["source"]
                self.assertTrue(source.is_file() and not source.is_symlink(), entry["source"])
                self.assertEqual(source.stat().st_mode & 0o777, entry["mode"], entry["source"])

    def test_all_shell_scripts_parse_including_optional_helpers(self):
        for path in (ROOT / "scripts").rglob("*"):
            if path.is_file() and (path.suffix == ".sh" or path.name == "power-menu"):
                subprocess.run(["sh", "-n", str(path)], check=True)


if __name__ == "__main__":
    unittest.main()

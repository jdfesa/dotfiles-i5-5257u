import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


links = load("links", "tools/link-user-config.py")
sync = load("sync", "tools/sync-to-host.py")
status = load("status", "scripts/sway-status.py")


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "repo"
        self.home = self.base / "home"
        (self.root / "config").mkdir(parents=True)
        self.home.mkdir()
        self.source = self.root / "config/test"
        self.source.write_text("managed\n")
        self.source.chmod(0o644)
        (self.root / "config/manifest.json").write_text(json.dumps([
            dict(source="config/test", destination=".config/test/config", mode=0o644, deployment="symlink")]))
        self.target = self.home / ".config/test/config"

    def test_dry_run_has_no_side_effects(self):
        self.assertEqual(links.plan(self.root, self.home)[0]["action"], "create")
        self.assertFalse((self.home / ".config").exists())

    def test_apply_is_idempotent_and_rollback_removes_new_link(self):
        journal = links.apply(links.plan(self.root, self.home), self.root, self.home, self.base / "backup")
        self.assertEqual(self.target.resolve(), self.source)
        self.assertEqual(links.plan(self.root, self.home)[0]["action"], "unchanged")
        self.assertEqual(journal.stat().st_mode & 0o777, 0o600)
        links.rollback(journal)
        self.assertFalse(self.target.exists())

    def test_identical_copy_is_backed_up_and_restored(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.source.read_bytes())
        self.target.chmod(0o640)
        journal = links.apply(links.plan(self.root, self.home), self.root, self.home, self.base / "backup")
        links.rollback(journal)
        self.assertFalse(self.target.is_symlink())
        self.assertEqual(self.target.read_bytes(), self.source.read_bytes())
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o640)

    def test_changed_copy_is_a_conflict(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_text("personal changes\n")
        with self.assertRaisesRegex(ValueError, "Conflict"):
            links.plan(self.root, self.home)
        self.assertEqual(self.target.read_text(), "personal changes\n")

    def test_symlinked_parent_is_refused(self):
        other = self.base / "other"
        other.mkdir()
        (self.home / ".config").symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlinked parent"):
            links.plan(self.root, self.home)

    def test_rollback_preserves_new_user_changes(self):
        journal = links.apply(links.plan(self.root, self.home), self.root, self.home, self.base / "backup")
        self.target.unlink()
        self.target.write_text("new user data\n")
        with self.assertRaisesRegex(ValueError, "Changed destination"):
            links.rollback(journal)
        self.assertEqual(self.target.read_text(), "new user data\n")

    def test_backup_inside_repo_is_refused(self):
        with self.assertRaisesRegex(ValueError, "outside the working tree"):
            links.apply(links.plan(self.root, self.home), self.root, self.home, self.root / "backup")

    def test_plan_detects_changed_source_before_apply(self):
        plan = links.plan(self.root, self.home)
        self.source.write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "changed after planning"):
            links.apply(plan, self.root, self.home, self.base / "backup")


class BatteryTests(unittest.TestCase):
    def test_real_charge_not_battery_health(self):
        sample = "  state: discharging\n  percentage: 87.5%\n  capacity: 62.9%\n"
        self.assertEqual(status.parse_battery(sample), (87.5, "discharging"))

    def test_bad_and_missing_readings_are_honest(self):
        self.assertIsNone(status.parse_battery("capacity: 62.9%"))
        self.assertIsNone(status.parse_battery("state: discharging\npercentage: 101%"))
        self.assertIn("unavailable", status.format_status(None))

    def test_warnings_only_while_discharging(self):
        self.assertEqual(status.warning_level((19, "discharging")), 1)
        self.assertEqual(status.warning_level((9, "discharging")), 2)
        self.assertEqual(status.warning_level((9, "charging")), 0)


class HygieneTests(unittest.TestCase):
    def test_manifest_destinations_are_home_relative_unique(self):
        entries = json.loads((ROOT / "config/manifest.json").read_text())
        destinations = [e["destination"] for e in entries]
        self.assertEqual(len(destinations), len(set(destinations)))
        for destination in destinations:
            self.assertFalse(Path(destination).is_absolute())
            self.assertNotIn("..", Path(destination).parts)

    def test_only_reviewed_private_file_is_transferable(self):
        self.assertEqual(sync.PRIVATE_FILES, ("private/sway/local.conf",))

    def test_reference_bindings_and_sway_specific_lock(self):
        config = (ROOT / "config/sway/config").read_text()
        for binding in ("$mod+Return", "$mod+space", "$mod+n", "$mod+a", "$mod+k", "$mod+Mod1+s"):
            self.assertIn("bindsym " + binding + " ", config)
        self.assertNotIn("i3lock", config)
        self.assertNotIn(" restart\n", config)
        self.assertIn("swaylock -f", config)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_text("/private/\n*.pem\n.env\n")
        (self.root / "public.conf").write_text("public fixture\n")
        (self.root / "private/sway").mkdir(parents=True)
        (self.root / "private/local").mkdir()
        (self.root / "private/sway/local.conf").write_text("output eDP-1 scale 2\n")
        (self.root / "private/sway/local.conf").chmod(0o600)
        (self.root / "private/local/ssh-target").write_text("fixture, never transferred\n")

    def test_private_local_and_ignored_secrets_never_enter_payload(self):
        (self.root / ".env").write_text("test fixture, not a credential\n")
        (self.root / "fixture.pem").write_text("not a key\n")
        self.assertEqual(sync.file_list(self.root), [".gitignore", "private/sway/local.conf", "public.conf"])

    def test_temporary_reference_tree_never_enters_transfer_list(self):
        with (self.root / ".gitignore").open("a") as stream:
            stream.write("tmp/\n")
        reference = self.root / "tmp/reference/install_scripts"
        reference.mkdir(parents=True)
        (reference / "install.sh").write_text("fixture only; never execute\n")
        self.assertEqual(sync.file_list(self.root),
                         [".gitignore", "private/sway/local.conf", "public.conf"])

    def test_tracked_but_newly_ignored_file_blocks_transfer(self):
        (self.root / "state.log").write_text("non-secret fixture\n")
        subprocess.run(["git", "add", "state.log"], cwd=self.root, check=True)
        with (self.root / ".gitignore").open("a") as stream:
            stream.write("*.log\n")
        with self.assertRaisesRegex(ValueError, "Tracked-but-ignored"):
            sync.file_list(self.root)

    def test_symlink_source_is_refused(self):
        os.symlink("public.conf", self.root / "unexpected-link")
        with self.assertRaisesRegex(ValueError, "regular in-tree"):
            sync.file_list(self.root)

    def test_shared_private_requires_0600(self):
        (self.root / "private/sway/local.conf").chmod(0o644)
        with self.assertRaisesRegex(ValueError, "0600"):
            sync.file_list(self.root)


if __name__ == "__main__":
    unittest.main()

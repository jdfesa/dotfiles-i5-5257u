import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("packages", Path(__file__).resolve().parents[1] / "scripts/update-packages.py")
packages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packages)


class PackageTests(unittest.TestCase):
    def test_count_install_candidates_not_summary(self):
        self.assertEqual(packages.count_upgrades("Inst foo [1] (2 Debian)\nConf foo (2 Debian)\nInst bar (1 Debian)\n"), 2)
        self.assertEqual(packages.count_upgrades("0 upgraded, 0 newly installed"), 0)

    def test_command_cannot_install_or_refresh_metadata(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(packages.subprocess, "run") as run:
            run.return_value.stdout = "Inst foo [1] (2 Debian)\n"
            self.assertEqual(packages.refresh(Path(folder)), 0)
            self.assertEqual((Path(folder) / "updates.txt").read_text(), "1\n")
            self.assertEqual(run.call_args.args[0], ["apt-get", "--simulate", "upgrade"])
            self.assertTrue(run.call_args.kwargs["check"])

    def test_error_replaces_count_with_unknown(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(packages.subprocess, "run", side_effect=subprocess.TimeoutExpired("apt", 25)):
            self.assertEqual(packages.refresh(Path(folder)), 1)
            self.assertEqual((Path(folder) / "updates.txt").read_text(), "?\n")


if __name__ == "__main__":
    unittest.main()

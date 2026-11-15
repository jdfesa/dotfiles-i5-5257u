"""Test optional restoration without editing the host or downloading binaries."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import pty
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"tools/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


restore = load("restore-profile")
node = load("install-node")


class RestorePlanTests(unittest.TestCase):
    def test_packages_default_to_simulation_without_sudo(self):
        for profile in restore.PROFILES:
            with self.subTest(profile=profile):
                cmd = restore.build_command(profile, "packages")
                self.assertEqual(cmd[:2], ["apt-get", "-s"])
                self.assertIn("--no-remove", cmd)
                self.assertEqual(restore.build_command(profile, "packages", True),
                                 ["sudo", "apt-get", *cmd[2:]])
                dependency_file = ROOT / f"config/{profile}/packages-debian.txt"
                packages = dependency_file.read_text().splitlines()
                self.assertEqual(packages, sorted(set(packages)))
                self.assertEqual(cmd[-len(packages):], packages)
        main = (ROOT / "config/packages/debian.txt").read_text().splitlines()
        for name in ("openssh-server", "dnsmasq-base", "nodejs", "xfce4"):
            self.assertNotIn(name, main)

    def test_links_only_for_supported_profiles_with_explicit_backup(self):
        for name in ("node", "ssh"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                restore.build_command(name, "links")
        for name in ("hotspot", "xampp", "xfce"):
            with self.subTest(name=name):
                cmd = restore.build_command(name, "links")
                self.assertEqual(cmd[-2:], ["--manifest", f"config/{name}/manifest.json"])
                self.assertNotIn("--apply", cmd)
                with self.assertRaises(ValueError):
                    restore.build_command(name, "links", True)
                self.assertEqual(restore.build_command(name, "links", True, "/tmp/backup"),
                                 cmd + ["--apply", "--backup-dir", "/tmp/backup"])
        with self.assertRaises(ValueError):
            restore.build_command("ssh", "packages", backup="/tmp/backup")

    def test_ssh_hardening_is_a_standalone_template(self):
        path = ROOT / "config/ssh/10-dotfiles-key-only.conf"
        directives = [line.split() for line in path.read_text().splitlines()
                      if line and not line.startswith("#")]
        self.assertEqual(dict(directives), {
            "PermitRootLogin": "no", "PubkeyAuthentication": "yes",
            "PasswordAuthentication": "no", "KbdInteractiveAuthentication": "no",
        })
        self.assertNotIn("sshd", (ROOT / "config/manifest.json").read_text())


class NodeInstallTests(unittest.TestCase):
    version = "v22.20.0"

    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.base = Path(td.name).resolve()
        self.home = self.base / "home with spaces"
        self.home.mkdir()
        self.name = f"node-{self.version}-linux-x64"
        src = self.base / self.name
        (src / "bin").mkdir(parents=True)
        cli = src / "lib/npm-cli.js"
        cli.parent.mkdir()
        for exe in (src / "bin/node", cli):
            exe.write_text("#!/bin/sh\nexit 0\n")
            exe.chmod(0o755)
        for cmd in ("npm", "npx"):
            (src / "bin" / cmd).symlink_to("../lib/npm-cli.js")
        self.archive = self.base / f"{self.name}.tar.xz"
        with tarfile.open(self.archive, "w:xz") as tar:
            tar.add(src, self.name)
        self.digest = sha256(self.archive.read_bytes()).hexdigest()

    def download(self, args, **kwargs):
        self.assertEqual(args[-1], f"https://nodejs.org/dist/{self.version}/{self.archive.name}")
        self.assertIn("=https", args)
        shutil.copyfile(self.archive, args[args.index("--output") + 1])

    def test_verified_archive_installs_relative_links(self):
        with patch.object(node.subprocess, "run", side_effect=self.download):
            node.install(self.home, self.version, self.name, self.digest)
        for cmd in node.COMMANDS:
            link = self.home / ".local/bin" / cmd
            self.assertTrue(link.is_symlink())
            self.assertFalse(Path(os.readlink(link)).is_absolute())
            self.assertTrue(link.resolve().is_file())
            self.assertTrue(link.resolve().is_relative_to(self.home / ".local/share/nodejs"))
        with self.assertRaisesRegex(ValueError, "Destination already exists"):
            node.destinations(self.home, self.name)

    def test_wrong_sha_does_not_install_binaries_or_leave_download(self):
        with patch.object(node.subprocess, "run", side_effect=self.download):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                node.install(self.home, self.version, self.name, "0" * 64)
        self.assertEqual(list((self.home / ".local/share/nodejs").iterdir()), [])
        self.assertFalse((self.home / ".local/bin").exists())

    def test_existing_dangling_link_prevents_download(self):
        bindir = self.home / ".local/bin"
        bindir.mkdir(parents=True)
        link = bindir / "npm"
        link.symlink_to("previous-install")
        with patch.object(node.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "Destination already exists"):
                node.install(self.home, self.version, self.name, self.digest)
            run.assert_not_called()
        self.assertEqual(os.readlink(link), "previous-install")

    def test_extract_rejects_link_outside_archive(self):
        info = tarfile.TarInfo(f"{self.name}/bin/node")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../../outside"
        with tarfile.open(self.archive, "w:xz") as tar:
            tar.addfile(info)
        with patch.object(node.subprocess, "run", side_effect=self.download):
            with self.assertRaises(tarfile.FilterError):
                node.install(self.home, self.version, self.name,
                             sha256(self.archive.read_bytes()).hexdigest())
        self.assertFalse((self.home / ".local/bin").exists())

    def test_rejects_unsafe_version_and_invalid_digest(self):
        with self.assertRaises(ValueError):
            node.spec("../v22.20.0", self.digest)
        with self.assertRaises(ValueError):
            node.spec(self.version, self.digest[:-1])
        self.assertEqual(node.spec(self.version, self.digest.upper()), (self.name, self.digest))


MOCK_NMCLI = """#!/usr/bin/python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ["EVENT_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
if "--get-values" in args:
    field = args[args.index("--get-values") + 1]
    settings = {
        "connection.type": "802-11-wireless",
        "802-11-wireless.mode": os.environ.get("WIFI_MODE", "ap"),
        "connection.autoconnect": os.environ.get("AUTOCONNECT", "no"),
        "ipv4.method": "shared",
        "802-11-wireless-security.key-mgmt": os.environ.get("KEY_MGMT", "wpa-psk"),
        "UUID": os.environ.get("ACTIVE_UUID", ""),
    }
    if field == "UUID" and os.environ.get("FAIL_ACTIVE_QUERY"):
        sys.exit(1)
    print(settings[field])
"""


class HotspotTests(unittest.TestCase):
    uuid = "12345678-1234-abcd-1234-1234567890ab"

    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        mock = self.tmp / "nmcli"
        mock.write_text(MOCK_NMCLI)
        mock.chmod(0o755)
        self.log = self.tmp / "events"
        self.env = {
            "PATH": f"{self.tmp}:{os.defpath}",
            "EVENT_LOG": str(self.log),
        }

    def run_cli(self, action, answer=None, uuid=None, **env):
        command = [str(ROOT / "scripts/wifi-hotspot.sh"), action, uuid or self.uuid]
        kwargs = dict(env=self.env | env, text=True, capture_output=True, timeout=5)
        if answer is None:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, **kwargs)
        else:
            master, slave = pty.openpty()
            try:
                os.write(master, (answer + "\n").encode())
                result = subprocess.run(command, stdin=slave, **kwargs)
            finally:
                os.close(master)
                os.close(slave)
        events = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        self.log.unlink(missing_ok=True)
        return result, events

    def changes(self, events):
        return [cmd[2:] for cmd in events if cmd[2:4] in (["connection", "up"],
                                                          ["connection", "down"])]

    def test_status_is_read_only_even_over_ssh(self):
        result, events = self.run_cli("status", SSH_CONNECTION="connected", ACTIVE_UUID=self.uuid)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Hotspot is active", result.stdout)
        self.assertEqual(self.changes(events), [])

    def test_rejects_multiline_uuid_before_network_queries(self):
        result, events = self.run_cli("status", uuid=self.uuid + "\nextra")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(events, [])

    def test_rejects_mutation_over_ssh_or_without_tty(self):
        for params in ({"answer": "y", "SSH_CONNECTION": "connected"}, {}):
            with self.subTest(params=params):
                result, events = self.run_cli("start", **params)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(events, [])

    def test_refuses_client_autoconnect_and_unprotected_profiles(self):
        for env in ({"WIFI_MODE": "infrastructure"}, {"AUTOCONNECT": "yes"},
                    {"KEY_MGMT": "none"}, {"FAIL_ACTIVE_QUERY": "1"}):
            with self.subTest(env=env):
                result, events = self.run_cli("start", "y", **env)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.changes(events), [])

    def test_start_requires_confirmation_and_forward_only_selected_uuid(self):
        result, events = self.run_cli("start", "")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.changes(events), [])
        result, events = self.run_cli("start", "y")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.changes(events), [["connection", "up", "uuid", self.uuid]])

    def test_stop_only_acts_on_selected_active_ap(self):
        result, events = self.run_cli("stop", "", ACTIVE_UUID=self.uuid)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.changes(events), [["connection", "down", "uuid", self.uuid]])
        result, events = self.run_cli("stop", "", ACTIVE_UUID="other")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.changes(events), [])


if __name__ == "__main__":
    unittest.main()

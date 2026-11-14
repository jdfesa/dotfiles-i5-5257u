#!/usr/bin/env python3
"""Preview or apply one optional Debian package or user-link profile."""
import argparse
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "hotspot": "config/hotspot/manifest.json",
    "node": None,
    "ssh": None,
    "xampp": "config/xampp/manifest.json",
    "xfce": "config/xfce/manifest.json",
}


def build_command(profile, action, apply=False, backup=None):
    if action == "packages":
        if backup is not None:
            raise ValueError("--backup-dir is only valid for --apply links")
        packages = (ROOT / "config" / profile / "packages-debian.txt").read_text().splitlines()
        if not packages or any(not re.fullmatch(r"[a-z0-9][a-z0-9+.-]+", p)
                               for p in packages):
            raise ValueError("Invalid Debian package list")
        prefix = ["sudo"] if apply else []
        flags = [] if apply else ["-s"]
        return prefix + ["apt-get", *flags, "--no-install-recommends", "--no-remove",
                         "install", *packages]

    manifest = PROFILES[profile]
    if manifest is None:
        raise ValueError(f"{profile} has no user-link manifest")
    if apply != (backup is not None):
        raise ValueError("--apply links requires a new external --backup-dir")
    command = ["python3", str(ROOT / "tools/link-user-config.py"), "--manifest", manifest]
    if apply:
        command += ["--apply", "--backup-dir", backup]
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILES)
    parser.add_argument("action", choices=("packages", "links"))
    parser.add_argument("--apply", action="store_true", help="Apply instead of previewing")
    parser.add_argument("--backup-dir", help="New external backup directory for --apply links")
    args = parser.parse_args()
    try:
        command = build_command(args.profile, args.action, args.apply, args.backup_dir)
        raise SystemExit(subprocess.call(command))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Stopped: {error}\n")


if __name__ == "__main__":
    main()

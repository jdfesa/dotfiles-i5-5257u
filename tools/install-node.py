#!/usr/bin/env python3
"""Install a reviewed Node.js linux-x64 tarball in the current user's home."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
from tempfile import TemporaryDirectory

COMMANDS = ("node", "npm", "npx")
BASE = "https://nodejs.org/dist"


def spec(version, sha256):
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Expected a stable release such as v22.20.0")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", sha256):
        raise ValueError("Expected the reviewed SHA-256 for the linux-x64 .tar.xz")
    return f"node-{version}-linux-x64", sha256.lower()


def destinations(home, name):
    local = home / ".local"
    share = local / "share"
    releases = share / "nodejs"
    bindir = local / "bin"
    for path in (home, local, share, releases, bindir):
        if path.is_symlink() or (path.exists() and
                                (not path.is_dir() or path.stat().st_uid != os.getuid())):
            raise ValueError(f"Refusing an unsafe home directory path: {path}")
    release = releases / name
    for path in (release, *(bindir / cmd for cmd in COMMANDS)):
        if path.exists() or path.is_symlink():
            raise ValueError(f"Destination already exists; preserve and review: {path}")
    return release, bindir


def install(home, version, name, sha256):
    release, bindir = destinations(home, name)
    release.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".node-install-", dir=release.parent) as path:
        work = Path(path)
        archive = work / f"{name}.tar.xz"
        subprocess.run(["curl", "--disable", "--fail", "--silent", "--show-error", "--location",
                        "--proto", "=https", "--proto-redir", "=https",
                        "--connect-timeout", "15", "--max-time", "180",
                        "--output", str(archive), f"{BASE}/{version}/{archive.name}"], check=True)
        with archive.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != sha256:
            raise ValueError("SHA-256 mismatch; no binaries installed")
        with tarfile.open(archive, "r:xz") as bundle:
            bundle.extractall(work / "extract", filter="data")
        source = work / "extract" / name
        if not source.is_dir() or source.is_symlink():
            raise ValueError("Missing expected release directory")
        for cmd in COMMANDS:
            executable = (source / "bin" / cmd).resolve()
            if not executable.is_relative_to(source) or not executable.is_file() or not os.access(executable, os.X_OK):
                raise ValueError(f"Missing or unsafe Node.js executable: {cmd}")

        destinations(home, name)
        bindir.mkdir(parents=True, exist_ok=True)
        # Reserve the version directory without overwriting another installation.
        release.mkdir()
        made = []
        try:
            for entry in source.iterdir():
                entry.rename(release / entry.name)
            for cmd in COMMANDS:
                link = bindir / cmd
                link.symlink_to(os.path.relpath(release / "bin" / cmd, bindir))
                made.append(link)
        except OSError:
            for link in made:
                link.unlink()
            shutil.rmtree(release)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Reviewed stable release, including the v prefix")
    parser.add_argument("sha256", help="Digest of the linux-x64 .tar.xz from the verified manifest")
    parser.add_argument("--apply", action="store_true", help="Download, verify and install")
    args = parser.parse_args()
    try:
        if os.geteuid() == 0:
            raise ValueError("Run as the target user, without sudo")
        if platform.system() != "Linux" or platform.machine() != "x86_64":
            raise ValueError("This profile requires Linux x86_64")
        home = Path.home()
        name, digest = spec(args.version, args.sha256)
        release, bindir = destinations(home, name)
        print(f"Release: {release}\nLinks: {bindir}/{{node,npm,npx}}", flush=True)
        if args.apply:
            install(home, args.version, name, digest)
        else:
            print("Dry-run only; no downloads or changes")
    except (OSError, ValueError, tarfile.TarError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Stopped: {error}\n")


if __name__ == "__main__":
    main()

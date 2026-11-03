#!/usr/bin/env python3
"""SSH/rsync only: reviewed public files plus a fixed private allowlist.

Dry-run by default, no deletions, no .git transfer, external private backups.
Bootstrap the destination Git checkout before using this tool.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_FILES = ("private/sway/local.conf",)
DESTINATION = "dotfiles-i5-5257u"


def verify_remote(ssh, target, destination, names):
    records = [{"name": name, "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                "mode": stat.S_IMODE((ROOT / name).stat().st_mode)} for name in names]
    code = '''import hashlib,json,os,pathlib,stat,sys
root=pathlib.Path(sys.argv[1])
records=json.load(sys.stdin)
for record in records:
    path=root/record["name"]
    if path.is_symlink() or not path.is_file() or path.resolve()!=path:
        raise SystemExit("Unsafe remote source: "+record["name"])
    if path.stat().st_uid!=os.getuid() or stat.S_IMODE(path.stat().st_mode)!=record["mode"]:
        raise SystemExit("Remote owner/mode mismatch: "+record["name"])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=record["sha256"]:
        raise SystemExit("Remote hash mismatch: "+record["name"])
print("Verified remote SHA256, owner and mode for",len(records),"reviewed files.")
'''
    command = "python3 -c " + shlex.quote(code) + " " + shlex.quote(destination)
    subprocess.run(ssh + [target, command], input=json.dumps(records), text=True, check=True)


def file_list(root):
    ignored = subprocess.check_output(
        ["git", "ls-files", "-ci", "--exclude-standard", "-z"], cwd=root)
    if ignored:
        raise ValueError("Tracked-but-ignored files found; review before transfer")
    files = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root)
    names = set(os.fsdecode(name) for name in files.split(b"\0") if name)
    # Deleted public files are deliberately not propagated as remote deletions.
    names = {name for name in names if (root / name).exists()}
    for name in PRIVATE_FILES:
        source = root / name
        if not source.is_file() or stat.S_IMODE(source.stat().st_mode) != 0o600:
            raise ValueError(f"Required private file must be regular and 0600: {name}")
        names.add(name)
    for name in names:
        path = Path(name)
        source = root / path
        if path.is_absolute() or ".." in path.parts or ".git" in path.parts:
            raise ValueError("Unsafe source path")
        if source.is_symlink() or source.resolve() != root.resolve() / path or not source.is_file():
            raise ValueError(f"Only regular in-tree files can be sent: {name}")
    return sorted(names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--target", help="user@host; default private/local/ssh-target")
    parser.add_argument("--ssh-control", type=Path, help="An existing SSH ControlPath")
    args = parser.parse_args()
    try:
        target = args.target or (ROOT / "private/local/ssh-target").read_text().strip()
        if not re.fullmatch(r"[a-z_][a-z0-9_-]*@[A-Za-z0-9][A-Za-z0-9_.-]*", target):
            raise ValueError("Expected user@host, without SSH options or paths")
        names = file_list(ROOT)
        ssh = ["ssh", "-o", "StrictHostKeyChecking=yes", "-o", "BatchMode=yes"]
        if args.ssh_control:
            ssh += ["-S", str(args.ssh_control)]
        home = subprocess.check_output(ssh + [target, 'printf "%s" "$HOME"'], text=True).strip()
        if not re.fullmatch(r"/home/[a-z_][a-z0-9_-]*", home):
            raise ValueError("Unexpected remote home; review manually")
        destination = home + "/" + DESTINATION
        subprocess.run(ssh + [target,
            f"test ! -L {shlex.quote(destination)} && test -d {shlex.quote(destination + '/.git')}"], check=True)
        backup = home + "/.local/state/" + DESTINATION + "/sync-backups/" + \
            datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
        if args.apply:
            subprocess.run(ssh + [target, f"umask 077; mkdir -p {shlex.quote(backup)}; chmod 700 {shlex.quote(backup)}"], check=True)
        print(f"Public files: {len(names) - len(PRIVATE_FILES)}; private allowlist: {', '.join(PRIVATE_FILES)}", flush=True)
        command = ["rsync", "-rltp", "--checksum", "--itemize-changes", "--from0", "--files-from=-",
                   "--backup", "--backup-dir=" + backup, "-e", shlex.join(ssh)]
        if not args.apply:
            command.append("--dry-run")
        command += [str(ROOT) + "/", target + ":" + destination + "/"]
        subprocess.run(command, input=b"\0".join(os.fsencode(name) for name in names) + b"\0", check=True)
        print("Transfer finished; replaced files backed up outside the repo." if args.apply else "Dry-run only; nothing changed.")
        if args.apply:
            subprocess.run(ssh + [target, f"chmod 700 {shlex.quote(destination + '/private')} {shlex.quote(destination + '/private/sway')}"], check=True)
            verify_remote(ssh, target, destination, names)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Stopped: {error}\n")


if __name__ == "__main__":
    main()

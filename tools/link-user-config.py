#!/usr/bin/env python3
"""Link only manifest entries explicitly marked deployment=symlink.

Adapted from i3-2310m; see licenses/i3-reference-MIT.txt.

Dry-run by default. Different files/links and symlinked parents are conflicts.
Only identical regular copies may be replaced, with a private external backup.
Rollback verifies link identity and backups before touching any destination.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_parents(path, boundary):
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Invalid destination path")
    path.relative_to(boundary)
    current = boundary
    if current.is_symlink() or not current.is_dir():
        raise ValueError(f"Unsafe home directory: {current}")
    if current.stat().st_uid != os.getuid():
        raise ValueError(f"Directory is not owned by this account: {current}")
    for part in path.parent.relative_to(boundary).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlinked parent: {current}")
        if current.exists() and (not current.is_dir() or current.stat().st_uid != os.getuid()):
            raise ValueError(f"Unsafe parent: {current}")


def snapshot(path):
    if path.is_symlink():
        if path.lstat().st_uid != os.getuid():
            raise ValueError(f"Link is not owned by this account: {path}")
        return {"kind": "link", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "absent"}
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        raise ValueError(f"Not an account-owned regular file: {path}")
    return {"kind": "file", "sha256": digest(path), "mode": stat.S_IMODE(st.st_mode)}


def plan(root, home, manifest=Path("config/manifest.json")):
    root, home = root.resolve(), home.absolute()
    manifest = Path(manifest)
    if manifest.is_absolute() or ".." in manifest.parts:
        raise ValueError("Manifest must be an in-tree relative path")
    manifest_path = root / manifest
    if manifest_path.is_symlink() or not manifest_path.is_file() or manifest_path.resolve() != manifest_path:
        raise ValueError("Manifest must be a regular in-tree file")
    entries = json.loads(manifest_path.read_text())
    result = []
    for entry in entries:
        if entry.get("deployment") != "symlink":
            continue
        relative = Path(entry["source"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid source path")
        source = root / relative
        if source.is_symlink() or not source.is_file() or source.resolve() != source:
            raise ValueError(f"Source must be a regular in-tree file: {source}")
        if source.stat().st_uid != os.getuid() or stat.S_IMODE(source.stat().st_mode) != entry["mode"]:
            raise ValueError(f"Incorrect source owner/mode: {source}")
        relative_target = Path(entry["destination"])
        if relative_target.is_absolute() or ".." in relative_target.parts:
            raise ValueError("Invalid destination path")
        target = home / relative_target
        check_parents(target, home)
        before = snapshot(target)
        expected = {"kind": "link", "target": str(source)}
        if before == expected:
            action = "unchanged"
        elif before["kind"] == "absent":
            action = "create"
        elif before["kind"] == "file" and before["sha256"] == digest(source):
            action = "replace-identical-copy"
        else:
            raise ValueError(f"Conflict; preserve and review: {target}")
        result.append(dict(source=str(source), destination=str(target), before=before,
                           sha256=digest(source), action=action))
    if len({e["destination"] for e in result}) != len(result):
        raise ValueError("Duplicate destination")
    if not result:
        raise ValueError("No explicitly symlink-managed entries")
    return result


def write_journal(path, data):
    temporary = path.with_suffix(".new")
    with temporary.open("x") as stream:
        os.chmod(temporary, 0o600)
        json.dump(data, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def rollback(journal):
    if journal.is_symlink() or journal.stat().st_uid != os.getuid():
        raise ValueError("Refusing an unsafe journal")
    data = json.loads(journal.read_text())
    if data.get("version") != 1:
        raise ValueError("Unsupported journal version")
    home = Path(data["home"])
    actions = []
    for entry in data["entries"]:
        target = Path(entry["destination"])
        check_parents(target, home)
        current = snapshot(target)
        expected = {"kind": "link", "target": entry["source"]}
        if current not in (expected, entry["before"], {"kind": "absent"}):
            raise ValueError(f"Changed destination; rollback stopped: {target}")
        name = entry.get("backup")
        if name and (Path(name).name != name or name in (".", "..")):
            raise ValueError("Invalid backup filename")
        backup = journal.parent / name if name else None
        if backup is not None:
            if backup.is_symlink() or digest(backup) != entry["before"]["sha256"]:
                raise ValueError(f"Invalid backup: {backup}")
        actions.append((entry, target, current, backup))
    for entry, target, current, backup in reversed(actions):
        if current == entry["before"]:
            continue
        if target.is_symlink():
            target.unlink()
        if backup is not None:
            with target.open("xb") as stream:
                stream.write(backup.read_bytes())
                os.fchmod(stream.fileno(), entry["before"]["mode"])
    data["state"] = "rolled-back"
    write_journal(journal, data)


def apply(entries, root, home, backup):
    root, home, backup = root.resolve(), home.absolute(), backup.absolute()
    if backup == root or root in backup.parents:
        raise ValueError("Backup must be outside the working tree")
    if backup == home / ".config" or home / ".config" in backup.parents:
        raise ValueError("Backup must be outside configuration destinations")
    for path in (backup, *backup.parents):
        if path.is_symlink():
            raise ValueError("Symlinked backup path")
    if backup.exists():
        raise ValueError("Backup directory must be new")
    active = [dict(e) for e in entries if e["action"] != "unchanged"]
    if not active:
        return None
    for entry in active:
        target, source = Path(entry["destination"]), Path(entry["source"])
        check_parents(target, home)
        if snapshot(target) != entry["before"] or digest(source) != entry["sha256"]:
            raise ValueError("Files changed after planning")
    backup.mkdir(mode=0o700, parents=True)
    os.chmod(backup, 0o700)
    for index, entry in enumerate(active):
        if entry["before"]["kind"] == "file":
            name = f"file-{index}"
            path = backup / name
            with path.open("xb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(Path(entry["destination"]).read_bytes())
            if digest(path) != entry["before"]["sha256"]:
                raise ValueError("File changed while backing up")
            entry["backup"] = name
    journal = backup / "journal.json"
    data = dict(version=1, root=str(root), home=str(home), state="prepared", entries=active)
    write_journal(journal, data)
    try:
        for entry in active:
            target = Path(entry["destination"])
            check_parents(target, home)
            if snapshot(target) != entry["before"]:
                raise ValueError(f"Destination changed: {target}")
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            if entry["before"]["kind"] == "file":
                target.unlink()
            os.symlink(entry["source"], target)
        data["state"] = "applied"
        write_journal(journal, data)
    except Exception:
        rollback(journal)
        raise
    return journal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--rollback", type=Path, metavar="JOURNAL")
    parser.add_argument("--manifest", type=Path, default=Path("config/manifest.json"),
                        help="In-tree manifest; default is the Sway profile")
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error("Run as the target account, never root")
    try:
        if args.rollback:
            if args.apply or args.backup_dir or args.manifest != Path("config/manifest.json"):
                parser.error("Rollback cannot be combined with deployment")
            rollback(args.rollback.absolute())
            print("Rollback complete; sources and unrelated files preserved")
            return
        entries = plan(ROOT, Path.home(), args.manifest)
        for entry in entries:
            print(f"{entry['action']}: {entry['destination']}")
        if args.apply:
            if not args.backup_dir:
                parser.error("--apply requires a new private --backup-dir outside the tree")
            journal = apply(entries, ROOT, Path.home(), args.backup_dir)
            print(f"Rollback journal: {journal}" if journal else "No changes")
        elif args.backup_dir:
            parser.error("--backup-dir requires --apply")
        else:
            print("Dry-run only; nothing changed")
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Stopped: {error}\n")


if __name__ == "__main__":
    main()

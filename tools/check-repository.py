#!/usr/bin/env python3
"""Read-only structural validation of working files and optional Git history."""
import argparse
import ipaddress
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"README.md", "LICENSE", "AGENTS.md", "CHANGELOG.md", "TODO.md",
              ".gitignore", ".gitattributes"}
ROOT_DIRS = {"config", "docs", "licenses", "scripts", "tests", "tools"}
PATTERNS = {
    "key-block": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY(?: BLOCK)?-----"),
    "github-token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,255}|github_pat_[A-Za-z0-9_]{50,255})"),
    "cloud-access-id": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "service-api-key": re.compile(rb"\bsk-(?:proj-|svcacct-|ant-)?[A-Za-z0-9_-]{20,}\b"),
    "google-api-key": re.compile(rb"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "slack-token": re.compile(rb"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
    "url-userinfo": re.compile(rb"[a-z][a-z0-9+.-]*://[^\s/]+:[^\s/]+@", re.I),
}
NETWORKS = tuple(ipaddress.IPv4Network(value) for value in
                 ((0x0A000000, 8), (0xAC100000, 12), (0xC0A80000, 16)))
DOC_MARKERS = re.compile(r"\bel usuario (?:confirm|pidi|solicit|respond|aclar)|\busuario confirm|durante (?:este|el) trabajo|"
                         r"equipo de administraci[oó]n|en esta conversaci[oó]n", re.I)
IGNORED_EXAMPLES = ("private/sway/local.conf", "private/local/ssh-target", ".env",
                    ".local/share/zed/db.sqlite", ".config/helium/Default/Cookies",
                    "downloads/editor.tar.gz", "fixture.pem", "nested/.ssh/id_ed25519",
                    "nested/.codex/config.toml", ".DS_Store",
                    "tmp/reference/README.md", "tmp/reference/install_scripts/install.sh",
                    "nested/.npmrc", "nested/.pypirc", "nested/.docker/config.json",
                    "nested/.kube/config", "vault.kdbx")


def git(root, *args, data=None):
    return subprocess.check_output(["git", "-C", str(root), *args], input=data)


def working_files(root):
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted({name.decode() for name in names.split(b"\0") if name and
                   ((root / name.decode()).exists() or (root / name.decode()).is_symlink())})


def content_findings(data):
    findings = [name for name, pattern in PATTERNS.items() if pattern.search(data)]
    if b"/" + b"Users/" in data:
        findings.append("administration-path")
    for match in re.findall(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b", data):
        try:
            address = ipaddress.IPv4Address(match.decode())
        except ipaddress.AddressValueError:
            continue
        if any(address in network for network in NETWORKS):
            findings.append("lan-address")
            break
    return findings


def history_blobs(root):
    objects = git(root, "rev-list", "--objects", "--all").splitlines()
    ids = sorted({line.split(b" ", 1)[0] for line in objects})
    if not ids:
        return
    descriptions = git(root, "cat-file", "--batch-check", data=b"\n".join(ids) + b"\n")
    for line in descriptions.splitlines():
        oid, kind, size = line.split()
        if kind == b"blob" and int(size) <= 1_000_000:
            yield oid.decode(), git(root, "cat-file", "blob", oid.decode())


def audit(root, history=False):
    findings = []
    names = working_files(root)
    ignored = git(root, "ls-files", "-ci", "--exclude-standard", "-z")
    if ignored:
        findings.append("tracked-ignore-conflict")
    for required in ROOT_FILES:
        if not (root / required).is_file():
            findings.append(f"missing-root-file: {required}")
    for name in names:
        path = Path(name)
        if (len(path.parts) == 1 and name not in ROOT_FILES or
                len(path.parts) > 1 and path.parts[0] not in ROOT_DIRS):
            findings.append(f"unexpected-layout: {name}")
        source = root / name
        if source.is_symlink() or not source.is_file():
            findings.append(f"non-regular-source: {name}")
            continue
        data = source.read_bytes()
        if len(data) <= 1_000_000 and b"\0" not in data:
            findings.extend(f"{category}: {name}" for category in content_findings(data))
        if source.suffix == ".md":
            text = data.decode("utf-8")
            if DOC_MARKERS.search(text):
                findings.append(f"documentation-style: {name}")
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith(("#", "mailto:")):
                    continue
                target = link.split("#", 1)[0]
                if target and not (source.parent / target).exists():
                    findings.append(f"broken-link: {name} -> {target}")
    for name in IGNORED_EXAMPLES:
        result = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "-q", name])
        if result.returncode != 0:
            findings.append(f"missing-ignore-rule: {name}")
    history_count = 0
    if history:
        for oid, data in history_blobs(root):
            history_count += 1
            findings.extend(f"history-{category}: {oid}" for category in content_findings(data))
    return names, history_count, findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    names, count, findings = audit(ROOT, args.history)
    print(f"Working files checked: {len(names)}; history text-size blobs checked: {count}")
    for finding in findings:
        print(f"FAILED {finding}")
    if findings:
        raise SystemExit(1)
    print("Repository checks: OK")


if __name__ == "__main__":
    main()

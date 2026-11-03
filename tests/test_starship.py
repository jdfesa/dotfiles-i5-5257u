"""Bounded prompt checks: isolated homes/repos, never the user's credentials."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config/starship/starship.toml"
CONFIG = tomllib.loads(PROFILE.read_text())
STARSHIP = shutil.which("starship")
GIT = shutil.which("git")


class StarshipSourceTests(unittest.TestCase):
    def test_profile_is_individually_managed(self):
        entries = json.loads((ROOT / "config/manifest.json").read_text())
        entry = next(e for e in entries if e["source"] == "config/starship/starship.toml")
        self.assertEqual(entry["destination"], ".config/starship.toml")
        self.assertEqual(entry["mode"], 0o644)
        self.assertEqual(entry["deployment"], "symlink")

    def test_active_reference_layout_and_palette_are_retained(self):
        self.assertEqual(CONFIG["palette"], "catppuccin_mocha")
        self.assertEqual(CONFIG["right_format"].strip(), "$all")
        self.assertEqual(CONFIG["directory"]["truncation_length"], 4)
        self.assertIn("${custom.giturl}", CONFIG["format"])
        self.assertIn("${custom.git_worktree}", CONFIG["format"])
        self.assertFalse(CONFIG["add_newline"])

    def test_custom_modules_have_explicit_posix_shell_and_timeouts(self):
        self.assertEqual(CONFIG["scan_timeout"], 100)
        self.assertEqual(CONFIG["command_timeout"], 500)
        self.assertFalse(CONFIG["follow_symlinks"])
        for module in CONFIG["custom"].values():
            self.assertFalse(module["ignore_timeout"])
            self.assertTrue(module["require_repo"])
            self.assertEqual(module["shell"], ["sh"])
            for key in ("command", "when"):
                subprocess.run(["sh", "-n"], input=module[key], text=True, check=True)
                self.assertNotIn("[[", module[key])
                self.assertNotIn("eval", module[key])

    @unittest.skipUnless(shutil.which("fc-query"), "fontconfig not available")
    def test_configured_nerd_font_icons_exist_in_the_managed_font(self):
        charset = subprocess.check_output(
            ["fc-query", "--format", "%{charset}",
             str(ROOT / "config/fonts/JetBrainsMonoNerdFontMono-Regular.ttf")], text=True)
        ranges = [tuple(int(p, 16) for p in chunk.split("-")) for chunk in charset.split()]
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for child in value.values():
                    yield from strings(child)
            elif isinstance(value, list):
                for child in value:
                    yield from strings(child)
        points = {ord(c) for s in strings(CONFIG) for c in s
                  if 0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c) <= 0x10FFFD}
        self.assertTrue(points)
        missing = [f"U+{cp:X}" for cp in sorted(points)
                   if not any(r[0] <= cp <= r[-1] for r in ranges)]
        self.assertEqual(missing, [])
        self.assertNotIn("\uf7a1", PROFILE.read_text())


@unittest.skipUnless(STARSHIP and GIT, "Starship/Git not installed on this host")
class StarshipRuntimeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        home = self.root / "home"
        home.mkdir(mode=0o700)
        cache = self.root / "cache"
        cache.mkdir(mode=0o700)
        # Intentionally do not inherit cloud/context, Git, prompt or shell env.
        self.env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home),
                    "XDG_CONFIG_HOME": str(home / ".config"),
                    "STARSHIP_CACHE": str(cache), "STARSHIP_CONFIG": str(PROFILE),
                    "STARSHIP_SHELL": "zsh", "TERM": "xterm-kitty", "LANG": "C.UTF-8",
                    "TMPDIR": str(self.root),
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_TERMINAL_PROMPT": "0"}
        self.repo = self.root / "repo"
        subprocess.run([GIT, "init", "-q", "-b", "main", str(self.repo)],
                       env=self.env, check=True)

    def git(self, *args):
        return subprocess.run([GIT, "-C", str(self.repo), *args], env=self.env,
                              capture_output=True, text=True, check=True)

    def starship(self, *args, path=None, env=None):
        return subprocess.run([STARSHIP, *args], cwd=path or self.repo,
                              env=env or self.env, capture_output=True, text=True, timeout=5)

    def test_packaged_parser_and_empty_directory_prompt(self):
        result = self.starship("print-config")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(result.stderr, result.stderr)
        tomllib.loads(result.stdout)
        for extra in ([], ["--right"]):
            result = self.starship("prompt", "--terminal-width", "120", *extra,
                                   path=self.root / "home")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(result.stderr, result.stderr)
        self.assertIn("", self.starship("module", "character").stdout)

    def test_remote_indicator_uses_only_local_url_resolution(self):
        for url, symbol in (("https://github.com/example/fixture.git", ""),
                            ("https://gitlab.com/example/fixture.git", ""),
                            ("https://bitbucket.org/example/fixture.git", ""),
                            ("https://git.example.invalid/fixture", ""),
                            ("/tmp/fixture", "")):
            with self.subTest(symbol=symbol):
                self.git("config", "remote.origin.url", url)
                result = self.starship("module", "custom.giturl")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(result.stderr, result.stderr)
                self.assertIn(symbol, result.stdout)

    def test_branch_and_untracked_status_render(self):
        (self.repo / "fixture.txt").write_text("fixture\n")
        result = self.starship("prompt", "--terminal-width", "120")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(result.stderr, result.stderr)
        self.assertIn("main", result.stdout)
        self.assertIn("?1", result.stdout)

    def test_linked_worktree_indicator(self):
        (self.repo / "fixture.txt").write_text("fixture\n")
        self.git("add", "fixture.txt")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                 "commit", "-qm", "fixture")
        linked = self.root / "linked"
        self.git("worktree", "add", "--quiet", "--detach", str(linked))
        self.assertEqual(self.starship("module", "custom.git_worktree").stdout.strip(), "")
        result = self.starship("module", "custom.git_worktree", path=linked)
        self.assertFalse(result.stderr, result.stderr)
        self.assertIn("⛓", result.stdout)

    def test_slow_custom_git_command_is_bounded(self):
        binary = self.root / "bin"
        binary.mkdir()
        fake = binary / "git"
        fake.write_text('#!/bin/sh\ncase "$*" in\n'
                        '"ls-remote --get-url") exec sleep 4 ;;\n'
                        f'*) exec "{GIT}" "$@" ;;\nesac\n')
        fake.chmod(0o700)
        start = time.monotonic()
        result = self.starship("module", "custom.giturl",
                               env={**self.env, "PATH": str(binary) + ":" + self.env["PATH"]})
        self.assertLess(time.monotonic() - start, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("timed out", result.stderr)


if __name__ == "__main__":
    unittest.main()

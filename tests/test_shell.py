from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("zsh"), "Zsh is not installed on this host")
class ShellTests(unittest.TestCase):
    def test_clean_interactive_start_creates_only_private_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            env = {**os.environ, "HOME": str(root), "ZDOTDIR": str(root),
                   "XDG_STATE_HOME": str(root / "state"), "XDG_CACHE_HOME": str(root / "cache")}
            result = subprocess.run(["zsh", "-dfi", "-c", 'source "$1"; print -r -- "zsh-ready"',
                                     "test-shell", str(ROOT / "config/zsh/zshrc")],
                                    env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("zsh-ready", result.stdout)
            self.assertEqual((root / "state/zsh/history").stat().st_mode & 0o777, 0o600)
            self.assertEqual((root / "state/zsh").stat().st_mode & 0o777, 0o700)

    def test_shell_syntax(self):
        for name in ("zshrc", "zprofile"):
            subprocess.run(["zsh", "-n", str(ROOT / "config/zsh" / name)], check=True)

    def run_prompt_shell(self, directory, **extra):
        root = Path(directory).resolve()
        config = root / ".config"
        config.mkdir()
        (config / "starship.toml").symlink_to(ROOT / "config/starship/starship.toml")
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(root),
               "ZDOTDIR": str(root), "XDG_CONFIG_HOME": str(config),
               "XDG_STATE_HOME": str(root / "state"), "XDG_CACHE_HOME": str(root / "cache"),
               "TMPDIR": str(root), "TERM": "xterm-kitty", **extra}
        code = ('source "$1"; print -r -- "hook=${+functions[prompt_starship_precmd]}"; '
                'print -r -- "cache=${STARSHIP_CACHE:-none}"; print -r -- "mask=$(umask)"')
        return subprocess.run(["zsh", "-dfi", "-c", code, "test-prompt",
                               str(ROOT / "config/zsh/zshrc")], env=env,
                              capture_output=True, text=True, timeout=15)

    @unittest.skipUnless(shutil.which("starship"), "Starship not installed on this host")
    def test_starship_initializes_with_private_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_prompt_shell(directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(result.stderr, result.stderr)
            self.assertIn("hook=1", result.stdout)
            cache = Path(directory) / "cache/starship"
            self.assertEqual(cache.stat().st_mode & 0o777, 0o700)

    def test_prompt_recovery_and_incompatible_terminal_guards(self):
        for extra in ({"MBP_SIMPLE_PROMPT": "1"}, {"TERM": "dumb"},
                      {"NETBEANS_USERDIR": "/fixture/netbeans"}):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                result = self.run_prompt_shell(directory, **extra)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("hook=0", result.stdout)
                self.assertFalse((Path(directory) / "cache/starship").exists())

    def test_noninteractive_shell_does_not_initialize_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["zsh", "-df", "-c", 'source "$1"; print -r -- "hook=${+functions[prompt_starship_precmd]}"',
                 "test-noninteractive", str(ROOT / "config/zsh/zshrc")],
                env={"PATH": os.environ["PATH"], "HOME": directory, "ZDOTDIR": directory},
                capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hook=0", result.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()

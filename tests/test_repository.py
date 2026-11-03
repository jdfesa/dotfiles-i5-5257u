import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("repository_checks", ROOT / "tools/check-repository.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class RepositoryTests(unittest.TestCase):
    def test_current_working_tree_passes_static_checks(self):
        _, _, findings = checks.audit(ROOT)
        self.assertEqual(findings, [])

    def test_token_patterns_are_detected_without_echoing_values(self):
        sample = b"gh" + b"p_" + b"A" * 36
        self.assertIn("github-token", checks.content_findings(sample))
        sample = b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----"
        self.assertIn("key-block", checks.content_findings(sample))

    def test_documentation_addresses_and_digests_are_not_mistaken_for_values(self):
        self.assertEqual(checks.content_findings(b"https://example.org/docs " + b"a" * 64), [])

    def test_additional_high_confidence_credentials_are_detected(self):
        samples = [("service-api-key", b"sk-" + b"proj-" + b"A" * 40),
                   ("service-api-key", b"sk-" + b"ant-" + b"B" * 40),
                   ("google-api-key", b"AI" + b"za" + b"C" * 35),
                   ("slack-token", b"xox" + b"b-" + b"D" * 30),
                   ("key-block", b"-----BEGIN " + b"PGP PRIVATE KEY BLOCK-----"),
                   ("url-userinfo", b"ssh://" + b"fixture:fixture@" + b"example.invalid/path")]
        for category, value in samples:
            with self.subTest(category=category):
                self.assertIn(category, checks.content_findings(value))

    def test_environment_names_and_url_ports_remain_valid_documentation(self):
        self.assertEqual(checks.content_findings(
            b"OPENAI_API_KEY ANTHROPIC_API_KEY https://example.org:443/path"), [])

    def test_dangling_public_symlinks_remain_in_the_review_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "dangling").symlink_to("missing")
            self.assertIn("dangling", checks.working_files(root))


if __name__ == "__main__":
    unittest.main()

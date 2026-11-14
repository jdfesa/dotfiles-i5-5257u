"""Offline tests: fake HTTPS downloads, real XAMPP PHP, isolated user home."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHP = Path('/opt/lampp/bin/php')
PAYLOAD = '''<?php
if (in_array('--version', $argv, true)) {
    echo "Composer version TEST\\n";
} else {
    echo json_encode([
        'args' => array_slice($argv, 1),
        'php' => PHP_BINARY,
        'ca' => ini_get('openssl.cafile'),
        'curl_ca' => ini_get('curl.cainfo'),
        'path' => getenv('PATH'),
    ]);
}
'''
INSTALLER = '''<?php
$options = getopt('', ['2', 'install-dir:', 'filename:']);
file_put_contents(getenv('INSTALLER_MARKER'), 'executed');
file_put_contents($options['install-dir'].'/'.$options['filename'],
                  base64_decode('%s'));
''' % base64.b64encode(PAYLOAD.encode()).decode()
MOCK_CURL = '''#!/usr/bin/python3
import hashlib, os, pathlib, sys
url = next(arg for arg in sys.argv[1:] if arg.startswith('https://'))
with open(os.environ['URL_LOG'], 'a') as log:
    log.write(url + '\\n')
if os.environ.get('TEST_NETWORK_FAIL') == '1':
    sys.exit(6)
data = pathlib.Path(os.environ['INSTALLER_FIXTURE']).read_bytes()
if url.endswith('installer.sig'):
    data = (('0' * 96) if os.environ.get('TEST_BAD_SIG') == '1'
            else hashlib.sha384(data).hexdigest()).encode() + b'\\n'
target = pathlib.Path(sys.argv[sys.argv.index('-o') + 1])
target.write_bytes(data)
'''


@unittest.skipUnless(PHP.is_file(), 'Requires the existing XAMPP PHP CLI')
class ComposerInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='composer-offline-tests-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / 'home with spaces'
        self.home.mkdir()
        self.work = self.base / 'temporary downloads'
        self.work.mkdir()
        self.bin = self.base / 'mock-bin'
        self.bin.mkdir()
        self.fixture = self.base / 'official-installer-fixture.php'
        self.fixture.write_text(INSTALLER)
        self.marker = self.base / 'installer-executed'
        self.url_log = self.base / 'urls'
        (self.bin / 'curl').write_text(MOCK_CURL)
        (self.bin / 'curl').chmod(0o755)
        (self.bin / 'id').write_text('#!/bin/sh\nprintf "%s\\n" "${TEST_UID:-1000}"\n')
        (self.bin / 'id').chmod(0o755)
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith(('COMPOSER_', 'TEST_'))}
        self.env.update(HOME=str(self.home), TMPDIR=str(self.work),
                        PATH=f'{self.bin}:{os.environ["PATH"]}',
                        INSTALLER_FIXTURE=str(self.fixture),
                        INSTALLER_MARKER=str(self.marker), URL_LOG=str(self.url_log))

    def install(self, *args, **env):
        return subprocess.run(['sh', str(ROOT / 'tools/install-composer.sh'), *args],
                              env={**self.env, **env}, capture_output=True,
                              text=True, timeout=15)

    def assert_not_installed(self):
        self.assertFalse(self.marker.exists())
        self.assertFalse((self.home / '.local/share/composer/composer.phar').exists())
        self.assertEqual(list(self.work.iterdir()), [])

    def test_installs_only_verified_phar_without_root(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.marker.exists())
        self.assertEqual(self.url_log.read_text().splitlines(), [
            'https://composer.github.io/installer.sig',
            'https://getcomposer.org/installer'])
        self.assertEqual(list(self.work.iterdir()), [])
        self.assertFalse((self.home / '.local/bin').exists())
        payload = self.home / '.local/share/composer/composer.phar'
        self.assertEqual(payload.read_text(), PAYLOAD)
        self.assertEqual(payload.stat().st_mode & 0o777, 0o644)
        composer = ROOT / 'scripts/xampp/composer'
        probe = subprocess.run([str(composer), 'demo', 'two words', '--flag'],
                               env=self.env, text=True, capture_output=True, check=True)
        data = json.loads(probe.stdout)
        self.assertEqual(data['args'], ['demo', 'two words', '--flag'])
        self.assertEqual(data['php'], str(PHP.resolve()))
        self.assertEqual(data['ca'], '/etc/ssl/certs/ca-certificates.crt')
        self.assertEqual(data['curl_ca'], data['ca'])
        self.assertTrue(data['path'].startswith(str(self.home / '.local/bin') + ':'))

    def test_mismatched_checksum_never_executes_installer(self):
        result = self.install(TEST_BAD_SIG='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SHA-384 verification failed', result.stderr)
        self.assert_not_installed()

    def test_network_failure_leaves_no_installation_or_downloads(self):
        result = self.install(TEST_NETWORK_FAIL='1')
        self.assertEqual(result.returncode, 6)
        self.assert_not_installed()

    def test_refuses_root(self):
        result = self.install(TEST_UID='0')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('without sudo', result.stderr)
        self.assert_not_installed()
        self.assertFalse(self.url_log.exists())

    def test_invalid_arguments_do_not_download(self):
        result = self.install('--unexpected')
        self.assertNotEqual(result.returncode, 0)
        self.assert_not_installed()
        self.assertFalse(self.url_log.exists())

    def test_rejects_symlinked_data_parent(self):
        outside = self.base / 'outside'
        outside.mkdir()
        local = self.home / '.local'
        local.mkdir()
        (local / 'share').symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(self.url_log.exists())

    def test_symlinked_phar_is_not_overwritten_or_followed(self):
        original = self.base / 'original'
        original.write_text('preserve me')
        target = self.home / '.local/share/composer/composer.phar'
        target.parent.mkdir(parents=True)
        target.symlink_to(original)
        self.assertNotEqual(self.install().returncode, 0)
        self.assertTrue(target.is_symlink())
        self.assertEqual(original.read_text(), 'preserve me')
        self.assertFalse(self.url_log.exists())

    def test_nonregular_phar_is_rejected_before_download(self):
        target = self.home / '.local/share/composer/composer.phar'
        target.mkdir(parents=True)
        self.assertNotEqual(self.install().returncode, 0)
        self.assertTrue(target.is_dir())
        self.assertFalse(self.url_log.exists())

    def test_failed_verification_preserves_existing_phar(self):
        target = self.home / '.local/share/composer/composer.phar'
        target.parent.mkdir(parents=True)
        target.write_text('previous version')
        self.assertNotEqual(self.install(TEST_BAD_SIG='1').returncode, 0)
        self.assertEqual(target.read_text(), 'previous version')
        self.assertEqual(list(self.work.iterdir()), [])

    def test_reinstall_replaces_regular_phar(self):
        first = self.install()
        self.assertEqual(first.returncode, 0, first.stderr)
        target = self.home / '.local/share/composer/composer.phar'
        target.write_text('previous version')
        second = self.install()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(target.read_text(), PAYLOAD)
        self.assertEqual(list(target.parent.iterdir()), [target])
        self.assertEqual(list(self.work.iterdir()), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)

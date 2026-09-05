"""Execute the workflow's Python gate with mocked macOS commands, not fake apps.

The temporary CodeResources bytes below are unit-test input only. Real codesign,
quarantine and Gatekeeper checks must still run on both macOS CI runners.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest
from unittest import mock

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/sync-hermes-desktop.yml'
VERIFY_STEP = 'Verify installed code seals and assess Gatekeeper without bypasses'
LOG_STEP = 'Retain installed signature and Gatekeeper evidence'


def step_text(name):
    # Keep the test suite stdlib-only; extract a named six-space-indented step.
    text = WORKFLOW.read_text()
    match = re.search(r'^      - name: ' + re.escape(name) + r'\n((?:^        .*\n|^\n)*)', text, re.M)
    if not match:
        raise AssertionError(f'Missing workflow step: {name}')
    return match[1]


class InstalledSigningWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='hermes workflow unit ')
        self.addCleanup(self.temp.cleanup)
        self.runner_temp = Path(self.temp.name)
        self.app = self.runner_temp / 'hermes-cask-apps/Hermes.app'
        self.seal = self.app / 'Contents/_CodeSignature/CodeResources'
        self.seal.parent.mkdir(parents=True)
        self.seal.write_bytes(b'unit-test resource seal bytes; not a signed app\n')
        self.logs = self.runner_temp / 'hermes-cask-signing'
        self.responses = {
            'codesign': (0, b'', b'Hermes.app: valid on disk\n'),
            'gatekeeper-status': (0, b'assessments enabled\n', b''),
            'quarantine': (0, b'0083;unit-test;Homebrew Cask;unit-test\n', b''),
            'gatekeeper-assessment': (3, b'', f'{self.app}: rejected\nsource=no usable signature\n'.encode()),
        }
        self.commands = []

    def run_verification(self):
        step = step_text(VERIFY_STEP)
        self.assertIn('        shell: python\n', step)
        self.assertIn('        run: |\n', step)
        code = textwrap.dedent(step.split('        run: |\n', 1)[1])

        def run(command, **kwargs):
            self.assertEqual(kwargs, {'capture_output': True})
            self.commands.append(command)
            if command[0] == '/usr/bin/codesign':
                name = 'codesign'
            elif command[0] == '/usr/bin/xattr':
                name = 'quarantine'
            elif '--status' in command:
                name = 'gatekeeper-status'
            else:
                name = 'gatekeeper-assessment'
            returncode, stdout, stderr = self.responses[name]
            return subprocess.CompletedProcess(command, returncode, stdout, stderr)

        with mock.patch.dict(os.environ, {'RUNNER_TEMP': str(self.runner_temp)}), mock.patch(
            'subprocess.run', side_effect=run
        ):
            exec(compile(code, str(WORKFLOW), 'exec'), {})

    def test_valid_seal_and_expected_gatekeeper_rejection_keep_raw_evidence(self):
        self.run_verification()
        self.assertEqual(self.commands, [
            ['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', str(self.app)],
            ['/usr/sbin/spctl', '--status'],
            ['/usr/bin/xattr', '-p', 'com.apple.quarantine', str(self.app)],
            ['/usr/sbin/spctl', '--assess', '--type', 'execute', '--verbose=4', str(self.app)],
        ])
        for name, (returncode, stdout, stderr) in self.responses.items():
            self.assertEqual((self.logs / f'{name}.stdout.log').read_bytes(), stdout)
            self.assertEqual((self.logs / f'{name}.stderr.log').read_bytes(), stderr)
            self.assertEqual(json.loads((self.logs / f'{name}.json').read_text())['exitCode'], returncode)
        self.assertEqual((self.logs / 'CodeResources').read_bytes(), self.seal.read_bytes())
        report = json.loads((self.logs / 'verification.json').read_text())
        self.assertTrue(report['bundleVerified'])
        self.assertEqual(report['rootCodeResources']['path'], str(self.seal))
        self.assertEqual(report['rootCodeResources']['sha256'], hashlib.sha256(self.seal.read_bytes()).hexdigest())
        self.assertEqual(report['gatekeeper'], {
            'enabled': True, 'quarantinePresent': True, 'accepted': False,
            'exitCode': 3, 'assessment': 'unnotarized-ad-hoc',
        })

    def test_missing_or_empty_root_seal_stops_before_assessment(self):
        for absent in (False, True):
            with self.subTest(absent=absent):
                self.seal.write_bytes(b'')
                if absent:
                    self.seal.unlink()
                with self.assertRaisesRegex(RuntimeError, 'CodeResources'):
                    self.run_verification()
                self.assertFalse(self.commands)
                self.assertFalse((self.logs / 'verification.json').exists())

    def test_codesign_failure_preserves_logs_and_stops_before_assessment(self):
        self.responses['codesign'] = (1, b'', b'code has no resources but signature indicates they must be present\n')
        with self.assertRaisesRegex(RuntimeError, 'codesign'):
            self.run_verification()
        self.assertEqual(len(self.commands), 1)
        self.assertEqual((self.logs / 'codesign.stderr.log').read_bytes(), self.responses['codesign'][2])
        self.assertFalse((self.logs / 'verification.json').exists())

    def test_disabled_gatekeeper_or_absent_quarantine_is_not_a_pass(self):
        valid = self.responses.copy()
        for name, response in (
            ('gatekeeper-status', (0, b'assessments disabled\n', b'')),
            ('gatekeeper-status', (1, b'assessments enabled\n', b'')),
            ('quarantine', (1, b'', b'No such xattr: com.apple.quarantine\n')),
            ('quarantine', (0, b'', b'')),
        ):
            with self.subTest(name=name, response=response):
                self.responses = {**valid, name: response}
                self.commands.clear()
                with self.assertRaises(RuntimeError):
                    self.run_verification()
                self.assertFalse(any('--assess' in c for c in self.commands))
                self.assertFalse((self.logs / 'verification.json').exists())

    def test_gatekeeper_must_reject_with_exit_three_without_bad_seal_errors(self):
        invalids = [
            (0, b'Hermes.app: accepted\n', b''),
            (3, b'Hermes.app: accepted\n', b''),
            (3, b'Hermes.app: rejected\nHermes.app: accepted\n', b''),
            (1, b'', b'Hermes.app: rejected\n'),
            (3, b'', b'spctl crashed\n'),
            (3, b'', b'Hermes.app: rejected\nmissing CodeResources\n'),
            (3, b'', b'Hermes.app: rejected\ncode has no resources but signature indicates they must be present\n'),
            (3, b'', b'Hermes.app: rejected\na sealed resource is missing or invalid\n'),
            (3, b'', b'Hermes.app: rejected\nresource envelope is obsolete\n'),
            (3, b'', b'Hermes.app: rejected\ninvalid signature\n'),
            (3, b'', b'Hermes.app: rejected\ncode object is not signed at all\n'),
        ]
        for response in invalids:
            with self.subTest(response=response):
                self.responses['gatekeeper-assessment'] = response
                with self.assertRaisesRegex(RuntimeError, 'Gatekeeper'):
                    self.run_verification()
                self.assertEqual((self.logs / 'gatekeeper-assessment.stderr.log').read_bytes(), response[2])
                self.assertFalse((self.logs / 'verification.json').exists())

    def test_ci_verifies_actual_brew_install_on_both_architectures_and_uploads_failures(self):
        text = WORKFLOW.read_text()
        self.assertIn('runner: [macos-15, macos-15-intel]', text)
        self.assertIn('brew install --cask --appdir="$RUNNER_TEMP/hermes-cask-apps" frankhommers/tap/hermes-desktop', text)
        self.assertLess(text.index('brew install --cask'), text.index('- name: ' + VERIFY_STEP))
        self.assertLess(text.index('- name: ' + VERIFY_STEP), text.index('  publish:'))
        self.assertIn('needs: [prepare, validate]', text)
        upload = step_text(LOG_STEP)
        self.assertIn('        if: always()\n', upload)
        self.assertIn('uses: actions/upload-artifact@', upload)
        self.assertIn('name: hermes-cask-signing-${{ matrix.runner }}', upload)
        self.assertIn('path: ${{ runner.temp }}/hermes-cask-signing', upload)
        for forbidden in ('--master-disable', '--global-disable', '--no-quarantine', 'xattr -d', 'xattr -c'):
            self.assertNotIn(forbidden, text)


if __name__ == '__main__':
    unittest.main()

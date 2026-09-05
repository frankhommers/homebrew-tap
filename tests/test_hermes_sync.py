import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_hermes', ROOT / 'scripts/sync-hermes-desktop.py')
assert spec is not None and spec.loader is not None
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def signing_fixture():
    return {
        'schema': 1,
        'mode': 'ad-hoc',
        'developerID': False,
        'notarized': False,
        'stagedNativeCount': 7,
        'bundleVerified': True,
        'archiveVerified': True,
        'nativePayloadsVerified': 7,
        'tamperRejected': True,
        'missingSealRejected': True,
        'gatekeeper': {
            'enabled': True,
            'quarantinePresent': True,
            'accepted': False,
            'exitCode': 3,
            'assessment': 'unnotarized-ad-hoc',
        },
    }


class SyncTests(unittest.TestCase):
    def fixture(self):
        # Metadata-only unit fixture; no app or pretend release is produced.
        manifest = {
            'schema': 1, 'buildRepository': sync.REPO, 'version': '0.17.0.2',
            'buildRun': f'https://github.com/{sync.REPO}/actions/runs/123', 'targets': {},
        }
        for platform, arch in [('darwin', 'arm64'), ('darwin', 'x64'), ('win32', 'x64'), ('linux', 'x64')]:
            suffix = 'adhoc' if platform == 'darwin' else 'unsigned'
            target = {
                'archive': f'Hermes-0.17.0.2-{platform}-{arch}-{suffix}.zip',
                'sha256': ('1' if arch == 'arm64' else '2') * 64,
                'sourceClean': True, 'archiveRoundtrip': True,
                'nativeSmoke': {'platform': platform, 'arch': arch, 'errors': []},
            }
            if platform == 'darwin':
                target['macSigning'] = signing_fixture()
            manifest['targets'][platform + '-' + arch] = target
        return manifest

    def release(self, manifest):
        base = f'https://github.com/{sync.REPO}/releases/download/v{manifest["version"]}'
        names = ['release-manifest.json'] + [t['archive'] for t in manifest['targets'].values()]
        return {
            'tag_name': 'v' + manifest['version'], 'draft': False,
            'assets': [{'name': n, 'browser_download_url': f'{base}/{n}'} for n in names],
        }

    def run_sync(self, output, manifest, release=None):
        release = release if release is not None else self.release(manifest)
        with mock.patch.object(sync, 'get_json', side_effect=[release, manifest]), mock.patch(
            'sys.argv', ['sync-hermes-desktop.py', '--version', manifest['version'], '--output', str(output)]
        ):
            sync.main()

    def test_cask_has_no_security_or_agent_hooks(self):
        text = sync.render(self.fixture())
        self.assertIn('app "Hermes.app"', text)
        for forbidden in ('postflight', 'preflight', 'system_command', 'xattr', 'spctl', 'installer', 'sha256 :no_check'):
            self.assertNotIn(forbidden, text)

    def test_render_uses_exact_adhoc_assets_for_both_architectures(self):
        text = sync.render(self.fixture())
        dependency = next(line.strip() for line in text.splitlines() if line.strip().startswith('depends_on macos:'))
        self.assertRegex(dependency, r'^depends_on macos: :[a-z][a-z0-9_]*$')
        self.assertNotIn('verified:', text)
        self.assertIn('  version "0.17.0.2"', text)
        for arch, digest in [('arm64', '1' * 64), ('x64', '2' * 64)]:
            self.assertIn(f'/v#{{version}}/Hermes-#{{version}}-darwin-{arch}-adhoc.zip"', text)
            self.assertIn(f'    sha256 "{digest}"', text)
        self.assertNotIn('-unsigned.zip', text)

    def test_caveats_describe_signing_without_changing_remaining_guidance(self):
        caveats = sync.render(self.fixture()).split('  caveats <<~EOS\n')[1].split('  EOS')[0]
        self.assertEqual(caveats, '''    Ad-hoc signed community build; no Developer ID or Apple notarization.
    Gatekeeper remains enabled; app-specific approval may be required.
    Choose "Connect to existing Hermes", not "Install Hermes locally".
    An existing local Hermes runtime may be discovered and started by upstream.
    Review existing installations before launching if local startup must be avoided.
    No Python agent is installed by this cask. Updates use brew upgrade, not the in-app updater.
''')

    def test_missing_or_mismatched_build_blocks(self):
        mutations = [
            lambda m: m['targets'].pop('linux-x64'),
            lambda m: m.update(buildRepository='untrusted/repo'),
            lambda m: m['targets']['darwin-arm64'].update(sha256='no_check'),
            lambda m: m['targets']['darwin-x64']['nativeSmoke'].update(arch='arm64'),
        ]
        for mutation in mutations:
            manifest = self.fixture()
            mutation(manifest)
            with self.assertRaises(ValueError):
                sync.render(manifest)

    def test_archive_filename_injections_and_unsigned_names_are_rejected(self):
        for arch in ('arm64', 'x64'):
            name = self.fixture()['targets']['darwin-' + arch]['archive']
            for invalid in (name.replace('-adhoc.zip', '-unsigned.zip'), '../' + name, name + '\n',
                            name + '?download=1', name + '"\n  postflight do', '#{system("id")}.zip'):
                with self.subTest(arch=arch, archive=invalid):
                    manifest = self.fixture()
                    manifest['targets']['darwin-' + arch]['archive'] = invalid
                    with self.assertRaises(ValueError):
                        sync.render(manifest)

    def test_version_and_checksum_injections_are_rejected(self):
        for version in ('main', '0.17.0.2\n', '0.17.0.2/../evil', '0.17.0.2"\nend', '#{system("id")}', 'v0.17.0.2'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                sync.version_tuple(version)
        for digest in ('1' * 64 + '\n', '1' * 64 + '"', '#{system("id")}', 'A' * 64):
            manifest = self.fixture()
            manifest['targets']['darwin-arm64']['sha256'] = digest
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                sync.render(manifest)

    def test_versions_are_compared_numerically(self):
        self.assertGreater(sync.version_tuple('0.17.0.10'), sync.version_tuple('0.17.0.9'))

    def test_main_writes_adhoc_cask_and_leaves_other_casks_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'casks/hermes-desktop.rb'
            other = output.with_name('other.rb')
            other.parent.mkdir()
            other.write_text('untouched cask\n')
            self.run_sync(output, self.fixture())
            self.assertEqual(output.read_text(), sync.render(self.fixture()))
            self.assertEqual(other.read_text(), 'untouched cask\n')
            self.run_sync(output, self.fixture())  # Idempotent for the same immutable release.

    def test_main_requires_published_adhoc_assets_for_each_mac(self):
        for arch in ('arm64', 'x64'):
            with self.subTest(arch=arch), tempfile.TemporaryDirectory() as directory:
                manifest = self.fixture()
                release = self.release(manifest)
                name = manifest['targets']['darwin-' + arch]['archive']
                release['assets'] = [a for a in release['assets'] if a['name'] != name]
                release['assets'].append({'name': name.replace('-adhoc.zip', '-unsigned.zip')})
                output = Path(directory) / 'hermes-desktop.rb'
                with self.assertRaisesRegex(ValueError, 'Missing Mac ZIP asset'):
                    self.run_sync(output, manifest, release)
                self.assertFalse(output.exists())

    def assert_signing_rejected(self, signing):
        for arch in ('arm64', 'x64'):
            with self.subTest(arch=arch):
                manifest = self.fixture()
                manifest['targets']['darwin-' + arch]['macSigning'] = copy.deepcopy(signing)
                with self.assertRaisesRegex(ValueError, 'Mac signing'):
                    sync.render(manifest)

    def test_missing_mac_signing_cannot_be_replaced_by_adhoc_filename(self):
        for arch in ('arm64', 'x64'):
            manifest = self.fixture()
            del manifest['targets']['darwin-' + arch]['macSigning']
            with self.subTest(arch=arch), self.assertRaisesRegex(ValueError, 'Mac signing'):
                sync.render(manifest)

    def test_mac_signing_must_be_an_object(self):
        for invalid in (None, False, True, 1, 'ad-hoc', [], {}):
            with self.subTest(signing=invalid):
                self.assert_signing_rejected(invalid)

    def test_each_signing_and_gatekeeper_field_is_required(self):
        for group in (None, 'gatekeeper'):
            fields = signing_fixture() if group is None else signing_fixture()[group]
            for field in fields:
                with self.subTest(group=group, missing=field):
                    signing = signing_fixture()
                    del (signing if group is None else signing[group])[field]
                    self.assert_signing_rejected(signing)

    def test_proof_flags_require_literal_booleans(self):
        groups = {
            None: {
                'developerID': False, 'notarized': False,
                'bundleVerified': True, 'archiveVerified': True,
                'tamperRejected': True, 'missingSealRejected': True,
            },
            'gatekeeper': {'enabled': True, 'quarantinePresent': True, 'accepted': False},
        }
        for group, fields in groups.items():
            for field, expected in fields.items():
                for invalid in (not expected, int(expected), str(expected).lower(), None, [], {}):
                    with self.subTest(group=group, field=field, invalid=invalid):
                        signing = signing_fixture()
                        (signing if group is None else signing[group])[field] = invalid
                        self.assert_signing_rejected(signing)

    def test_signing_schema_mode_and_gatekeeper_outcome_are_exact(self):
        cases = [
            (None, 'schema', (True, False, 1.0, '1', 0, 2, None)),
            (None, 'mode', ('unsigned', 'adhoc', 'developer-id', True, None)),
            (None, 'gatekeeper', (None, True, 3, [], 'rejected')),
            ('gatekeeper', 'exitCode', (True, 3.0, '3', 0, 1, 2, None)),
            ('gatekeeper', 'assessment', ('accepted', 'unsigned', 'missing-seal', '', None)),
        ]
        for group, field, invalids in cases:
            for invalid in invalids:
                with self.subTest(group=group, field=field, invalid=invalid):
                    signing = signing_fixture()
                    (signing if group is None else signing[group])[field] = invalid
                    self.assert_signing_rejected(signing)

    def test_native_counts_are_positive_integers_and_all_staged_payloads_verified(self):
        for field in ('stagedNativeCount', 'nativePayloadsVerified'):
            for invalid in (True, False, 0, -1, 7.0, '7', None, [], {}):
                with self.subTest(field=field, invalid=invalid):
                    signing = signing_fixture()
                    signing[field] = invalid
                    self.assert_signing_rejected(signing)
        for count in (6, 8):
            signing = signing_fixture()
            signing['nativePayloadsVerified'] = count
            self.assert_signing_rejected(signing)
        manifest = self.fixture()
        for arch, count in [('arm64', 1), ('x64', 19)]:
            manifest['targets']['darwin-' + arch]['macSigning'].update(
                stagedNativeCount=count, nativePayloadsVerified=count,
            )
        sync.render(manifest)

    def test_release_schema_and_existing_proofs_are_strictly_typed(self):
        for schema in (True, 1.0, '1', None, 2):
            manifest = self.fixture()
            manifest['schema'] = schema
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                sync.render(manifest)
        for field in ('sourceClean', 'archiveRoundtrip'):
            for invalid in (False, 1, 'true', None, [], {}):
                manifest = self.fixture()
                manifest['targets']['darwin-arm64'][field] = invalid
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    sync.render(manifest)
        for invalid in (False, 0, '', None, {}, ['failed']):
            manifest = self.fixture()
            manifest['targets']['darwin-x64']['nativeSmoke']['errors'] = invalid
            with self.subTest(errors=invalid), self.assertRaises(ValueError):
                sync.render(manifest)

    def test_non_string_and_non_ascii_versions_are_rejected(self):
        for version in (None, True, 17, ['0.17.0.2'], '０.１７.０.２'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                sync.version_tuple(version)

    def test_failed_signing_proof_leaves_existing_cask_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'hermes-desktop.rb'
            old = sync.render(self.fixture()).replace('0.17.0.2', '0.17.0.1')
            output.write_text(old)
            manifest = self.fixture()
            del manifest['targets']['darwin-x64']['macSigning']
            with self.assertRaisesRegex(ValueError, 'Mac signing'):
                self.run_sync(output, manifest)
            self.assertEqual(output.read_text(), old)

    def test_main_refuses_immutable_version_changes_and_downgrades(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'hermes-desktop.rb'
            for old in (sync.render(self.fixture()).replace('1' * 64, 'f' * 64),
                        sync.render(self.fixture()).replace('0.17.0.2', '0.17.0.3')):
                output.write_text(old)
                with self.assertRaises(ValueError):
                    self.run_sync(output, self.fixture())
                self.assertEqual(output.read_text(), old)


if __name__ == '__main__':
    unittest.main()

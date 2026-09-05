import copy
import importlib.util
import hashlib
import io
import json
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
    def test_actions_token_is_used_only_for_https_github_api_not_downloads(self):
        for url, expected in [('https://api.github.com/repos/x/y/releases', 'Bearer unit-test-token'),
                              ('https://github.com/x/y/releases/download/v1/manifest.json', None),
                              ('https://example.invalid/', None),
                              ('http://api.github.com/repos/x/y/releases', None)]:
            with self.subTest(url=url), mock.patch.dict('os.environ', {'GH_TOKEN': 'unit-test-token'}, clear=True), mock.patch.object(
                sync.urllib.request, 'urlopen', return_value=io.BytesIO(b'{}')
            ) as opener:
                sync.get_json(url)
                request = opener.call_args.args[0]
                self.assertEqual(request.get_header('Authorization'), expected)
                self.assertNotIn('Authorization', request.headers)  # Must not survive a redirect.

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

    def patched_fixture(self):
        manifest = self.fixture()
        manifest['version'] = '0.17.0.3'
        manifest['upstream'] = {'commit': 'a' * 40}
        # Inert test bytes, never an executable patch or a release artifact.
        patch = b'metadata-only patch fixture\n'
        rows = [{'file': 'remote-client-ui.patch', 'sha256': hashlib.sha256(patch).hexdigest()}]
        raw = (json.dumps({'schema': 1, 'patches': rows}, indent=2) + '\n').encode()
        receipt = {'schema': 1, 'verified': True, 'upstreamCommit': 'a' * 40,
                   'upstreamTree': 'b' * 40, 'patchedTree': 'c' * 40,
                   'manifestSha256': hashlib.sha256(raw).hexdigest(), 'patches': rows}
        manifest['sourcePatch'] = receipt
        for label, target in manifest['targets'].items():
            target['archive'] = target['archive'].replace('0.17.0.2', '0.17.0.3')
            target.update(sourceClean=False, sourceVerified=True, sourcePatch=copy.deepcopy(receipt))
            target['nativeSmoke'].update(firstRun=True, remoteForm=True, noAgentCheckout=True,
                                        unreachableRemoteBlocksApply=True, localInstallStarted=False,
                                        remoteSetupDirect=True, localInstallOfferAbsent=True)
            target['targetedSuite'] = {'releaseGatePassed': True}
            if label == 'linux-x64':
                target['fullSuite'] = {'releaseGatePassed': True}
        return manifest, {'source-patches.json': raw, 'remote-client-ui.patch': patch}

    def patched_release(self, manifest, files):
        files = dict(files)
        files['release-manifest.json'] = (json.dumps(manifest) + '\n').encode()
        hashes = {t['archive']: t['sha256'] for t in manifest['targets'].values()}
        hashes.update({name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()
                       if name != 'release-manifest.json'})
        files['SHA256SUMS'] = ''.join(f'{sha}  {name}\n' for name, sha in hashes.items()).encode()
        hashes.update({name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()})
        base = f'https://github.com/{sync.REPO}/releases/download/v{manifest["version"]}'
        release = {'tag_name': 'v' + manifest['version'], 'draft': False,
                   'assets': [{'name': n, 'browser_download_url': f'{base}/{n}', 'digest': 'sha256:' + sha}
                              for n, sha in hashes.items()]}
        return release, {f'{base}/{name}': raw for name, raw in files.items()}

    def run_patched(self, output, manifest, release, downloads):
        with mock.patch.object(sync, 'get_bytes', side_effect=lambda url: downloads[url], create=True):
            self.run_sync(output, manifest, release)

    def assert_patched_rejected(self, manifest, files, mutate_release=None):
        release, downloads = self.patched_release(manifest, files)
        if mutate_release:
            mutate_release(release, downloads)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'hermes-desktop.rb'
            old = sync.render(self.fixture()).encode()
            output.write_bytes(old)
            with self.assertRaises(ValueError):
                self.run_patched(output, manifest, release, downloads)
            self.assertEqual(output.read_bytes(), old)

    def test_verified_patch_renders_only_new_guidance_and_syncs_idempotently(self):
        manifest, files = self.patched_fixture()
        expected = sync.render(self.fixture()).replace('0.17.0.2', '0.17.0.3').replace(
            '    Choose "Connect to existing Hermes", not "Install Hermes locally".',
            '    First start connects to an existing Hermes server; local installation UI is hidden.')
        self.assertEqual(sync.render(manifest), expected)
        release, downloads = self.patched_release(manifest, files)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'hermes-desktop.rb'
            self.run_patched(output, manifest, release, downloads)
            self.assertEqual(output.read_bytes(), expected.encode())
            self.run_patched(output, manifest, release, downloads)

    def test_patch_receipt_fields_are_required_and_strict(self):
        receipt = self.patched_fixture()[0]['sourcePatch']
        cases = [(key, None) for key in receipt]
        cases += [('schema', v) for v in (True, 1.0, '1', 2)]
        cases += [('verified', v) for v in (False, 1, 'true')]
        for key in ('upstreamCommit', 'upstreamTree', 'patchedTree'):
            cases += [(key, v) for v in ('0' * 40, 'A' * 40, 'a' * 39, 'a' * 40 + '\n', True)]
        cases += [('manifestSha256', v) for v in ('A' * 64, 'a' * 63, True)]
        cases += [('patches', v) for v in ([], {}, None)]
        for key, invalid in cases:
            with self.subTest(field=key, value=invalid):
                manifest, files = self.patched_fixture()
                if invalid is None:
                    del manifest['sourcePatch'][key]
                else:
                    manifest['sourcePatch'][key] = invalid
                for target in manifest['targets'].values():
                    target['sourcePatch'] = copy.deepcopy(manifest['sourcePatch'])
                self.assert_patched_rejected(manifest, files)
        for invalid in (None, False, [], 'verified'):
            manifest, files = self.patched_fixture()
            manifest['sourcePatch'] = invalid
            self.assert_patched_rejected(manifest, files)

    def test_patch_identity_and_all_target_receipts_must_agree(self):
        mutations = [lambda m: m.pop('sourcePatch'),
                     lambda m: m['upstream'].update(commit='d' * 40),
                     lambda m: m['sourcePatch'].update(patchedTree='b' * 40)]
        for label in self.fixture()['targets']:
            mutations.extend([lambda m, l=label: m['targets'].pop(l),
                              lambda m, l=label: m['targets'][l].pop('sourcePatch'),
                              lambda m, l=label: m['targets'][l]['sourcePatch'].update(schema=True),
                              lambda m, l=label: m['targets'][l]['sourcePatch']['patches'][0].update(sha256='d' * 64)])
        for mutation in mutations:
            manifest, files = self.patched_fixture()
            mutation(manifest)
            self.assert_patched_rejected(manifest, files)

    def test_patched_gates_require_literal_booleans_on_every_target(self):
        groups = {None: {'sourceClean': False, 'sourceVerified': True, 'archiveRoundtrip': True},
                  'nativeSmoke': {'firstRun': True, 'remoteForm': True, 'noAgentCheckout': True,
                                  'unreachableRemoteBlocksApply': True, 'localInstallStarted': False,
                                  'remoteSetupDirect': True, 'localInstallOfferAbsent': True},
                  'targetedSuite': {'releaseGatePassed': True}, 'fullSuite': {'releaseGatePassed': True}}
        for label in self.fixture()['targets']:
            for group, fields in groups.items():
                if group == 'fullSuite' and label != 'linux-x64':
                    continue
                for field, expected in fields.items():
                    for invalid in (None, not expected, int(expected), str(expected).lower(), [], {}):
                        with self.subTest(target=label, group=group, field=field, invalid=invalid):
                            manifest, files = self.patched_fixture()
                            target = manifest['targets'][label]
                            obj = target if group is None else target[group]
                            if invalid is None:
                                del obj[field]
                            else:
                                obj[field] = invalid
                            self.assert_patched_rejected(manifest, files)

    def test_patched_native_target_and_error_fields_are_exact(self):
        for label in self.fixture()['targets']:
            for field, invalid in [('platform', 'other'), ('arch', 'other'), ('errors', False),
                                   ('errors', {}), ('errors', ['failure'])]:
                manifest, files = self.patched_fixture()
                manifest['targets'][label]['nativeSmoke'][field] = invalid
                self.assert_patched_rejected(manifest, files)
            for group in ('nativeSmoke', 'targetedSuite'):
                manifest, files = self.patched_fixture()
                del manifest['targets'][label][group]
                self.assert_patched_rejected(manifest, files)

    def test_patched_receipts_do_not_relax_signing_or_gatekeeper(self):
        for label in ('darwin-arm64', 'darwin-x64'):
            for group, field, invalid in [(None, 'bundleVerified', False), (None, 'tamperRejected', 1),
                                          (None, 'missingSealRejected', False),
                                          ('gatekeeper', 'enabled', False), ('gatekeeper', 'accepted', True)]:
                manifest, files = self.patched_fixture()
                signing = manifest['targets'][label]['macSigning']
                (signing if group is None else signing[group])[field] = invalid
                self.assert_patched_rejected(manifest, files)

    def test_patch_names_and_digests_are_not_arbitrary_paths(self):
        for name in ('../remote-client-ui.patch', '/tmp/a.patch', 'https://evil/a.patch',
                     'remote-client-ui.patch\n', 'a.patch?raw=1', 'a.patch#x', 'A.patch'):
            manifest, files = self.patched_fixture()
            manifest['sourcePatch']['patches'][0]['file'] = name
            for target in manifest['targets'].values():
                target['sourcePatch'] = copy.deepcopy(manifest['sourcePatch'])
            self.assert_patched_rejected(manifest, files)
        for row in ({'file': 'remote-client-ui.patch', 'sha256': True},
                    {'file': 'remote-client-ui.patch'}, {'file': 'a.patch', 'sha256': 'f' * 64, 'extra': True}):
            manifest, files = self.patched_fixture()
            manifest['sourcePatch']['patches'] = [row]
            self.assert_patched_rejected(manifest, files)
        manifest, files = self.patched_fixture()
        manifest['sourcePatch']['patches'] *= 2
        self.assert_patched_rejected(manifest, files)

    def test_public_patch_bytes_and_original_manifest_bytes_are_verified(self):
        for name in ('source-patches.json', 'remote-client-ui.patch'):
            manifest, files = self.patched_fixture()
            files[name] += b'\n'
            self.assert_patched_rejected(manifest, files)
        # Self-consistent byte hash must not excuse a different public patch list.
        manifest, files = self.patched_fixture()
        files['source-patches.json'] = json.dumps({'schema': 1, 'patches': []}).encode()
        manifest['sourcePatch']['manifestSha256'] = hashlib.sha256(files['source-patches.json']).hexdigest()
        for target in manifest['targets'].values():
            target['sourcePatch'] = copy.deepcopy(manifest['sourcePatch'])
        self.assert_patched_rejected(manifest, files)

    def test_patched_public_assets_require_exact_urls_names_and_digests(self):
        manifest, files = self.patched_fixture()
        release, _ = self.patched_release(manifest, files)
        for name in [a['name'] for a in release['assets']]:
            for field, value in [('name', 'wrong-' + name), ('digest', None), ('digest', 'sha256:' + 'f' * 64),
                                 ('browser_download_url', f'https://github.com/evil/repo/releases/download/v0.17.0.3/{name}'),
                                 ('browser_download_url', f'https://github.com/{sync.REPO}/releases/download/v0.17.0.2/{name}')]:
                with self.subTest(asset=name, field=field, value=value):
                    def mutate(r, d, name=name, field=field, value=value):
                        a = next(a for a in r['assets'] if a['name'] == name)
                        if value is None:
                            del a[field]
                        else:
                            a[field] = value
                    self.assert_patched_rejected(manifest, files, mutate)
            self.assert_patched_rejected(manifest, files,
                lambda r, d, n=name: r['assets'].append(copy.deepcopy(next(a for a in r['assets'] if a['name'] == n))))

    def test_sha256sums_must_include_exact_patch_hashes(self):
        manifest, files = self.patched_fixture()
        for name in files:
            def mutate(release, downloads, name=name):
                url = next(u for u in downloads if u.endswith('/SHA256SUMS'))
                raw = b''.join(line for line in downloads[url].splitlines(keepends=True)
                               if not line.endswith(('  ' + name + '\n').encode()))
                downloads[url] = raw
                next(a for a in release['assets'] if a['name'] == 'SHA256SUMS')['digest'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
            self.assert_patched_rejected(manifest, files, mutate)

    def test_legacy_assets_keep_optional_digest_but_reject_wrong_metadata(self):
        manifest = self.fixture()
        for field, invalid in [('digest', 'sha256:' + 'f' * 64),
                               ('browser_download_url', 'https://evil.example/Hermes.zip')]:
            release = self.release(manifest)
            release['assets'][1][field] = invalid
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'hermes-desktop.rb'
                with self.assertRaises(ValueError):
                    self.run_sync(output, manifest, release)
                self.assertFalse(output.exists())

    def test_exact_requested_tag_and_manifest_asset_name_are_required(self):
        manifest = self.fixture()
        for mutate in (lambda r: r.update(tag_name='x0.17.0.2'),
                       lambda r: r.update(tag_name='v0.17.0.3'),
                       lambda r: r['assets'][0].update(name='other.json')):
            release = self.release(manifest)
            mutate(release)
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    self.run_sync(Path(directory) / 'hermes-desktop.rb', manifest, release)

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

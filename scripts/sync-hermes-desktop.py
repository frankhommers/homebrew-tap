#!/usr/bin/env python3
"""Generate only the Hermes cask from a verified immutable community release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
import urllib.parse

REPO='frankhommers/hermes-desktop-builds'
ROOT=Path(__file__).resolve().parents[1]


def get_json(url):
    request=urllib.request.Request(url,headers={'User-Agent':'frankhommers-homebrew-tap','Accept':'application/json'})
    parsed=urllib.parse.urlsplit(url)
    token=os.environ.get('GH_TOKEN')
    if token and parsed.scheme=='https' and parsed.netloc=='api.github.com':
        # Hosted runners share unauthenticated API quotas. Keep the read-only
        # Actions token off release/CDN requests and off every redirected request.
        request.add_unredirected_header('Authorization','Bearer '+token)
    with urllib.request.urlopen(request,timeout=60) as response:
        return json.load(response)


def version_tuple(version):
    if not isinstance(version,str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+',version):raise ValueError('Invalid distribution version')
    return tuple(map(int,version.split('.')))


def require_fields(obj,expected,label):
    """Require JSON types as well as values (True == 1 in Python)."""
    if not isinstance(obj,dict):
        raise ValueError(f'{label}: expected an object')
    for key,value in expected.items():
        actual=obj.get(key)
        if type(actual) is not type(value) or actual!=value:
            raise ValueError(f'{label}: invalid or missing {key}')


def validate_mac_signing(signing):
    require_fields(signing,{
        'schema':1,'mode':'ad-hoc','developerID':False,'notarized':False,
        'bundleVerified':True,'archiveVerified':True,
        'tamperRejected':True,'missingSealRejected':True,
    },'Mac signing')
    for key in ('stagedNativeCount','nativePayloadsVerified'):
        value=signing.get(key)
        if type(value) is not int or value<=0:
            raise ValueError(f'Mac signing: {key} must be a positive integer')
    if signing['nativePayloadsVerified']!=signing['stagedNativeCount']:
        raise ValueError('Mac signing: not all staged native payloads were verified')
    require_fields(signing.get('gatekeeper'),{
        'enabled':True,'quarantinePresent':True,'accepted':False,
        'exitCode':3,'assessment':'unnotarized-ad-hoc',
    },'Mac signing Gatekeeper')


def hex_digest(value, length):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def validate_patch_rows(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Missing source patches')
    names = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'file', 'sha256'}:
            raise ValueError('Malformed source patch entry')
        name = row['file']
        if (not isinstance(name, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.patch', name)
                or name in names or not hex_digest(row['sha256'], 64)):
            raise ValueError('Unsafe, duplicate or unhashed source patch')
        names.add(name)


def validate_patch_receipt(receipt, upstream):
    require_fields(receipt, {'schema': 1, 'verified': True}, 'Source patch receipt')
    if set(receipt) != {'schema', 'verified', 'upstreamCommit', 'upstreamTree',
                       'patchedTree', 'manifestSha256', 'patches'}:
        raise ValueError('Malformed source patch receipt')
    for key in ('upstreamCommit', 'upstreamTree', 'patchedTree'):
        if not hex_digest(receipt[key], 40) or receipt[key] == '0' * 40:
            raise ValueError('Invalid source patch identity: ' + key)
    require_fields(upstream, {'commit': receipt['upstreamCommit']}, 'Source patch upstream')
    if receipt['upstreamTree'] == receipt['patchedTree']:
        raise ValueError('Source patch must change the tree')
    if not hex_digest(receipt['manifestSha256'], 64):
        raise ValueError('Invalid source patch manifest SHA256')
    validate_patch_rows(receipt['patches'])


def validate_sources(manifest):
    targets = manifest.get('targets')
    if not isinstance(targets, dict) or set(targets) != {'darwin-arm64', 'darwin-x64', 'win32-x64', 'linux-x64'}:
        raise ValueError('Incomplete crossplatform release')
    patched = 'sourcePatch' in manifest
    if patched:
        validate_patch_receipt(manifest['sourcePatch'], manifest.get('upstream'))
    for label, target in targets.items():
        require_fields(target, {'sourceClean': not patched, 'archiveRoundtrip': True}, 'Incomplete validation')
        platform, arch = label.split('-')
        require_fields(target.get('nativeSmoke'), {'platform': platform, 'arch': arch, 'errors': []}, 'Bad native smoke')
        if not patched:
            if 'sourcePatch' in target:
                raise ValueError('Target source patch without release receipt')
            continue  # Legacy receipts predate UI and suite gates; keep their rendering immutable.
        require_fields(target, {'sourceVerified': True}, 'Source verification')
        validate_patch_receipt(target.get('sourcePatch'), manifest.get('upstream'))
        if target['sourcePatch'] != manifest['sourcePatch']:
            raise ValueError('Targets did not build the same patched source')
        require_fields(target.get('nativeSmoke'), {
            'remoteSetupDirect': True, 'localInstallOfferAbsent': True,
            'firstRun': True, 'remoteForm': True, 'noAgentCheckout': True,
            'unreachableRemoteBlocksApply': True, 'localInstallStarted': False,
        }, 'Patched UI smoke')
        require_fields(target.get('targetedSuite'), {'releaseGatePassed': True}, 'Targeted suite')
        if platform == 'linux':
            require_fields(target.get('fullSuite'), {'releaseGatePassed': True}, 'Full suite')
        suffix = 'adhoc' if platform == 'darwin' else 'unsigned'
        extension = 'tar.gz' if platform == 'linux' else 'zip'
        if (target.get('archive') != f'Hermes-{manifest["version"]}-{label}-{suffix}.{extension}'
                or not hex_digest(target.get('sha256'), 64)):
            raise ValueError('Bad patched artifact')
    return patched


def get_bytes(url):
    # Read evidence only. Never write, apply or execute downloaded patch code.
    request = urllib.request.Request(url, headers={'User-Agent': 'frankhommers-homebrew-tap'})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Oversized release metadata or source patch')
    return raw


def release_asset(release, version, name, expected=None, required_digest=False):
    assets = release.get('assets')
    if not isinstance(assets, list):
        raise ValueError('Missing release assets')
    matches = [a for a in assets if isinstance(a, dict) and a.get('name') == name]
    if len(matches) != 1:
        label = 'Missing Mac ZIP asset' if name.endswith('-adhoc.zip') else 'Missing or duplicate release asset'
        raise ValueError(label + ': ' + name)
    asset = matches[0]
    require_fields(asset, {'browser_download_url': f'https://github.com/{REPO}/releases/download/v{version}/{name}'}, 'Release asset URL')
    if required_digest or 'digest' in asset:
        digest = asset.get('digest')
        if not isinstance(digest, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            raise ValueError('Missing or invalid asset digest: ' + name)
        if expected is not None and digest != 'sha256:' + expected:
            raise ValueError('Asset digest mismatch: ' + name)
    return asset


def read_verified_asset(release, version, name, expected=None):
    asset = release_asset(release, version, name, expected, required_digest=True)
    raw = get_bytes(asset['browser_download_url'])
    actual = hashlib.sha256(raw).hexdigest()
    if asset['digest'] != 'sha256:' + actual or (expected is not None and actual != expected):
        raise ValueError('Downloaded asset SHA256 mismatch: ' + name)
    return raw


def validate_public_patches(release, manifest):
    version = manifest['version']
    receipt = manifest['sourcePatch']
    raw = read_verified_asset(release, version, 'source-patches.json', receipt['manifestSha256'])
    published = json.loads(raw)
    require_fields(published, {'schema': 1}, 'Published patch manifest')
    if set(published) != {'schema', 'patches'}:
        raise ValueError('Malformed published patch manifest')
    validate_patch_rows(published.get('patches'))
    if published['patches'] != receipt['patches']:
        raise ValueError('Published source patch set differs from receipt')
    expected = {'source-patches.json': receipt['manifestSha256']}
    for row in receipt['patches']:
        read_verified_asset(release, version, row['file'], row['sha256'])
        expected[row['file']] = row['sha256']
    for target in manifest['targets'].values():
        release_asset(release, version, target['archive'], target['sha256'], required_digest=True)
        expected[target['archive']] = target['sha256']
    sums = read_verified_asset(release, version, 'SHA256SUMS').decode('utf-8')
    checks = {}
    for line in sums.splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]*)', line)
        if not match or match[2] in checks:
            raise ValueError('Malformed or duplicate SHA256SUMS entry')
        checks[match[2]] = match[1]
    if any(checks.get(name) != digest for name, digest in expected.items()):
        raise ValueError('SHA256SUMS does not match source patches and archives')


def render(manifest):
    version=manifest['version'];version_tuple(version)
    require_fields(manifest,{'schema':1,'buildRepository':REPO},'Wrong release provenance')
    if not isinstance(manifest.get('buildRun'),str) or not re.fullmatch(r'https://github.com/frankhommers/hermes-desktop-builds/actions/runs/[0-9]+',manifest['buildRun']):raise ValueError('Missing build run')
    patched=validate_sources(manifest)
    targets=manifest['targets']
    guidance=('First start connects to an existing Hermes server; local installation UI is hidden.' if patched
              else 'Choose "Connect to existing Hermes", not "Install Hermes locally".')
    blocks=[]
    for arch,condition in [('arm64','on_arm'),('x64','on_intel')]:
        m=targets['darwin-'+arch]
        expected=f'Hermes-{version}-darwin-{arch}-adhoc.zip'
        if m.get('archive')!=expected or not hex_digest(m.get('sha256'),64):raise ValueError('Bad Mac artifact')
        require_fields(m.get('nativeSmoke'),{'platform':'darwin','arch':arch,'errors':[]},'Bad Mac smoke')
        validate_mac_signing(m.get('macSigning'))
        blocks.append(f'''  {condition} do
    sha256 "{m['sha256']}"

    url "https://github.com/{REPO}/releases/download/v#{{version}}/Hermes-#{{version}}-darwin-{arch}-adhoc.zip"
  end''')
    return f'''# frozen_string_literal: true

cask "hermes-desktop" do
  version "{version}"

{chr(10).join(blocks)}

  name "Hermes Desktop"
  desc "Standalone Hermes Electron Desktop for remote backends"
  homepage "https://github.com/{REPO}"

  depends_on macos: :monterey

  app "Hermes.app"

  caveats <<~EOS
    Ad-hoc signed community build; no Developer ID or Apple notarization.
    Gatekeeper remains enabled; app-specific approval may be required.
    {guidance}
    An existing local Hermes runtime may be discovered and started by upstream.
    Review existing installations before launching if local startup must be avoided.
    No Python agent is installed by this cask. Updates use brew upgrade, not the in-app updater.
  EOS
end
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',help='Exact published distribution version; default highest valid release')
    parser.add_argument('--output',type=Path,default=ROOT/'casks/hermes-desktop.rb')
    args=parser.parse_args()
    if args.version:
        version_tuple(args.version)
        release=get_json(f'https://api.github.com/repos/{REPO}/releases/tags/v{args.version}')
    else:
        releases=get_json(f'https://api.github.com/repos/{REPO}/releases?per_page=100')
        candidates=[r for r in releases if not r['draft'] and re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+',r['tag_name'])]
        if not candidates:raise ValueError('No verified Hermes Desktop releases yet')
        release=max(candidates,key=lambda r:version_tuple(r['tag_name'][1:]))
    tag=release.get('tag_name')
    if not isinstance(tag,str) or not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+',tag):raise ValueError('Invalid release tag')
    version=tag[1:];version_tuple(version)
    if args.version and version!=args.version:raise ValueError('Requested version/tag mismatch')
    require_fields(release,{'draft':False},'Draft release is not installable')
    url=f'https://github.com/{REPO}/releases/download/v{version}/release-manifest.json'
    manifest_asset=release_asset(release,version,'release-manifest.json')
    manifest=get_json(url)
    if manifest['version']!=version:raise ValueError('Manifest/tag mismatch')
    text=render(manifest)
    patched='sourcePatch' in manifest
    if patched or 'digest' in manifest_asset:
        raw=read_verified_asset(release,version,'release-manifest.json')
        if json.dumps(json.loads(raw),sort_keys=True)!=json.dumps(manifest,sort_keys=True):raise ValueError('Release manifest changed during sync')
    for arch in ('arm64','x64'):
        name=f'Hermes-{version}-darwin-{arch}-adhoc.zip'
        release_asset(release,version,name,manifest['targets']['darwin-'+arch]['sha256'],required_digest=patched)
    if patched:validate_public_patches(release,manifest)
    if args.output.exists():
        old=args.output.read_text()
        current=re.search(r'^  version "([0-9.]+)"$',old,re.M)
        if current and version_tuple(version)<version_tuple(current[1]):raise ValueError('Refusing downgrade')
        if current and version==current[1] and text!=old:raise ValueError('Immutable release changed without a version bump')
        if text==old:print('Cask already current:',version);return
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(text)
    print('Generated cask:',version,'from',manifest['buildRun'])

if __name__=='__main__':main()

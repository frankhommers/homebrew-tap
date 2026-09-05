#!/usr/bin/env python3
"""Generate only the Hermes cask from a verified immutable community release."""
import argparse
import json
from pathlib import Path
import re
import urllib.request

REPO='frankhommers/hermes-desktop-builds'
ROOT=Path(__file__).resolve().parents[1]


def get_json(url):
    request=urllib.request.Request(url,headers={'User-Agent':'frankhommers-homebrew-tap','Accept':'application/json'})
    with urllib.request.urlopen(request,timeout=60) as response:
        return json.load(response)


def version_tuple(version):
    if not re.fullmatch(r'\d+\.\d+\.\d+\.\d+',version):raise ValueError('Invalid distribution version')
    return tuple(map(int,version.split('.')))


def render(manifest):
    version=manifest['version'];version_tuple(version)
    if manifest.get('schema')!=1 or manifest.get('buildRepository')!=REPO:raise ValueError('Wrong release provenance')
    if not re.fullmatch(r'https://github.com/frankhommers/hermes-desktop-builds/actions/runs/\d+',manifest['buildRun']):raise ValueError('Missing build run')
    targets=manifest['targets']
    if set(targets)!={'darwin-arm64','darwin-x64','win32-x64','linux-x64'}:raise ValueError('Incomplete crossplatform release')
    blocks=[]
    for arch,condition in [('arm64','on_arm'),('x64','on_intel')]:
        m=targets['darwin-'+arch]
        expected=f'Hermes-{version}-darwin-{arch}-unsigned.zip'
        if m['archive']!=expected or not re.fullmatch('[0-9a-f]{64}',m['sha256']):raise ValueError('Bad Mac artifact')
        if m['nativeSmoke']['platform']!='darwin' or m['nativeSmoke']['arch']!=arch or m['nativeSmoke']['errors']:raise ValueError('Bad Mac smoke')
        if not m['sourceClean'] or not m['archiveRoundtrip']:raise ValueError('Incomplete validation')
        blocks.append(f'''  {condition} do
    sha256 "{m['sha256']}"

    url "https://github.com/{REPO}/releases/download/v#{{version}}/Hermes-#{{version}}-darwin-{arch}-unsigned.zip"
  end''')
    return f'''# frozen_string_literal: true

cask "hermes-desktop" do
  version "{version}"

{chr(10).join(blocks)}

  name "Hermes Desktop"
  desc "Standalone Hermes Electron Desktop for remote backends"
  homepage "https://github.com/{REPO}"

  depends_on macos: ">= :monterey"

  app "Hermes.app"

  caveats <<~EOS
    Unsigned community build; not Apple-notarized. Gatekeeper remains enabled.
    Choose "Connect to existing Hermes", not "Install Hermes locally".
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
        candidates=[r for r in releases if not r['draft'] and re.fullmatch(r'v\d+\.\d+\.\d+\.\d+',r['tag_name'])]
        if not candidates:raise ValueError('No verified Hermes Desktop releases yet')
        release=max(candidates,key=lambda r:version_tuple(r['tag_name'][1:]))
    version=release['tag_name'][1:];version_tuple(version)
    if release['draft']:raise ValueError('Draft release is not installable')
    url=f'https://github.com/{REPO}/releases/download/v{version}/release-manifest.json'
    if not any(a['browser_download_url']==url for a in release['assets']):raise ValueError('No release manifest asset')
    manifest=get_json(url)
    if manifest['version']!=version:raise ValueError('Manifest/tag mismatch')
    for arch in ('arm64','x64'):
        name=f'Hermes-{version}-darwin-{arch}-unsigned.zip'
        if not any(a['name']==name for a in release['assets']):raise ValueError('Missing Mac ZIP asset')
    text=render(manifest)
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

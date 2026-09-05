# Homebrew Tap

Homebrew casks and formulae for Frank Hommers' macOS tools.

## Usage

```bash
brew tap frankhommers/tap
```

## Available Casks

| Cask | Description | Install |
|------|-------------|---------|
| hermes-desktop | Standalone Hermes Electron Desktop, unsigned community preview | `brew install --cask frankhommers/tap/hermes-desktop` |
| mcp-manager | MCP server management with multi-target export | `brew install --cask frankhommers/tap/mcp-manager` |
| git-auto-sync | Git repository auto-sync with GUI and daemon | `brew install --cask frankhommers/tap/git-auto-sync` |
| rclone-mount-manager | Rclone mount manager with GUI | `brew install --cask frankhommers/tap/rclone-mount-manager` |

### Hermes Desktop

```bash
brew install --cask frankhommers/tap/hermes-desktop
# Later:
brew update
brew upgrade --cask frankhommers/tap/hermes-desktop
```

This is the standalone Electron desktop from
[hermes-desktop-builds](https://github.com/frankhommers/hermes-desktop-builds),
not the agent bootstrap installer. The cask selects Apple Silicon or Intel automatically.
It does not install Python/an agent, remove quarantine or disable Gatekeeper.
The current community preview is unsigned and not Apple-notarized.

On a clean first run choose **Connect to existing Hermes**. An already installed
local runtime can be discovered by the unchanged upstream app; review that before
launching if local startup must be avoided. The in-app updater is not used here.

The daily/manual **Sync Hermes Desktop cask** workflow consumes only a published
crossplatform release manifest, validates/downloads/installs on both Mac architectures,
and commits the cask only after those checks pass. No cross-repository PAT is needed.
The installer checks do not prove Gatekeeper acceptance or remote-backend login on your Mac.

### Cask maintenance

The **Validate tap casks** pull-request workflow checks the current Homebrew DSL,
style and audit for every cask on Apple Silicon and Intel Macs. It also downloads,
checks SHA256 and installs `git-auto-sync`, `mcp-manager` and
`rclone-mount-manager` into a temporary app directory, verifying their native
executables and structured `postflight_steps`. It does not launch those apps.
Hermes retains its separate signature/Gatekeeper installation gate.

The three older apps retain their existing, app-root-only quarantine removal;
this DSL migration does not add signing or notarization. Hermes does **not** use
that hook. Published application versions, URLs and checksums are unchanged.
The release-triggered cask updater changes only versions/checksums and runs DSL
regression tests before publishing, so future updates preserve the modern syntax.

## Available Formulae

| Formula | Description | Install |
|---------|-------------|---------|
| tmux | tmux with an embedded `Info.plist` so macOS grants it Local Network access | `brew install frankhommers/tap/tmux` |

### tmux

On macOS 15 and later, Local Network Privacy blocks connections to LAN addresses
from processes whose parent chain has no recognisable app identity. tmux
daemonises itself and is ad-hoc signed without a bundle identifier, so anything
you run *inside* tmux — node, python, go — silently fails with `EHOSTUNREACH`
on local addresses, while Apple-signed binaries such as `curl` work fine. The
error suggests a routing problem, which makes it painful to diagnose.

This formula links an `Info.plist` containing `CFBundleIdentifier` and
`NSLocalNetworkUsageDescription` into the binary's `__TEXT,__info_plist`
section, then ad-hoc signs it. tmux then has a stable identity and shows up
under **System Settings → Privacy & Security → Local Network**.

Replacing the Homebrew version:

```bash
brew uninstall --ignore-dependencies tmux
brew install frankhommers/tap/tmux
```

A running tmux server keeps the old binary in memory. To test without losing
your sessions, start a server on a separate socket:

```bash
tmux -L test new-session
```

Existing sessions only pick up the new binary after `tmux kill-server`.

Credit for the approach: [Fixing tmux Local Network Access on macOS](https://colosieve.com/posts/fixing-tmux-local-network-privacy-macos/).

#### Staying in sync

`Formula/tmux.rb` is **generated, not maintained by hand**.
`scripts/generate-tmux-formula.py` fetches the current formula from
homebrew-core and injects the patch, so upstream changes — new versions,
dependencies, configure flags — are picked up automatically. The core `bottle`
block is stripped, since those bottles contain the unpatched binary.

A weekly GitHub Action regenerates the formula, builds it, verifies the
`Info.plist` is present in the resulting binary, and only then commits. If
homebrew-core changes enough that the patch no longer applies, the workflow
fails loudly instead of silently shipping an unpatched build.

Run it locally with:

```bash
python3 scripts/generate-tmux-formula.py
```

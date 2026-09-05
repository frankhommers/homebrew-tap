# frozen_string_literal: true

cask "hermes-desktop" do
  version "0.17.0.3"

  on_arm do
    sha256 "e2bbc944eb6cff431a528d4f0b6e2735d9445f25725ced59b03fd3a726be81aa"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-arm64-adhoc.zip"
  end
  on_intel do
    sha256 "6459527f09c36be01322443e2d4fcc2e82801ff7de1c0a7d7343a4400d0d842d"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-x64-adhoc.zip"
  end

  name "Hermes Desktop"
  desc "Standalone Hermes Electron Desktop for remote backends"
  homepage "https://github.com/frankhommers/hermes-desktop-builds"

  depends_on macos: :monterey

  app "Hermes.app"

  caveats <<~EOS
    Ad-hoc signed community build; no Developer ID or Apple notarization.
    Gatekeeper remains enabled; app-specific approval may be required.
    First start connects to an existing Hermes server; local installation UI is hidden.
    An existing local Hermes runtime may be discovered and started by upstream.
    Review existing installations before launching if local startup must be avoided.
    No Python agent is installed by this cask. Updates use brew upgrade, not the in-app updater.
  EOS
end

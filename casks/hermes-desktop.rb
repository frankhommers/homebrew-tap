# frozen_string_literal: true

cask "hermes-desktop" do
  version "0.17.6.2"

  on_arm do
    sha256 "9b85b3d7b4b26e3f05eb1381b89235f10142ccc51921ba4aa02e44bd68f74d44"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-arm64-adhoc.zip"
  end
  on_intel do
    sha256 "108c0bd6671937b2eecf45529e93f4d9716a52f9b4653608db858984efcf0bb0"

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
    No Python agent is installed by this cask.
    The first upgrade from before 0.17.2.1 must run with:
      brew upgrade --cask frankhommers/tap/hermes-desktop
    This build can apply later Desktop updates in-app through Homebrew.
    Remote backends are never updated by the Desktop updater.
  EOS
end

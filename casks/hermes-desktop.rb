# frozen_string_literal: true

cask "hermes-desktop" do
  version "0.17.2.1"

  on_arm do
    sha256 "f67238a6664afc06579868aec79e01b1a85ff3d17a79b3523d776f9b06b1c062"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-arm64-adhoc.zip"
  end
  on_intel do
    sha256 "8bd576d88077a58a3b372948b365f6a2f5b36f7b2ab0addd7aa8b189286eb78a"

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

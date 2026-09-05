# frozen_string_literal: true

cask "hermes-desktop" do
  version "0.17.0.1"

  on_arm do
    sha256 "2205043b0136aad5040ed2a62358c6b02af97206bb41748dd4802fd4c274a0ec"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-arm64-unsigned.zip"
  end
  on_intel do
    sha256 "de6b339c64c7cac81059df03b65f5abdcc90f27c26bc03680571e614fcedc07a"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-x64-unsigned.zip"
  end

  name "Hermes Desktop"
  desc "Standalone Hermes Electron Desktop for remote backends"
  homepage "https://github.com/frankhommers/hermes-desktop-builds"

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

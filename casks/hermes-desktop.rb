# frozen_string_literal: true

cask "hermes-desktop" do
  version "0.17.0.2"

  on_arm do
    sha256 "fed28fc30910373c05fc87df6b4657c405837377e2411c2c68d071a297046db4"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-arm64-adhoc.zip"
  end
  on_intel do
    sha256 "cee670ec2ca2262bd7b89d5be119fa450b39c1801a61e2281cfcbee256c59988"

    url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/v#{version}/Hermes-#{version}-darwin-x64-adhoc.zip"
  end

  name "Hermes Desktop"
  desc "Standalone Hermes Electron Desktop for remote backends"
  homepage "https://github.com/frankhommers/hermes-desktop-builds"

  depends_on macos: ">= :monterey"

  app "Hermes.app"

  caveats <<~EOS
    Ad-hoc signed community build; no Developer ID or Apple notarization.
    Gatekeeper remains enabled; app-specific approval may be required.
    Choose "Connect to existing Hermes", not "Install Hermes locally".
    An existing local Hermes runtime may be discovered and started by upstream.
    Review existing installations before launching if local startup must be avoided.
    No Python agent is installed by this cask. Updates use brew upgrade, not the in-app updater.
  EOS
end

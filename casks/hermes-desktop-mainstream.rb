# frozen_string_literal: true

cask "hermes-desktop-mainstream" do
  version "1.0.1"
  sha256 "b46910ec0653759713471d1f3ba3342d092037618db504da5461b66e449f5b2b"

  url "https://github.com/frankhommers/hermes-desktop-builds/releases/download/mainstream-v#{version}/Hermes-mainstream-#{version}.zip"
  name "Hermes Desktop Mainstream"
  desc "One-time migration to the official in-app Desktop updater"
  homepage "https://github.com/frankhommers/hermes-desktop-builds"

  livecheck do
    skip "One-time installer; the installed client uses the official Hermes updater"
  end

  auto_updates true
  depends_on arch: :arm64
  depends_on formula: ["node", "python@3.12"]
  depends_on macos: :sequoia

  installer script: {
    executable:   "#{HOMEBREW_PREFIX}/opt/python@3.12/bin/python3.12",
    args:         ["#{staged_path}/Hermes-mainstream/brew_install.py",
                   "--brew", "#{HOMEBREW_PREFIX}/bin/brew", "--app", "#{appdir}/Hermes.app"],
    must_succeed: true,
    sudo:         false,
  }

  # The bootstrap receipt does not own/delete the app, source or user data.
  uninstall script: { executable: "/usr/bin/true" }

  caveats <<~EOS
    Migrates an existing, closed Hermes.app with a saved remote-primary connection.
    Builds unmodified official source locally; installs Python/Node prerequisites.
    No local agent autostart, service registration or automatic app launch.
    Existing sources/services or unsafe saved routing cause a refusal, not deletion.
    The old app and private user-data backups are retained.
    An installed frankhommers/tap/hermes-desktop cask is pinned, not uninstalled.
    Keep it pinned: future app updates belong to the official in-app updater.
    Its uninstall still removes Hermes.app; this bootstrap's uninstall removes only its receipt.
    Ad-hoc signing is not Apple notarization; app-specific Gatekeeper approval may be needed.
    Keep Python/Node and ~/.hermes/hermes-agent for the official updater.
  EOS
end

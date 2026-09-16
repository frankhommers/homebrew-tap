# frozen_string_literal: true

cask "rclone-mount-manager" do
  version "1.0.7"

  on_arm do
    sha256 "f6552e4a8dd6a1d2f73b012b20b1c46cc5e16f2f1b3b28f8b1bc4a6225cbf336"

    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "f256cd62bed47166f438b578e27afe32044e6ee562e3e31f6e04355f538ef8ac"

    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-x64.dmg"
  end

  name "Rclone Mount Manager"
  desc "GUI for managing rclone mounts"
  homepage "https://github.com/frankhommers/rclone-mount-manager"

  app "Rclone Mount Manager.app"

  postflight_steps do
    run "/usr/bin/xattr",
        args:         ["-d", "com.apple.quarantine", "{{appdir}}/Rclone Mount Manager.app"],
        sudo:         false,
        must_succeed: true
  end

  zap trash: "~/.config/rclone-mount-manager"
end

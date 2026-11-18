# frozen_string_literal: true

cask "rclone-mount-manager" do
  version "1.1.0"

  on_arm do
    sha256 "9fde15d254cdf02400b2b0f24cfa2b3c209746a9b66e28ebcb37184db5a79698"

    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "322497ef1e9e359ad90520b18b1b09e782a9f24822c8ac3f4a9eb454801b0e95"

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

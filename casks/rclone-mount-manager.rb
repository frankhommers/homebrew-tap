# frozen_string_literal: true

cask "rclone-mount-manager" do
  version "1.0.8"

  on_arm do
    sha256 "683ff6c207ee292de65223e8e89626ac64739e881123a5bd073afd908acba957"

    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "331346cab7fde3bf0e4c7360243a891e5fe2b80b53e28ef29376b4eae43ec3bd"

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

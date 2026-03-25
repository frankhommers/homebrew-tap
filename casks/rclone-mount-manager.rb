cask "rclone-mount-manager" do
  version "1.0.6"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "46652df3b9a1b36c216a4b89d1cdd2fda2f5dcee00923b3155e1bcd82630f3fd"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "73ed350f94fb82ba35780506ea94e166a37a6c1cf9f898378b41ba5ad0afc396"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-x64.dmg"
  end

  name "Rclone Mount Manager"
  desc "Rclone mount manager with GUI"
  homepage "https://github.com/frankhommers/rclone-mount-manager"

  app "Rclone Mount Manager.app"

  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-d", "com.apple.quarantine", "#{appdir}/Rclone Mount Manager.app"],
                   sudo: false
  end

  zap trash: [
    "~/.config/rclone-mount-manager",
  ]
end

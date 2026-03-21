cask "rclone-mount-manager" do
  version "1.0.2"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "715baff0a945f217baf03cebed9212f5df20d03c9395625472dcf5d1f81e28a3"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "4d2299f1962e2a0562818552b60a0909555dc51d809aefb9be170f76c0cedfc7"
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

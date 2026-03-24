cask "rclone-mount-manager" do
  version "1.0.5"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "be26b98399ac6ba9141a41f76df287ad0ac1f7f5c5c31b4d4c4285ebbeb0753a"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "c2950ef130da4b26c21f00f59590ad586c5bbcf1236a21f079cb5a53c3164d71"
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

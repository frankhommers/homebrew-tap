cask "rclone-mount-manager" do
  version "1.0.1"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "74f783b4146998a4c88c51b71cac1d57885c739946ccf2d5ecbeb97574e70a81"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "33cb81ed072f1a1559f42aa37f25c054a896c757289193886403d1628637646b"
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

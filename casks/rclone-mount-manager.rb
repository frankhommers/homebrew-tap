cask "rclone-mount-manager" do
  version "1.0.0"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "35ec63cf794177cc959f2f9aaf3a81c5396ca8f697d41559fcede3df820dd07b"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "8ad7b5abfd5061bf86b00fbd942a1dc9d24f41c9044c7b6f6c7961cc835ecd95"
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

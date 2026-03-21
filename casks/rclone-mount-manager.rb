cask "rclone-mount-manager" do
  version "1.0.3"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "847d8582a4428de0193aa2fdf4a8020edc8f38d50759414fdeaca4733c5b10f8"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "54cf6c80cf07ccce9de59d68f7121bb31356391759dfcc43cacf44693f4c0ebb"
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

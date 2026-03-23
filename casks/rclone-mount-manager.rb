cask "rclone-mount-manager" do
  version "1.0.4"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "04a466223e1fc8ef72c04b2c0d6aa9d086255d7d7d0043ce02b499c27f58ef5a"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "9c1338712575f7de197da16c6fe2de7f57a524de9f6bb9449e8546c13e2036ae"
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

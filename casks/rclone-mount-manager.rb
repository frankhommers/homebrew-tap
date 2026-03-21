cask "rclone-mount-manager" do
  version "1.0.1"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "d60ed854c1f3a892c78818db4302640bd6029026225c3bb3ddcaee56a7c10ee0"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "08161ffd93c29112d6d2301d9271f5b947e4b08a095cfa904a338320c7428302"
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

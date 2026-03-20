cask "rclone-mount" do
  version "0.1.0"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 :no_check
    url "https://github.com/frankhommers/rclone-mount/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 :no_check
    url "https://github.com/frankhommers/rclone-mount/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-x64.dmg"
  end

  name "Rclone Mount Manager"
  desc "Rclone mount manager with GUI"
  homepage "https://github.com/frankhommers/rclone-mount"

  app "Rclone Mount Manager.app"

  zap trash: [
    "~/.config/rclone-mount-manager",
  ]
end

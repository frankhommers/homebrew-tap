cask "rclone-mount-manager" do
  version "1.0.0"

  # TODO: Update SHA256 hashes when first release is published
  on_arm do
    sha256 "365fcf60b6cf9bfc241d7a0e71de5878a63431fc59ef838d264e545c4078523c"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "5a6a8c64cd8723d9271caf0fd3fe3ed7705d5ccbe814faba7c1823f72f7ba8ce"
    url "https://github.com/frankhommers/rclone-mount-manager/releases/download/v#{version}/RcloneMountManager-v#{version}-osx-x64.dmg"
  end

  name "Rclone Mount Manager"
  desc "Rclone mount manager with GUI"
  homepage "https://github.com/frankhommers/rclone-mount-manager"

  app "Rclone Mount Manager.app"

  zap trash: [
    "~/.config/rclone-mount-manager",
  ]
end

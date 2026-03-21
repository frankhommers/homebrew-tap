cask "git-auto-sync" do
  version "1.0.0"

  on_arm do
    sha256 "74710af7841db9b9f08bd808dcf9022875f4229bb44cdc2d2479d2c285f5e6ab"
    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "0ad689f681539355d191100287262ba35bbb0c74b43539c8c09f00cc4bc0b74a"
    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-x64.dmg"
  end

  name "Git Auto Sync"
  desc "Cross-platform Git repository auto-sync with GUI and daemon"
  homepage "https://github.com/frankhommers/git-auto-sync"

  app "Git Auto Sync.app"

  zap trash: [
    "~/.config/git-auto-sync",
    "~/Library/LaunchAgents/com.gitautosync.daemon.plist",
  ]
end

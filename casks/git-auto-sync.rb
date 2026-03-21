cask "git-auto-sync" do
  version "1.0.1"

  on_arm do
    sha256 "bef9de8e7ba6727724445af31005b10f3f0b4e6d08a2b9172af9ea8da3d1150b"
    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "77673661fe84bc6de5c68821b2953c266a083fc92e4d99429e3bd05ee91cf0b0"
    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-x64.dmg"
  end

  name "Git Auto Sync"
  desc "Cross-platform Git repository auto-sync with GUI and daemon"
  homepage "https://github.com/frankhommers/git-auto-sync"

  app "Git Auto Sync.app"

  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-d", "com.apple.quarantine", "#{appdir}/Git Auto Sync.app"],
                   sudo: false
  end

  zap trash: [
    "~/.config/git-auto-sync",
    "~/Library/LaunchAgents/com.gitautosync.daemon.plist",
  ]
end

cask "git-auto-sync" do
  version "1.0.5"

  on_arm do
    sha256 "7f252ff8065737b900092e09d3353a000dda6132e07b1411efd9bde696bac811"
    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "714af8f25e3346b4a8c9e9a49f5f1342d89c9f49e3eb6d7699c70a9c09d1734e"
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

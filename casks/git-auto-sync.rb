cask "git-auto-sync" do
  version "1.0.1"

  on_arm do
    sha256 "ceb08d472a4ee0e6535d80b39ea2bf984d7bc69d0a5f5ea69b72e55f23e918cf"
    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "5816ee3aa851e5bbf8b3c16cd1d6a34e4a7229557781bc416924426dd60764ce"
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

cask "git-auto-sync" do
  version "1.0.2"

  on_arm do
    sha256 "2821b1217afa13a16353a19b28981878b4772a7febfebe4e073f303c70e55a2a"
    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "548bd61c6b9f9a0ee22ed8bd477ab0d445fb2f097b0fe18d9fd7701ff211e256"
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

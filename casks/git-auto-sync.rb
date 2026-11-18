# frozen_string_literal: true

cask "git-auto-sync" do
  version "1.1.0"

  on_arm do
    sha256 "b0ca9760146dd7a416435d71c3413936e23b2f154916e7e78e0f2c2b1a335db3"

    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "aeb351bac9db6feaaa17787a5121d1dea25934ef2d368acc7143434b375673c7"

    url "https://github.com/frankhommers/git-auto-sync/releases/download/v#{version}/GitAutoSync-v#{version}-osx-x64.dmg"
  end

  name "Git Auto Sync"
  desc "Cross-platform Git repository auto-sync with GUI and daemon"
  homepage "https://github.com/frankhommers/git-auto-sync"

  app "Git Auto Sync.app"

  postflight_steps do
    run "/usr/bin/xattr",
        args:         ["-d", "com.apple.quarantine", "{{appdir}}/Git Auto Sync.app"],
        sudo:         false,
        must_succeed: true
  end

  zap trash: [
    "~/.config/git-auto-sync",
    "~/Library/LaunchAgents/com.gitautosync.daemon.plist",
  ]
end

# frozen_string_literal: true

cask "mcp-manager" do
  version "1.12.0"

  on_arm do
    sha256 "3bd3758104f146939677369dc4a70951ddd09d2ef0294fc8a2f8f128f8fbca01"

    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "95b1cad76f230a22266d7d77f7886aea5c920689a1b6d46ab5e712aafd2bcc1d"

    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-x64.dmg"
  end

  name "MCP Manager"
  desc "Cross-platform MCP server management with multi-target export"
  homepage "https://github.com/frankhommers/mcp-manager"

  app "MCP Manager.app"

  postflight_steps do
    run "/usr/bin/xattr",
        args:         ["-d", "com.apple.quarantine", "{{appdir}}/MCP Manager.app"],
        sudo:         false,
        must_succeed: true
  end

  zap trash: "~/.config/mcp-manager"
end

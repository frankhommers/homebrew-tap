# frozen_string_literal: true

cask "mcp-manager" do
  version "1.11.0"

  on_arm do
    sha256 "a22f9b601333c3dd8b08744f86bcba29d12a755be77f15aeee5c51a4bd4fc0bf"

    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "ae5390fc1976564da9d4ab8258a4be007daab03c63be9a74c6edddc2a630d5b7"

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

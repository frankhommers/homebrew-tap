# frozen_string_literal: true

cask "mcp-manager" do
  version "1.13.0"

  on_arm do
    sha256 "885f0352d1fac73228ad29aa46d8150ca7e672e1b26d9af6b0c1f6cc68f69b7f"

    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "a8be5515658f0e295d1f1e40a155605d3b90528696c738d7cfd5ec4924fa328b"

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

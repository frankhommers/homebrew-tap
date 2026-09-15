# frozen_string_literal: true

cask "mcp-manager" do
  version "1.10.0"

  on_arm do
    sha256 "bd65d9763fe9ecc44b9a3f41bc57e274118b56130754d507e42b0e16a9075798"

    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "1cb1c9003f212a123c7ed90739e91ae65db131c75070819a02b2c43b65080e07"

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

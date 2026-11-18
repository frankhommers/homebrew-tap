# frozen_string_literal: true

cask "mcp-manager" do
  version "1.13.1"

  on_arm do
    sha256 "9ad9928165262cfa312bf6f6c67fc245835628b5f46a5d8a824dd2b4d98eaadc"

    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "55df51e9b252c40cfc93604212ec61c923ab4af0f5ffa15a386aae9793374d6f"

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

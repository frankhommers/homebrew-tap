# frozen_string_literal: true

cask "mcp-manager" do
  version "1.14.0"

  on_arm do
    sha256 "b78422bee60e15842db15b181117e6720ca91327a9e8c730527328c0ff8a9a67"

    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end
  on_intel do
    sha256 "6b944f77f5f4d39d3b8252206b92282d88bf7f355680c830ab9c7c5f4437ff7f"

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

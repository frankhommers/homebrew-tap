cask "mcp-manager" do
  version "1.1.0"

  on_arm do
    sha256 "072c81452681fe6a28339bac4cf8642d817efcd6dfc19cc63e7e560017181af8"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "34ded5154704af9809d59212e7b38996246cb00bf0b993eeb8e9e8f9438cd22a"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-x64.dmg"
  end

  name "MCP Manager"
  desc "Cross-platform MCP server management with multi-target export"
  homepage "https://github.com/frankhommers/mcp-manager"

  app "MCP Manager.app"

  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-d", "com.apple.quarantine", "#{appdir}/MCP Manager.app"],
                   sudo: false
  end

  zap trash: [
    "~/.config/mcp-manager",
  ]
end

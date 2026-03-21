cask "mcp-manager" do
  version "1.2.0"

  on_arm do
    sha256 "3c4cb6c3df65747cd478f7b238e61cf12b917733ab6c146df24ad6d95db73863"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "a57077e538c2df39e07cde5f14fffac8cb86745c283f5a000737f9e35f7a771c"
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

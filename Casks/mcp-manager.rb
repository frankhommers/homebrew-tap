cask "mcp-manager" do
  version "1.0.0"

  on_arm do
    sha256 "2c1e586c150bf84119e1b21930309ace8c2764341b3641c7c489d1623049c69a"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "f6266b02de03027b367c3c9decc5fb3ce97f30750acdc4355fd1a6d471160f2c"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-x64.dmg"
  end

  name "MCP Manager"
  desc "Cross-platform MCP server management with multi-target export"
  homepage "https://github.com/frankhommers/mcp-manager"

  app "MCP Manager.app"

  zap trash: [
    "~/.config/mcp-manager",
  ]
end

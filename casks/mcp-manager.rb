cask "mcp-manager" do
  version "1.0.0"

  on_arm do
    sha256 "e55823a25c1bf8a456c2add5397a1acb1ad73a6f7565593fab387d23232e70bc"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "508afdc8b6561a11c741dfd1119731b3da756e334846d3006782c9804da9d260"
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

cask "mcp-manager" do
  version "1.0.0"

  on_arm do
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
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

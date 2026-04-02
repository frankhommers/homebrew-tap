cask "mcp-manager" do
  version "1.8.0"

  on_arm do
    sha256 "2a14dfdc48d4a23f5594e6ad04963fc7f53e068f9e68bdbe622ab23eb4516167"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "fbe185ca1e756f8d319b9620f2a8efaf36a147d5ef888f997fff64a63cb1efad"
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

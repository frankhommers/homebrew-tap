cask "mcp-manager" do
  version "1.6.3"

  on_arm do
    sha256 "2ad486920cabb478bd8727b4a851c4bdbd242df9a2e0bff891822cbe6c87270c"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "62cc49647a86bbf0e734076fb482773480de1b6e104eb32bd4c84f9aa1387bc9"
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

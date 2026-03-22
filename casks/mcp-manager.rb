cask "mcp-manager" do
  version "1.2.1"

  on_arm do
    sha256 "7e0a6d90a14bddf371c09bbfaa25e07ef70ac945863cbaecba6dbc7e8a7fd0d4"
    url "https://github.com/frankhommers/mcp-manager/releases/download/v#{version}/McpManager-v#{version}-osx-arm64.dmg"
  end

  on_intel do
    sha256 "fc8289bd4d894e56b319412efb8b2a3b31775a1a47fde8f7555d6de5845607fa"
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

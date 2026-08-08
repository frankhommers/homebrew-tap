# LET OP: dit bestand wordt gegenereerd door scripts/generate-tmux-formula.py
# Niet met de hand aanpassen; wijzig het script en draai het opnieuw.
#
# Afgeleid van homebrew-core met één toevoeging: een Info.plist wordt in de
# binary gelinkt zodat macOS tmux herkent voor Local Network Privacy. Zonder
# die patch krijgt alles wat je ín tmux draait EHOSTUNREACH op LAN-adressen.
#
# Achtergrond: https://colosieve.com/posts/fixing-tmux-local-network-privacy-macos/

class Tmux < Formula
  desc "Terminal multiplexer (met Info.plist voor macOS Local Network Privacy)"
  homepage "https://tmux.github.io/"
  url "https://github.com/tmux/tmux/releases/download/3.7b/tmux-3.7b.tar.gz"
  sha256 "87f2e99e3b685973f2ca002ffd6ed7e51a5744f7009daae5a15670b6d532db96"
  license "ISC"
  compatibility_version 1

  livecheck do
    url :stable
    regex(/v?(\d+(?:\.\d+)+[a-z]?)/i)
    strategy :github_latest
  end


  head do
    url "https://github.com/tmux/tmux.git", branch: "master"

    depends_on "autoconf" => :build
    depends_on "automake" => :build
    depends_on "libtool" => :build
  end

  depends_on "pkgconf" => :build
  depends_on "libevent"
  depends_on "ncurses"
  depends_on "utf8proc"

  uses_from_macos "bison" => :build # for yacc

  def install

    if OS.mac?
      (buildpath/"Info.plist").write <<~XML
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>CFBundleIdentifier</key>
            <string>com.github.tmux</string>
            <key>CFBundleName</key>
            <string>tmux</string>
            <key>CFBundleVersion</key>
            <string>#{version}</string>
            <key>NSLocalNetworkUsageDescription</key>
            <string>tmux runs terminal sessions that may access hosts on the local network.</string>
        </dict>
        </plist>
      XML

      ENV.append "LDFLAGS", "-Wl,-sectcreate,__TEXT,__info_plist,#{buildpath}/Info.plist"
    end
    system "sh", "autogen.sh" if build.head?

    args = %W[
      --enable-sixel
      --sysconfdir=#{etc}
      --enable-utf8proc
    ]

    # tmux finds the `tmux-256color` terminfo provided by our ncurses
    # and uses that as the default `TERM`, but this causes issues for
    # tools that link with the very old ncurses provided by macOS.
    # https://github.com/Homebrew/homebrew-core/issues/102748
    args << "--with-TERM=screen-256color" if OS.mac? && MacOS.version < :sonoma

    system "./configure", *args, *std_configure_args
    system "make", "install"

    pkgshare.install "example_tmux.conf"

    # Ad-hoc signeren nádat de plist erin gelinkt is; zonder geldige handtekening
    # negeert macOS de sectie.
    system "codesign", "--sign", "-", "--force", bin/"tmux" if OS.mac?
  end

  def caveats
    return unless OS.mac?

    <<~EOS
      Deze tmux bevat een ingebedde Info.plist zodat macOS hem herkent voor
      Local Network Privacy.

      Een draaiende tmux-server houdt de oude binary in geheugen. Start een
      nieuwe server om te testen zonder je sessies te verliezen:

        tmux -L test new-session

      Verschijnt er geen prompt, kijk dan in Systeeminstellingen ->
      Privacy en beveiliging -> Lokaal netwerk en zet 'tmux' aan.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/tmux -V")

    on_macos do
      assert_match "__info_plist", shell_output("otool -l #{bin}/tmux")
      assert_match "com.github.tmux", shell_output("codesign -dvvv #{bin}/tmux 2>&1")
    end
  end
end

#!/usr/bin/env python3
"""
Genereert Formula/tmux.rb uit homebrew-core, met onze macOS-patch erin.

Waarom: macOS 15+ blokkeert lokaal netwerkverkeer voor processen zonder
herkenbare app-identiteit in de parent-keten. tmux daemoniseert en is ad-hoc
gesigneerd zonder bundle-ID, dus alles wat je ín tmux draait (node, python, go)
krijgt EHOSTUNREACH op LAN-adressen. De fix is een Info.plist linken in de
__TEXT,__info_plist sectie en daarna ad-hoc signeren.

Deze aanpak kopieert de formula niet, maar leidt hem elke keer opnieuw af van
core. Zo volgen we upstream automatisch: nieuwe versies, gewijzigde
dependencies, aangepaste configure-flags.

Faalt de injectie omdat core van structuur veranderd is, dan stopt dit script
met een foutmelding in plaats van stilletjes iets verkeerds te schrijven.
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

CORE_URL = "https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/t/tmux.rb"
OUT = Path(__file__).resolve().parent.parent / "Formula" / "tmux.rb"

HEADER = """# LET OP: dit bestand wordt gegenereerd door scripts/generate-tmux-formula.py
# Niet met de hand aanpassen; wijzig het script en draai het opnieuw.
#
# Afgeleid van homebrew-core met één toevoeging: een Info.plist wordt in de
# binary gelinkt zodat macOS tmux herkent voor Local Network Privacy. Zonder
# die patch krijgt alles wat je ín tmux draait EHOSTUNREACH op LAN-adressen.
#
# Achtergrond: https://colosieve.com/posts/fixing-tmux-local-network-privacy-macos/

"""

PLIST_BLOCK = '''
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
'''

CODESIGN_BLOCK = '''
    # Ad-hoc signeren nádat de plist erin gelinkt is; zonder geldige handtekening
    # negeert macOS de sectie.
    system "codesign", "--sign", "-", "--force", bin/"tmux" if OS.mac?
'''

CAVEATS_AND_TEST = '''
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
'''


def die(msg: str) -> None:
    print(f"FOUT: {msg}", file=sys.stderr)
    print(
        "\nDe structuur van homebrew-core's tmux.rb is waarschijnlijk gewijzigd.\n"
        "Pas scripts/generate-tmux-formula.py aan.",
        file=sys.stderr,
    )
    sys.exit(1)


def fetch_core() -> str:
    req = urllib.request.Request(CORE_URL, headers={"User-Agent": "homebrew-tap-sync"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            die(f"kon core formula niet ophalen (HTTP {resp.status})")
        return resp.read().decode("utf-8")


def strip_bottle(src: str) -> str:
    """Bottles van core horen bij core's ongepatchte build. Laten staan zou
    betekenen dat Homebrew die binary downloadt en onze patch overslaat."""
    pattern = re.compile(r"\n  bottle do\n.*?\n  end\n", re.DOTALL)
    if not pattern.search(src):
        die("geen bottle-blok gevonden om te verwijderen")
    return pattern.sub("\n", src, count=1)


def patch_desc(src: str) -> str:
    pattern = re.compile(r'^  desc "([^"]*)"$', re.MULTILINE)
    if not pattern.search(src):
        die("desc-regel niet gevonden")
    return pattern.sub(
        r'  desc "\1 (met Info.plist voor macOS Local Network Privacy)"', src, count=1
    )


def inject_plist(src: str) -> str:
    """Direct na 'def install' invoegen, vóór de rest van de installatie."""
    marker = "\n  def install\n"
    if marker not in src:
        die("'def install' niet gevonden")
    return src.replace(marker, marker + PLIST_BLOCK, 1)


def inject_codesign(src: str) -> str:
    """Aan het eind van def install, direct vóór de afsluitende 'end'.

    We zoeken de laatste regel van de install-methode door te knippen bij de
    eerstvolgende regel die op kolom 2 eindigt met 'end'.
    """
    start = src.index("\n  def install\n")
    end_match = re.search(r"\n  end\n", src[start:])
    if not end_match:
        die("einde van 'def install' niet gevonden")
    insert_at = start + end_match.start()
    return src[:insert_at] + "\n" + CODESIGN_BLOCK.rstrip("\n") + src[insert_at:]


def replace_tail(src: str) -> str:
    """Core's eigen caveats/test vervangen door die van ons."""
    # Alles vanaf een eventuele 'def caveats' of 'test do' tot het eind weg.
    for marker in ("\n  def caveats\n", "\n  test do\n"):
        idx = src.find(marker)
        if idx != -1:
            return src[:idx] + CAVEATS_AND_TEST
    # Geen van beide aanwezig: alleen de laatste 'end' vervangen.
    idx = src.rstrip().rfind("\nend")
    if idx == -1:
        die("kon het einde van de class niet bepalen")
    return src[:idx] + CAVEATS_AND_TEST


def main() -> None:
    src = fetch_core()

    if "class Tmux < Formula" not in src:
        die("dit lijkt geen tmux-formula")

    src = strip_bottle(src)
    src = patch_desc(src)
    src = inject_plist(src)
    src = inject_codesign(src)
    src = replace_tail(src)
    src = HEADER + src

    # Controle: zit alles er echt in?
    for needle in ("__info_plist", "codesign", "NSLocalNetworkUsageDescription"):
        if needle not in src:
            die(f"'{needle}' ontbreekt in het resultaat")
    if "bottle do" in src:
        die("bottle-blok zit er nog in")

    version = re.search(r'url ".*/tmux-([^/"]+)\.tar\.gz"', src)
    print(f"core-versie: {version.group(1) if version else 'onbekend'}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    old = OUT.read_text() if OUT.exists() else ""
    if old == src:
        print("geen wijziging")
        return

    OUT.write_text(src)
    print(f"geschreven: {OUT}")


if __name__ == "__main__":
    main()

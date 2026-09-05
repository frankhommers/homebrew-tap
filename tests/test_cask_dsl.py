"""Keep all checked-in casks on the supported Homebrew DSL."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEGACY_APPS = {
    "git-auto-sync": "Git Auto Sync.app",
    "mcp-manager": "MCP Manager.app",
    "rclone-mount-manager": "Rclone Mount Manager.app",
}


class CaskDSLTests(unittest.TestCase):
    def test_no_deprecated_stanzas_in_any_cask(self):
        paths = sorted((ROOT / "casks").glob("*.rb"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(cask=path.stem):
                text = path.read_text()
                self.assertNotRegex(text, r"(?m)^\s*(?:preflight|postflight|uninstall_preflight|uninstall_postflight)\s+do\b")
                self.assertNotRegex(text, r"\bverified\s*:")
                self.assertNotRegex(text, r'depends_on\s+macos:\s*"')

    def test_legacy_apps_preserve_the_existing_scoped_command(self):
        for token, app in LEGACY_APPS.items():
            with self.subTest(cask=token):
                text = (ROOT / "casks" / f"{token}.rb").read_text()
                block = re.search(r"(?ms)^  postflight_steps do\n(.*?)^  end$", text)
                self.assertIsNotNone(block, "Use structured postflight_steps")
                assert block is not None
                body = re.sub(r"(?<=:)[ \t]+", " ", block[1])
                self.assertIn('run "/usr/bin/xattr",', body)
                self.assertIn(f'args: ["-d", "com.apple.quarantine", "{{{{appdir}}}}/{app}"],', body)
                self.assertIn("sudo: false", body)
                self.assertIn("must_succeed: true", body)
                self.assertNotIn("#{", body, "Resolve appdir at install time, not JSON generation")
                self.assertNotIn("system_command", body)
                self.assertNotIn('"-r"', body, "Do not widen existing quarantine removal")

    def test_hermes_has_no_quarantine_removal_hook(self):
        text = (ROOT / "casks/hermes-desktop.rb").read_text()
        self.assertNotRegex(text, r"(?m)^\s*(?:postflight_steps|postflight|system_command|run)\b")
        self.assertNotIn("com.apple.quarantine", text)

    def test_payload_fields_remain_well_formed(self):
        for path in sorted((ROOT / "casks").glob("*.rb")):
            with self.subTest(cask=path.stem):
                text = path.read_text()
                self.assertRegex(text, r'(?m)^  version "[0-9]+(?:\.[0-9]+)+"$')
                self.assertEqual(len(re.findall(r'(?m)^    sha256 "[0-9a-f]{64}"$', text)), 2)
                self.assertEqual(len(re.findall(r'(?m)^    url "https://github\.com/frankhommers/', text)), 2)


if __name__ == "__main__":
    unittest.main()

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-casks.py"
SPEC = importlib.util.spec_from_file_location("validate_casks", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidateCasksTrustTests(unittest.TestCase):
    def test_accepts_only_explicit_trust_for_this_tap(self):
        MODULE.require_tap_trusted('{"taps":["frankhommers/tap"]}')
        for raw in ('{}', '{"taps":[]}', '{"taps":["someone/else"]}', 'not-json'):
            with self.subTest(raw=raw), self.assertRaises(RuntimeError):
                MODULE.require_tap_trusted(raw)

    def test_trust_is_explicit_and_no_bypass_is_present(self):
        source = SCRIPT.read_text()
        trust_position = source.index('run("trust-tap"')
        tap_position = source.index('run("tap"')
        self.assertLess(trust_position, tap_position)
        self.assertIn('run("trust-before-tap"', source)
        self.assertIn('run("trust-after-tap"', source)
        self.assertIn('run("tap", "brew", "tap", TAP)', source)
        self.assertNotIn('run("tap", "brew", "tap", TAP, str(ROOT))', source)
        self.assertNotIn("HOMEBREW_NO_REQUIRE_TAP_TRUST", source)


if __name__ == "__main__":
    unittest.main()
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('sync_hermes',Path(__file__).resolve().parents[1]/'scripts/sync-hermes-desktop.py')
assert spec is not None and spec.loader is not None
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)

class SyncTests(unittest.TestCase):
    def fixture(self):
        # Metadata-only fixture; no app or pretend release is produced.
        m={'schema':1,'buildRepository':sync.REPO,'version':'0.17.0.1','buildRun':f'https://github.com/{sync.REPO}/actions/runs/123','targets':{}}
        for platform,arch in [('darwin','arm64'),('darwin','x64'),('win32','x64'),('linux','x64')]:
            m['targets'][platform+'-'+arch]={'archive':f'Hermes-0.17.0.1-{platform}-{arch}-unsigned.zip','sha256':'1'*64,'sourceClean':True,'archiveRoundtrip':True,'nativeSmoke':{'platform':platform,'arch':arch,'errors':[]}}
        return m

    def test_cask_has_no_security_bypass(self):
        text=sync.render(self.fixture())
        self.assertIn('app "Hermes.app"',text)
        for forbidden in ('postflight','system_command','xattr','sha256 :no_check'):
            self.assertNotIn(forbidden,text)

    def test_missing_or_mismatched_build_blocks(self):
        for mutation in [lambda m:m['targets'].pop('linux-x64'),lambda m:m.update(buildRepository='untrusted/repo'),lambda m:m['targets']['darwin-arm64'].update(sha256='no_check'),lambda m:m['targets']['darwin-x64']['nativeSmoke'].update(arch='arm64')]:
            m=self.fixture();mutation(m)
            with self.assertRaises(ValueError):sync.render(m)

    def test_versions_are_compared_numerically(self):
        self.assertGreater(sync.version_tuple('0.17.0.10'),sync.version_tuple('0.17.0.9'))
        with self.assertRaises(ValueError):sync.version_tuple('main')

if __name__=='__main__':unittest.main()

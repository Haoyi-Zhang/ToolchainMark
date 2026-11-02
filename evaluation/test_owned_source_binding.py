"""Retained owned rows bind fixed historical bytes, never a later checkout."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from derive_owned_native import ROOT, RETAINED_SOURCE_VERSIONS, RETAINED_PREIMAGES, verify_recorded_sources

class OwnedSourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='owned-source-binding-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.snapshot=self.root/'results/native-execution/source-snapshot'
        for name in RETAINED_SOURCE_VERSIONS:
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
            captured=ROOT/RETAINED_PREIMAGES[name] if name in RETAINED_PREIMAGES else None
            if captured is not None and captured.is_file():
                target=self.root/RETAINED_PREIMAGES[name];target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(captured,target)
        self.summary={'source_versions':copy.deepcopy(RETAINED_SOURCE_VERSIONS)}

    def test_registered_identity_uses_exact_preserved_admission(self):
        report=verify_recorded_sources(self.summary,self.root)
        self.assertEqual(report['recorded_sources'],6)
        self.assertEqual(set(report['preserved_source_files_used']),set(RETAINED_PREIMAGES))
        self.assertEqual(len(report['current_source_files_used']),4)

    def test_missing_or_corrupt_preimage_fails_closed(self):
        for relative in RETAINED_PREIMAGES.values():
            captured=self.root/relative
            original=captured.read_bytes()
            captured.unlink()
            with self.assertRaisesRegex(ValueError,'historical source bytes differ'):
                verify_recorded_sources(self.summary,self.root)
            captured.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'historical source bytes differ'):
                verify_recorded_sources(self.summary,self.root)
            captured.write_bytes(original)

    def test_live_source_cannot_substitute_for_recorded_source(self):
        shutil.copyfile(self.root/'src/tosem02/admission.py',self.snapshot/'src/tosem02/admission.py')
        with self.assertRaisesRegex(ValueError,'historical source bytes differ'):
            verify_recorded_sources(self.summary,self.root)

    def test_relabeling_summary_to_current_code_is_rejected(self):
        import hashlib
        self.summary['source_versions']['src/tosem02/admission.py']=hashlib.sha256((self.root/'src/tosem02/admission.py').read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'registered source identities differ'):
            verify_recorded_sources(self.summary,self.root)

    def test_extra_missing_and_traversal_source_keys_are_rejected(self):
        for mode in ('extra','missing','traversal'):
            summary=copy.deepcopy(self.summary)
            if mode=='missing':summary['source_versions'].pop('src/tosem02/admission.py')
            else:summary['source_versions']['../outside' if mode=='traversal' else 'extra.py']='0'*64
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'registered source identities differ'):
                verify_recorded_sources(summary,self.root)

if __name__=='__main__':unittest.main()

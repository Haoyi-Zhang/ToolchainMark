"""Reference consumers must use the artifact's current receipt, fail closed."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ARTIFACT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('receipt_package', ARTIFACT/'scripts/verify_package.py')
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


class ReferenceReceiptLocationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='reference-receipt-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root/'paper/evidence').mkdir(parents=True)
        (self.root/'artifact/evidence').mkdir(parents=True)
        (self.root/'artifact/scripts').mkdir(parents=True)
        shutil.copyfile(ARTIFACT/'scripts/audit_references.py', self.root/'artifact/scripts/audit_references.py')
        (self.root/'paper/main.tex').write_text('Owned fixture. \\cite{owned}.\n', encoding='utf-8')
        (self.root/'paper/references.bib').write_text(
            '@article{owned,\n  author={Fixture, Example},\n  title={Owned reference},\n'
            '  year={2000},\n  doi={10.1234/owned}\n}\n', encoding='utf-8')
        record={'citation_key':'owned', 'title':'Owned reference', 'authors':'Fixture, Example',
                'year':2000, 'doi':'10.1234/owned'}
        (self.root/'paper/evidence/reference_records.json').write_text(json.dumps([record]), encoding='utf-8')
        receipt={**record, 'record_located_this_revision':False, 'inherited_receipt_sha256':'0'*64}
        (self.root/'artifact/evidence/reference_review_current.json').write_text(json.dumps([receipt]), encoding='utf-8')

    def test_current_receipt_is_in_artifact_and_readable_by_both_consumers(self):
        spec = importlib.util.spec_from_file_location('receipt_audit', self.root/'artifact/scripts/audit_references.py')
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        self.assertEqual(audit.RECEIPTS, self.root/'artifact/evidence/reference_review_current.json')
        receipts = json.loads(audit.RECEIPTS.read_text(encoding='utf-8'))
        self.assertTrue(any(row.get('inherited_receipt_sha256') for row in receipts))
        ok, details = PACKAGE.check_references(self.root)
        self.assertTrue(ok, details)

    def test_retired_paper_location_does_not_mask_missing_current_receipt(self):
        current = self.root/'artifact/evidence/reference_review_current.json'
        current.rename(self.root/'paper/evidence/reference_review_current.json')
        ok, details = PACKAGE.check_references(self.root)
        self.assertFalse(ok, details)

    def test_duplicate_current_receipt_rejects(self):
        path = self.root/'artifact/evidence/reference_review_current.json'
        rows = json.loads(path.read_text(encoding='utf-8'))
        rows.append(rows[0])
        path.write_text(json.dumps(rows), encoding='utf-8')
        ok, details = PACKAGE.check_references(self.root)
        self.assertFalse(ok, details)


if __name__ == '__main__':
    unittest.main()

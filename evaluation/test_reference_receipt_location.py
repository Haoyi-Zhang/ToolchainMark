"""Reference consumers must use the artifact's current receipt, fail closed."""
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import copy
import os
import subprocess
import sys
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
        record={'number':1, 'citation_key':'owned', 'title':'Owned reference', 'authors':'Fixture, Example',
                'year':2000, 'doi':'10.1234/owned'}
        (self.root/'paper/evidence/reference_records.json').write_text(json.dumps([record]), encoding='utf-8')
        receipt={**record, 'record_located_this_revision':False, 'inherited_receipt_sha256':'0'*64,
                 'locator':'https://doi.org/10.1234/owned','source_class':'owned fixture',
                 'verification_scope':'Owned schema fixture; not a scholarly existence claim'}
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

    def test_companion_receipts_require_exact_bibliography_and_preserve_canonical(self):
        canonical = self.root/'artifact/evidence/reference_review_current.json'
        original = canonical.read_bytes()
        bibliography = self.root/'paper/references.bib'
        companion = canonical.with_name('reference_review_companion.json')
        contents = {'bibliography_sha256': hashlib.sha256(bibliography.read_bytes()).hexdigest(),
                    'receipts': json.loads(original)}
        companion.write_text(json.dumps(contents), encoding='utf-8')
        ok, details = PACKAGE.check_references(self.root)
        self.assertTrue(ok, details)
        self.assertTrue(details['receipt'].endswith(companion.name))
        completed = subprocess.run(
            [sys.executable, '-B', str(self.root/'artifact/scripts/audit_references.py')],
            capture_output=True, text=True, encoding='utf-8', timeout=15)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue((self.root/'paper/reference_support.csv').is_file())
        self.assertFalse((self.root/'artifact/citation_support.csv').exists())
        self.assertEqual(original, canonical.read_bytes())
        bibliography.write_bytes(bibliography.read_bytes()+b'\n')
        ok, details = PACKAGE.check_references(self.root)
        self.assertTrue(ok, details)
        self.assertTrue(details['receipt'].endswith(canonical.name))

    def test_duplicate_current_receipt_rejects(self):
        path = self.root/'artifact/evidence/reference_review_current.json'
        rows = json.loads(path.read_text(encoding='utf-8'))
        rows.append(rows[0])
        path.write_text(json.dumps(rows), encoding='utf-8')
        ok, details = PACKAGE.check_references(self.root)
        self.assertFalse(ok, details)

    def assert_rejected_by_both_consumers(self):
        ok, details = PACKAGE.check_references(self.root)
        self.assertFalse(ok, details)
        completed = subprocess.run(
            [sys.executable, '-B', str(self.root/'artifact/scripts/audit_references.py')],
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'},
            capture_output=True, text=True, encoding='utf-8', timeout=15)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        for relative in ('paper/reference_verification_audit.json',
                         'paper/reference_line_by_line_audit.csv', 'artifact/citation_support.csv'):
            self.assertFalse((self.root/relative).exists(), relative)

    def test_duplicate_bibliography_keys_reject_in_both_orders(self):
        path=self.root/'paper/references.bib'
        original=path.read_text(encoding='utf-8')
        changed=original.replace('Owned reference','Conflicting reference')
        for text in (original+original, changed+original, original+changed, ' '+original+original):
            with self.subTest(text=text):
                path.write_text(text,encoding='utf-8')
                self.assert_rejected_by_both_consumers()

    def test_duplicate_bibliography_fields_reject(self):
        path=self.root/'paper/references.bib'
        text=path.read_text(encoding='utf-8').replace('  author=', '  author={Other, Person},\n  author=',1)
        path.write_text(text,encoding='utf-8')
        self.assert_rejected_by_both_consumers()

    def test_invalid_and_resolver_DOI_variants_reject(self):
        record_path=self.root/'paper/evidence/reference_records.json'
        receipt_path=self.root/'artifact/evidence/reference_review_current.json'
        bib_path=self.root/'paper/references.bib'
        record=json.loads(record_path.read_text(encoding='utf-8'))
        receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
        bib=bib_path.read_text(encoding='utf-8')
        for invalid in ('not-a-doi','10.0/owned','https://doi.org/10.1234/owned','doi:10.1234/owned'):
            with self.subTest(doi=invalid):
                rr=copy.deepcopy(record);ss=copy.deepcopy(receipt)
                rr[0]['doi']=invalid;ss[0]['doi']=invalid
                record_path.write_text(json.dumps(rr),encoding='utf-8')
                receipt_path.write_text(json.dumps(ss),encoding='utf-8')
                bib_path.write_text(bib.replace('10.1234/owned',invalid),encoding='utf-8')
                self.assert_rejected_by_both_consumers()

    def test_receipt_location_flags_require_real_booleans(self):
        path=self.root/'artifact/evidence/reference_review_current.json'
        original=json.loads(path.read_text(encoding='utf-8'))
        for invalid in ('false','true',0,1,None,[],{}):
            with self.subTest(value=invalid):
                rows=copy.deepcopy(original);rows[0]['record_located_this_revision']=invalid
                path.write_text(json.dumps(rows),encoding='utf-8')
                self.assert_rejected_by_both_consumers()

    def test_required_receipt_fields_reject_when_absent(self):
        path=self.root/'artifact/evidence/reference_review_current.json'
        original=json.loads(path.read_text(encoding='utf-8'))
        for field in ('locator','source_class','verification_scope'):
            with self.subTest(field=field):
                rows=copy.deepcopy(original);del rows[0][field]
                path.write_text(json.dumps(rows),encoding='utf-8')
                self.assert_rejected_by_both_consumers()

    def test_DOI_author_mismatch_rejects(self):
        path=self.root/'paper/references.bib'
        path.write_text(path.read_text(encoding='utf-8').replace('Fixture, Example','Unrelated, Person'),encoding='utf-8')
        self.assert_rejected_by_both_consumers()

    def test_inherited_false_does_not_become_fresh(self):
        script=self.root/'artifact/scripts/audit_references.py'
        completed=subprocess.run([sys.executable,'-B',str(script)],capture_output=True,text=True,
                                 encoding='utf-8',timeout=15,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        self.assertEqual(completed.returncode,0,completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['fresh_documented_record_checks'],0)

    def test_author_normalization_preserves_nonlatin_distinctions(self):
        spec=importlib.util.spec_from_file_location('receipt_unicode_audit',self.root/'artifact/scripts/audit_references.py')
        audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
        self.assertNotEqual(audit.normalize_people('张三'),audit.normalize_people('李四'))
        self.assertEqual(audit.normalize_people('Josipović'),audit.normalize_people("Josipovi{\\'c}"))


if __name__ == '__main__':
    unittest.main()

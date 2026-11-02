"""Retained aggregate consistency, without native or compiler execution."""
import copy
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import owned_record_summary as records

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'results/owned-native-full-20261014-001'

class OwnedRecordSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads((RUN/'summary.json').read_text(encoding='utf-8'))
        cls.rows=[json.loads(line) for line in gzip.decompress((RUN/'raw.jsonl.gz').read_bytes()).splitlines()]

    def test_retained_aggregates_reconstruct_exactly(self):
        result=records.validate_summary(self.rows,self.summary)
        self.assertEqual((result['rows'],result['emitted_objects'],result['native_calls']),(704,832,5760))
        self.assertEqual(result['cohorts']['clean-workflow'],{'SATISFIED':320})

    def test_summary_drift_is_rejected_without_changing_raw_rows(self):
        for key,value in [('cohorts',{'clean-workflow':{'SATISFIED':319,'INCONSISTENT':1}}),
                          ('emitted_objects',999),('emitted_object_bytes',999),
                          ('native_calls',999),('case_wall_sum',999),('case_cpu_sum',999),
                          ('rows',True),('case_wall_sum',float('nan'))]:
            summary=copy.deepcopy(self.summary);summary[key]=value
            with self.subTest(field=key),self.assertRaises(ValueError):
                records.validate_summary(self.rows,summary)

    def test_raw_invalid_verdict_or_time_is_rejected(self):
        for key,value in [('verdict','UNKNOWN'),('case_seconds',float('inf')),
                          ('case_cpu_seconds',-1),('host_reference_differences',False)]:
            rows=copy.deepcopy(self.rows);rows[0][key]=value
            with self.subTest(field=key),self.assertRaises(ValueError):records.validate_summary(rows,self.summary)

    def test_deriver_consumes_validated_aggregates(self):
        import sys
        sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
        import derive_owned_native
        original=Path.read_text
        summary=copy.deepcopy(self.summary);summary['case_wall_sum']=999
        def read(path,*args,**kwargs):
            return json.dumps(summary) if path==RUN/'summary.json' else original(path,*args,**kwargs)
        with patch.object(Path,'read_text',read),self.assertRaisesRegex(ValueError,'summary/raw'):
            derive_owned_native.derive(RUN)

    def test_raw_calls_vectors_and_action_evidence_fail_closed(self):
        import tempfile
        import derive_owned_native
        for mode in ('wrong-call','missing-builds','empty-vectors','bad-input','bad-artifact','missing-extraction','contradictory-observation'):
            rows=copy.deepcopy(self.rows);summary=copy.deepcopy(self.summary)
            if mode=='wrong-call':
                next(r for r in rows if r['host_calls'])['host_calls'][0]['native']^=1
            elif mode=='missing-builds':
                for r in rows:r['builds']=[];r['host_calls']=[]
                summary.update(emitted_objects=0,emitted_object_bytes=0,native_calls=0)
            elif mode=='empty-vectors':
                for r in rows:
                    for b in r['builds']:b['native_inputs']=[];b['native_outputs']=[];b['reference_outputs']=[]
                    r['host_calls']=[]
                summary['native_calls']=0
            elif mode=='bad-input':next(r for r in rows if r['host_calls'])['host_calls'][0]['input']=False
            elif mode=='bad-artifact':next(r for r in rows if r['host_calls'])['host_calls'][0]['artifact_sha256']='0'*64
            elif mode=='missing-extraction':rows[0]['extractions']=[]
            else:rows[0]['observations']['extraction']['value']='00'
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary)
                (root/'summary.json').write_text(json.dumps(summary),encoding='utf-8')
                (root/'raw.jsonl.gz').write_bytes(gzip.compress(b'\n'.join(json.dumps(r).encode() for r in rows)))
                with self.assertRaises(ValueError):derive_owned_native.derive(root)

if __name__=='__main__':unittest.main()

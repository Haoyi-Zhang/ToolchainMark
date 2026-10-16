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

if __name__=='__main__':unittest.main()

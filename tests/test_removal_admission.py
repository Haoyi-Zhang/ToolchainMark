"""Finite MR09 repair verification, not a native/compiler campaign replay.

Owned byte records exercise the current handler. Retained matrices are only
read to check compatibility of their recorded MR09 observations and verdicts;
they are not relabelled or claimed to execute the repaired code.
"""
import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tosem02.admission import evaluate, inspect_carrier, no_accepted_carrier
from tosem02.catalog import artifact_root
from tosem02.model import ExtractionError
from tosem02.record import MAGIC, locate_record, make_record
from tosem02.relations import KEY1, KEY2, PAYLOAD1, PAYLOAD2
from test_repair_models import ByteBuildPipeline


class RemovalModelPipeline(ByteBuildPipeline):
    def __init__(self, *, prefix=b'', suffix=b'', mutant='CLEAN', reject=None,
                 accept=False, failure=None):
        super().__init__(mutant=mutant)
        self.prefix, self.suffix = prefix, suffix
        self.reject, self.accept, self.failure = reject, accept, failure
        self.followup = None
        self.followup_extractions = 0

    def build(self, request):
        result = super().build(request)
        result.binary.write_bytes(self.prefix + result.binary.read_bytes() + self.suffix)
        return result

    def remove_carrier(self, result, directory):
        self.followup = super().remove_carrier(result, directory)
        return self.followup

    def extract(self, binary, key):
        if binary == self.followup:
            self.followup_extractions += 1
            if self.failure is not None:
                raise self.failure
            if self.accept:
                return PAYLOAD1
            if self.reject is not None:
                raise ExtractionError(self.reject, 'owned follow-up control')
        return super().extract(binary, key)


class RemovalAdmissionTests(unittest.TestCase):
    def setUp(self):
        guard = patch('subprocess.run', side_effect=AssertionError('No external execution in finite controls'))
        guard.start()
        self.addCleanup(guard.stop)
        self.host = artifact_root() / 'hosts/H01-gcd.c'

    def call(self, pipeline):
        with tempfile.TemporaryDirectory() as temporary:
            return evaluate('MR09', pipeline, self.host, Path(temporary) / 'case')

    def test_normal_removal_preserves_exact_absent_observations(self):
        pipeline = RemovalModelPipeline()
        outcome = self.call(pipeline)
        self.assertEqual(outcome.verdict, 'SATISFIED')
        self.assertTrue(all(outcome.admission.values()))
        self.assertEqual(outcome.observations['followup_carrier'], {'kind': 'rejection', 'value': 'absent'})
        self.assertEqual(outcome.observations['followup'], outcome.observations['followup_carrier'])
        self.assertEqual(pipeline.followup_extractions, 1)

    def test_invalid_candidates_before_valid_record_retain_precise_rejection(self):
        version = bytearray(make_record(b'earlier', KEY1)); version[4] = 2
        malformed = bytearray(make_record(b'earlier', KEY1)); malformed[13:15] = b'\xff\xff'
        checksum = bytearray(make_record(b'earlier', KEY1)); checksum[-1] ^= 1
        prefixes = {'version': bytes(version), 'malformed': bytes(malformed),
                    'wrong-key': make_record(b'earlier', KEY2), 'checksum': bytes(checksum)}
        for reason, prefix in prefixes.items():
            with self.subTest(reason=reason):
                pipeline = RemovalModelPipeline(prefix=prefix)
                outcome = self.call(pipeline)
                expected = {'kind': 'rejection', 'value': reason}
                self.assertEqual(outcome.verdict, 'SATISFIED')
                self.assertTrue(outcome.admission['carrier_removed'])
                self.assertEqual(outcome.observations['followup_carrier'], expected)
                self.assertEqual(outcome.observations['followup'], expected)
                self.assertEqual(pipeline.followup_extractions, 1)

    def test_false_magic_before_or_after_valid_record(self):
        false_magic = MAGIC + b'\xff' * 19
        for location in ('prefix', 'suffix'):
            with self.subTest(location=location):
                outcome = self.call(RemovalModelPipeline(**{location: false_magic}))
                self.assertEqual(outcome.verdict, 'SATISFIED')
                self.assertEqual(outcome.observations['followup_carrier']['value'], 'version')

    def test_second_valid_record_including_empty_payload_blocks_removal(self):
        for payload in (PAYLOAD2, b''):
            with self.subTest(payload=payload):
                pipeline = RemovalModelPipeline(suffix=make_record(payload, KEY1))
                outcome = self.call(pipeline)
                self.assertEqual((outcome.verdict, outcome.reason), ('INADMISSIBLE', 'carrier_removed'))
                self.assertFalse(outcome.admission['carrier_removed'])
                self.assertEqual(outcome.observations['followup_carrier'], {'kind': 'payload', 'value': payload.hex()})
                self.assertEqual(pipeline.followup_extractions, 0)

    def test_removing_both_valid_records_can_establish_removal(self):
        class RemoveBoth(RemovalModelPipeline):
            def remove_carrier(self, result, directory):
                target = super().remove_carrier(result, directory)
                data = bytearray(target.read_bytes())
                start, _ = locate_record(bytes(data), KEY1)
                data[start:start + len(MAGIC)] = b'XXXX'
                target.write_bytes(data)
                return target
        outcome = self.call(RemoveBoth(prefix=MAGIC + b'\xff' * 19,
                                       suffix=make_record(PAYLOAD2, KEY1)))
        self.assertEqual(outcome.verdict, 'SATISFIED')
        self.assertTrue(outcome.admission['carrier_removed'])
        self.assertEqual(outcome.observations['followup']['value'], 'version')

    def test_noop_with_or_without_false_magic_never_reaches_tested_extraction(self):
        for prefix in (b'', MAGIC + b'\xff' * 19):
            with self.subTest(prefix=prefix):
                pipeline = RemovalModelPipeline(prefix=prefix, mutant='M15')
                outcome = self.call(pipeline)
                self.assertEqual((outcome.verdict, outcome.reason), ('INADMISSIBLE', 'carrier_removed'))
                self.assertFalse(outcome.exposed)
                self.assertEqual(pipeline.followup_extractions, 0)

    def test_accepted_payload_after_verified_removal_is_inconsistent(self):
        outcome = self.call(RemovalModelPipeline(prefix=MAGIC + b'\xff' * 19, accept=True))
        self.assertEqual(outcome.verdict, 'INCONSISTENT')
        self.assertTrue(all(outcome.admission.values()))

    def test_different_domain_or_context_rejection_is_not_a_pass(self):
        for reason in ('absent', 'checksum', 'wrong-key', 'malformed', 'path', 'sidecar'):
            with self.subTest(reason=reason):
                outcome = self.call(RemovalModelPipeline(prefix=MAGIC + b'\xff' * 19, reject=reason))
                self.assertEqual(outcome.verdict, 'INCONSISTENT')
                self.assertEqual(outcome.observations['followup_carrier']['value'], 'version')
                self.assertEqual(outcome.observations['followup']['value'], reason)

    def test_tested_tool_unknown_or_io_failure_is_inadmissible(self):
        failures = (OSError('owned I/O failure'), TimeoutError('owned timeout'),
                    ExtractionError('tool', 'owned tool failure'),
                    ExtractionError('unknown', 'owned unknown rejection'))
        for failure in failures:
            with self.subTest(failure=repr(failure)):
                outcome = self.call(RemovalModelPipeline(failure=failure))
                self.assertEqual(outcome.verdict, 'INADMISSIBLE')
                self.assertFalse(outcome.exposed)
                self.assertTrue(outcome.reason.startswith('execution-error:'))

    def test_observer_failure_is_not_removal_evidence(self):
        for failure in (OSError('owned I/O failure'), TimeoutError('owned timeout'),
                        ExtractionError('tool', 'owned tool failure'),
                        ExtractionError('unknown', 'owned unknown rejection')):
            pipeline = RemovalModelPipeline()
            def observer(carrier, binary, key):
                if binary == pipeline.followup:
                    raise failure
                return inspect_carrier(carrier, binary, key)
            with self.subTest(failure=repr(failure)), patch('tosem02.admission.inspect_carrier', side_effect=observer):
                outcome = self.call(pipeline)
                self.assertEqual(outcome.verdict, 'INADMISSIBLE')
                self.assertFalse(outcome.exposed)
                self.assertEqual(pipeline.followup_extractions, 0)

    def test_context_and_unknown_observations_cannot_establish_removal(self):
        for reason in ('path', 'sidecar', 'tool', 'unknown'):
            with self.subTest(reason=reason):
                self.assertFalse(no_accepted_carrier('string', {'kind': 'rejection', 'value': reason}))
                pipeline = RemovalModelPipeline()
                def observer(carrier, binary, key):
                    if binary == pipeline.followup:
                        return {'kind': 'rejection', 'value': reason}
                    return inspect_carrier(carrier, binary, key)
                with patch('tosem02.admission.inspect_carrier', side_effect=observer):
                    outcome = self.call(pipeline)
                self.assertEqual((outcome.verdict, outcome.reason), ('INADMISSIBLE', 'carrier_removed'))
                self.assertEqual(pipeline.followup_extractions, 0)

    def test_symbol_and_section_still_require_representation_absence(self):
        for carrier in ('symbol', 'section'):
            for reason in ('absent', 'version', 'malformed', 'checksum', 'wrong-key'):
                with self.subTest(carrier=carrier, reason=reason):
                    self.assertEqual(no_accepted_carrier(carrier, {'kind': 'rejection', 'value': reason}), reason == 'absent')


class RetainedRemovalCompatibilityTests(unittest.TestCase):
    def test_recorded_mr09_verdicts_remain_historical_not_current_execution(self):
        root = artifact_root()
        paths = [root / 'results/native-execution' / campaign / (run + '.csv')
                 for campaign in ('primary', 'mirror') for run in ('first', 'second')]
        paths += [root / 'results/current-native' / (run + '.csv.gz') for run in ('first', 'second')]
        paths += [root / 'results/admission-study/matrix.csv']
        with patch('tosem02.admission.evaluate', side_effect=AssertionError('Historical rows must not be executed')) as execute:
            for path in paths:
                count = 0
                opener = gzip.open if path.suffix == '.gz' else open
                with self.subTest(path=str(path)), opener(path, 'rt', encoding='utf-8', newline='') as handle:
                    for row in csv.DictReader(handle):
                        if row['relation_id'] != 'MR09':
                            continue
                        count += 1
                        observed = json.loads(row['observations_json'])
                        physical = observed.get('followup_carrier')
                        if physical is not None:
                            # The retained frame has no newly admitted residual-
                            # candidate case. Check its old gate, not a rerun.
                            self.assertEqual(no_accepted_carrier(row['carrier'], physical),
                                             physical == {'kind': 'rejection', 'value': 'absent'})
                        if row['verdict'] != 'INADMISSIBLE':
                            self.assertEqual(physical, {'kind': 'rejection', 'value': 'absent'})
                            expected = 'SATISFIED' if observed['followup'] == physical else 'INCONSISTENT'
                            self.assertEqual(row['verdict'], expected)
                self.assertEqual(count, 1350)
            execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()

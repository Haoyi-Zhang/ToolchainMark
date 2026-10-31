"""Current adapter on owned benign fixtures, never unlicensed upstream code."""
import argparse
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("external_adapter_owned_test",
    ROOT / "external-transfer/run_external_transfer.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
consumer_spec = importlib.util.spec_from_file_location('external_output_consumer',
    ROOT / 'external-transfer/verify_external_transfer.py')
consumer = importlib.util.module_from_spec(consumer_spec)
consumer_spec.loader.exec_module(consumer)


class ExternalAdapterExecution(unittest.TestCase):
    def test_unavailable_launch_and_timeout_are_not_successful_exits(self):
        for error in (FileNotFoundError("owned absent tool"),
                      subprocess.TimeoutExpired(["owned"], 1), UnicodeError("owned")):
            with mock.patch.object(adapter.subprocess, "run", side_effect=error):
                result, _ = adapter.run(["owned"])
            self.assertIsNone(result.returncode)
            self.assertIn(type(error).__name__, result.stderr)
            self.assertFalse(adapter.output_observation("2929", "before", Path("."),
                                                       result.stdout, result.returncode)["available"])

    @unittest.skipUnless(shutil.which("gcc") and shutil.which("clang"), "requires Linux GCC/Clang")
    def test_current_main_preserves_invalid_interventions_with_real_compilers(self):
        with tempfile.TemporaryDirectory(prefix="owned-adapter-") as temp:
            root = Path(temp)
            sources = root / "sources"
            sources.mkdir()
            fixtures = {
                "119_before.c": '#include <stdio.h>\nint main(void){FILE*f=fopen("nr_before.txt","w");if(!f)return 2;fputs("ok",f);return fclose(f);}\n',
                "119.c": 'int main(void){return 0;}\n',
                "2929_old.c": '#include <stdio.h>\nint main(void){puts("same");return 1;}\n',
                "2929.c": '#include <stdio.h>\nint main(void){puts("same");return 0;}\n',
                "363_old.c": 'float weighted_positive_mean(float*v,float*w,int n){(void)v;(void)w;(void)n;return 0;}\n',
                "363.c": 'float weighted_positive_mean(float*v,float*w,int n){(void)v;(void)w;(void)n;return 0;}\n',
            }
            for name, content in fixtures.items():
                (sources / name).write_text(content, encoding="utf-8")
            blobs = {name: adapter.git_blob_sha1(sources / name) for name in fixtures}
            args = argparse.Namespace(source_dir=sources, out=root / "out")
            with mock.patch.object(adapter, "EXPECTED_BLOBS", blobs), \
                 mock.patch.object(adapter, "OPTS", ["O0"]), \
                 mock.patch.object(adapter.PARSER, "parse_args", return_value=args), \
                 contextlib.redirect_stdout(io.StringIO()):
                adapter.main()
            with (args.out / "relation_verdicts.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                if row["relation"] in ("host_observation_equivalence", "compiler_optimization_stability"):
                    expected = ("SATISFIED" if row["case"] == "363" or
                        (row["case"] == "119" and row.get("variant") == "before") or
                        (row["case"] == "2929" and row.get("variant") == "watermarked")
                        else "INADMISSIBLE")
                    self.assertEqual(row["verdict"], expected, row)
            with (args.out / "execution_rows.csv").open(newline="", encoding="utf-8") as handle:
                execution = list(csv.DictReader(handle))
            for row in execution:
                invalid = (row["case"], row["variant"]) in {
                    ("119", "watermarked"), ("2929", "before")}
                self.assertEqual(row["relocation_verdict"], "INADMISSIBLE" if invalid else "SATISFIED")
                self.assertEqual(row["output_available"], str(not invalid))
            summary = json.loads((args.out / "summary.json").read_text())
            self.assertEqual(summary["observation_schema"], "available-output-v2")
            self.assertEqual(summary["runner_sha256"], adapter.sha256(Path(adapter.__file__)))
            self.assertEqual(summary["payload_recovery_verdict"], "INADMISSIBLE")
            expected_sources = {name:(blob, adapter.sha256(sources/name)) for name,blob in blobs.items()}
            checked = consumer.verify(args.out, optimizations=('O0',), source_identities=expected_sources)
            self.assertTrue(checked['observation_consistency_verified'])
            self.assertFalse(checked['execution_authenticity_verified'])
            for mutation in ('sentinel', 'missing-row', 'false-verdict', 'legacy-schema'):
                target = root / mutation
                shutil.copytree(args.out, target)
                if mutation == 'legacy-schema':
                    changed = dict(summary)
                    changed.pop('observation_schema')
                    (target / 'summary.json').write_text(json.dumps(changed), encoding='utf-8')
                else:
                    filename = 'relation_verdicts.csv' if mutation == 'false-verdict' else 'execution_rows.csv'
                    with (target/filename).open(newline='', encoding='utf-8') as handle:
                        reader = csv.DictReader(handle)
                        fields, data = reader.fieldnames, list(reader)
                    if mutation == 'missing-row':
                        data.pop()
                    elif mutation == 'sentinel':
                        row = next(r for r in data if r['output_available'] == 'False')
                        row['output_text'] = '<MISSING>'
                    else:
                        row = next(r for r in data if r['relation'] == 'host_observation_equivalence'
                                   and r['verdict'] == 'INADMISSIBLE')
                        row['verdict'] = 'SATISFIED'
                    with (target/filename).open('w', newline='', encoding='utf-8') as handle:
                        writer = csv.DictWriter(handle, fieldnames=fields)
                        writer.writeheader()
                        writer.writerows(data)
                with self.assertRaises(ValueError, msg=mutation):
                    consumer.verify(target, optimizations=('O0',), source_identities=expected_sources)


if __name__ == "__main__":
    unittest.main()

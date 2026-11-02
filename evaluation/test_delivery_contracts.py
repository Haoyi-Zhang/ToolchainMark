"""Bounded delivery regressions: no compiler, JIT or native subject execution."""
import copy
import csv
import gzip
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'scripts')]
from owned_native_tool import tool
from tosem02.study_validation import validate_rows, StudyInputError


def fixture(payload=b'owned'):
    record=tool.encode(payload,'key-alpha');names=b'\0.shstrtab\0.wmrec\0'
    table=64+len(names)+len(record)
    h=struct.pack('<16sHHIQQQIHHHHHH',b'\x7fELF\x02\x01\x01'+bytes(9),1,62,1,0,0,table,0,64,0,0,64,3,1)
    pack=lambda *x:struct.pack('<IIQQQQIIQQ',*x)
    return h+names+record+bytes(64)+pack(1,3,0,0,64,len(names),0,0,1,0)+pack(11,1,2,0,64+len(names),len(record),0,0,1,0),table


class OwnedObjectContractTests(unittest.TestCase):
    def test_complete_tiny_structure_and_typed_extract_cli(self):
        data,table=fixture()
        self.assertEqual(tool.extract(data,'key-alpha'),b'owned')
        self.assertEqual(tool.extract(fixture(b'')[0],'key-alpha'),b'')
        mutations=[(table+4,'<I',1),(table+32,'<Q',100000),(64,'B',88),
                   (table+128+48,'<Q',3),(table+128+8,'<Q',3),
                   (table+128+8,'<Q',0x802),(table+128+40,'<I',999),
                   (56,'<H',1),(65,'B',255),(table+128+24,'<Q',65)]
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'owned.obj'
            for offset,fmt,value in mutations:
                bad=bytearray(data);struct.pack_into(fmt,bad,offset,value)
                with self.subTest(offset=offset,value=value):
                    with self.assertRaises(tool.Rejected):tool.extract(bad,'key-alpha')
                    path.write_bytes(bad)
                    command=[sys.executable,'-B',str(ROOT/'owned_native_tool/tool.py'),
                             'extract','--artifact',str(path),'--key','key-alpha']
                    result=subprocess.run(command,capture_output=True,text=True)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertEqual(json.loads(result.stdout)['kind'],'rejection')
        for key,raw,kind in [('key-beta',data,'wrong-key'),
                             ('key-alpha',data[:64+17]+b'','malformed')]:
            with self.assertRaises(tool.Rejected) as caught:tool.extract(raw,key)
            self.assertEqual(caught.exception.kind,kind)
        record=bytearray(tool.encode(b'owned','key-alpha'));record[-1]^=1
        with self.assertRaises(tool.Rejected) as caught:tool.decode(record,'key-alpha')
        self.assertEqual(caught.exception.kind,'checksum')


class MatrixInputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=list(csv.DictReader(io.StringIO(gzip.decompress(
            (ROOT/'results/current-native/first.csv.gz').read_bytes()).decode('utf-8'))))

    def test_actual_cli_rejects_schema_and_timing_mutations(self):
        variants=[('string-false','admission_json','{"subject_exists":"False","isolated_workspace":true}'),
                  ('number','admission_json','{"subject_exists":1,"isolated_workspace":true}'),
                  ('null','admission_json','{"subject_exists":null,"isolated_workspace":true}'),
                  ('missing','admission_json','{}'),('array','observations_json','[]'),
                  ('bad-payload','observations_json','{"extraction":{"kind":"payload","value":5}}'),
                  ('bad-kind','observations_json','{"extraction":{"kind":"mystery","value":"00"}}'),
                  ('float-overflow','observations_json','{"extra":1e999}'),
                  ('duplicate-key','admission_json','{"subject_exists":true,"subject_exists":false}'),
                  ('exposed','exposed','not-a-boolean')]
        variants += [(str(value),'duration_seconds',str(value)) for value in ('nan','inf','-inf',0,-1)]
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)
            for label,field,value in variants:
                for rerun in (False,True):
                    rows=[dict(r) for r in self.rows];rows[0][field]=value
                    path=base/'input.csv'
                    with path.open('w',newline='',encoding='utf-8') as f:
                        writer=csv.DictWriter(f,fieldnames=self.rows[0]);writer.writeheader();writer.writerows(rows)
                    out=base/(label+str(rerun))
                    cmd=[sys.executable,*(['-O'] if not __debug__ else []),'-B',str(ROOT/'scripts/derive_admission_study.py'),
                         '--matrix',str(path),'--mutants',str(ROOT/'specs/mutants.json'),'--out',str(out)]
                    if rerun:cmd+=['--rerun',str(path)]
                    result=subprocess.run(cmd,capture_output=True,text=True)
                    with self.subTest(label=label,rerun=rerun):
                        self.assertNotEqual(result.returncode,0,result.stdout)
                        self.assertEqual(json.loads((out/'scientific_checks.json').read_text())['verdict'],'FAIL')

    def test_protocol_required_facts_and_both_inputs(self):
        row=copy.deepcopy(next(r for r in self.rows if r['relation_id']=='MR10' and r['verdict']=='SATISFIED'))
        facts=json.loads(row['admission_json'])
        for key in ('nonchecksum_material_preserved','subject_exists'):
            bad=copy.deepcopy(row);changed=dict(facts);changed.pop(key);bad['admission_json']=json.dumps(changed)
            with self.assertRaises(StudyInputError):validate_rows([bad],'evidence-gated-v2-checksum-locality')
        valid=copy.deepcopy(self.rows[0]);validate_rows([valid],'evidence-gated-v2-checksum-locality')
        stopped=dict(valid,verdict='INADMISSIBLE',exposed='False',
                     admission_json='{"subject_exists":false}',observations_json='{}',reason='subject_exists')
        validate_rows([stopped],'evidence-gated-v2-checksum-locality')


class PaperBuildPreflightTests(unittest.TestCase):
    def test_missing_plotting_dependency_precedes_all_writes(self):
        build=(ROOT.parent/'paper/build.sh').read_text(encoding='utf-8')
        block=build.split("<<'PYDEPEND'\n",1)[1].split('\nPYDEPEND',1)[0]
        self.assertLess(build.index("<<'PYDEPEND'"),build.index('python3 generate_adapter_surface.py'))
        self.assertLess(build.index('== --check-only'),build.index('python3 generate_adapter_surface.py'))
        with patch('importlib.util.find_spec',return_value=None),self.assertRaisesRegex(SystemExit,'requirements.txt'):
            exec(compile(block,'build-dependency-preflight','exec'),{})
        with patch('importlib.util.find_spec',return_value=object()):
            exec(compile(block,'build-dependency-preflight','exec'),{})

    def test_owned_derivation_output_guards_precede_helpers(self):
        import derive_owned_native as d
        with tempfile.TemporaryDirectory() as temporary:
            existing=Path(temporary)/'existing';existing.mkdir()
            for extra in ([],['--out',str(existing)],['--out',str(ROOT/'unsafe-new-output')]):
                with self.subTest(extra=extra),patch.object(sys,'argv',
                        ['derive_owned_native','--run','never-opened',*extra]),\
                        patch.object(d,'derive',side_effect=AssertionError('scientific helper reached')):
                    with self.assertRaises(SystemExit):d.main()


class InstalledWheelContractTests(unittest.TestCase):
    def test_explicit_checkout_dispatch_binds_python_source_without_execution(self):
        from tosem02 import cli
        with patch.object(sys,'argv',['tosem02','run','--artifact-root',str(ROOT),'--out','owned-never-run.csv']),\
                patch.object(cli.subprocess,'run') as launch:
            cli.main()
        self.assertEqual(launch.call_count,1)
        self.assertTrue(launch.call_args.kwargs['env']['PYTHONPATH'].startswith(str(ROOT/'src')+os.pathsep))

    def test_isolated_wheel_resources_and_explicit_checkout_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp=Path(temporary);source=temp/'source';source.mkdir()
            for name in ('pyproject.toml','setup.py','MANIFEST.in','LICENSE'):shutil.copyfile(ROOT/name,source/name)
            shutil.copytree(ROOT/'src',source/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            shutil.copytree(ROOT/'specs',source/'specs')
            result=subprocess.run([sys.executable,'-B','-c',
                "import setuptools.build_meta as b; b.build_wheel('dist')"],cwd=source,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            import zipfile
            installed=temp/'installed'
            with zipfile.ZipFile(next((source/'dist').glob('*.whl'))) as archive:
                names=archive.namelist();archive.extractall(installed)
            self.assertFalse(any('/results/' in n or '/hosts/' in n for n in names))
            self.assertEqual(sum('/data/' in n for n in names),3)
            env=dict(os.environ,PYTHONPATH=str(installed),PYTHONDONTWRITEBYTECODE='1')
            def run(*args):return subprocess.run([sys.executable,'-B',*args],cwd=temp,env=env,capture_output=True,text=True)
            api=run('-c','from tosem02.catalog import load_relations,load_mutants;from tosem02.evidence_catalog import load;print(len(load_relations()),len(load_mutants()),len(load()))')
            self.assertEqual(api.returncode,0,api.stderr);self.assertEqual(api.stdout.strip(),'14 24 14')
            catalog=run('-m','tosem02.cli','catalog')
            self.assertEqual(catalog.returncode,0,catalog.stderr);self.assertEqual(len(json.loads(catalog.stdout)['relations']),14)
            self.assertEqual(run('-m','tosem02.cli','--help').returncode,0)
            for command in ('run','robustness','derive','recheck'):
                args=['-m','tosem02.cli',command]
                if command!='recheck':args+=['--out',str(temp/'unused')]
                denied=run(*args)
                self.assertNotEqual(denied.returncode,0);self.assertIn('--artifact-root',denied.stderr)
                self.assertNotIn('FileNotFoundError',denied.stderr)
            # A valid explicit checkout reaches its data-only output guard,
            # rather than guessing resource paths under site-packages.
            existing=temp/'exists';existing.mkdir()
            result=run('-m','tosem02.cli','derive','--artifact-root',str(ROOT),'--out',str(existing))
            self.assertNotEqual(result.returncode,0);self.assertIn('existing',result.stderr)


if __name__=='__main__':unittest.main()

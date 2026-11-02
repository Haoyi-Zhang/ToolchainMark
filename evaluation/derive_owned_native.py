"""Read-only scientific derivation of the separate owned native activity.

No compiler/JIT or upstream tool is executed. --paper explicitly regenerates
only owned-native.tex, not any retained Linux table or historical plot.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import sys

# The documented script entry must work without installing this owned tool.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from run_owned_native import plan
from owned_native_tool import tool
from owned_record_summary import require, validate_summary

ROOT=Path(__file__).resolve().parents[1]
# Exact registered producer identities for the retained owned activity. A later
# checkout is not evidence that these old rows were measured with later code.
RETAINED_SOURCE_VERSIONS={
    'src/tosem02/admission.py':'632d95967a2680cd2d2179f56965268897ea2c248b11ecade35605ac1c28ee27',
    'src/tosem02/integrity.py':'485762ac4f281815dd69e98f87ac2d217f20138351c4fdbed5764e981d410aa2',
    'src/tosem02/record.py':'1daf9519b91f24ccc11262cf236cacec79447e75e2cc06c9b8d0265c332f909e',
    'owned_native_tool/tool.py':'8b6229cb1e213d51064cb6997a700c797b577232bd696c712f70123ea280061f',
    'owned_native_tool/adapter.py':'1518782a0863693838fc21ca62952b944973fed8f006b744bebf596b62ba401b',
    'evaluation/run_owned_native.py':'9cbbec608936647a972b9e5e3108fa32f1d5d8c174c002189713a91f9d9f48e7',
}
RETAINED_PREIMAGES={
    'src/tosem02/admission.py':'results/native-execution/source-snapshot/src/tosem02/admission.py',
    'owned_native_tool/tool.py':'results/owned-source-preimages/owned_native_tool/tool.py',
}

def verify_recorded_sources(summary, source_root=ROOT, preserved_root=None):
    expected=summary.get('source_versions')
    require(type(expected) is dict and expected==RETAINED_SOURCE_VERSIONS,
            'owned registered source identities differ')
    current=[];preserved=[]
    for name,digest in RETAINED_SOURCE_VERSIONS.items():
        def matches(path):
            return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest
        if matches(source_root/name):current.append(name)
        else:
            captured = (preserved_root/name if preserved_root is not None else
                        source_root/RETAINED_PREIMAGES[name] if name in RETAINED_PREIMAGES else None)
            require(captured is not None and matches(captured),'owned historical source bytes differ: '+name)
            preserved.append(name)
    return dict(recorded_sources=len(expected),current_source_files_used=current,
                preserved_source_files_used=preserved)


def derive(root):
    summary=json.loads((root/'summary.json').read_text())
    verify_recorded_sources(summary)
    packed=(root/'raw.jsonl.gz').read_bytes()
    unpacked=gzip.decompress(packed)
    rows=[json.loads(line) for line in unpacked.splitlines()]
    computed=validate_summary(rows,summary)
    expected=[list(x) for x in plan(summary['small'])]
    require([row['identity'] for row in rows]==expected,'owned identity plan differs')
    groups=defaultdict(Counter)
    limited=Counter()
    for row in rows:
        family,variant,profile,cohort,relation,intervention,bypass=row['identity']
        if row['verdict']!='INADMISSIBLE': require(all(row['admission'].values()),'owned admission differs')
        for build in row['builds']:
            data=bytes.fromhex(build['object_hex'])
            require(hashlib.sha256(data).hexdigest()==build['object_sha256'],'owned object bytes differ')
            tool.elf_sections(data)
            require(build['native_outputs']==build['reference_outputs']==[
                tool.expected(family,variant,x) for x in build['native_inputs']], 'owned output/reference differs')
            if build['marked']:
                require(tool.extract(data,build['key']).hex()==build['payload_hex'],'owned payload differs')
        if cohort=='integrity-challenge':
            groups[intervention][row['verdict']]+=1
            # Same recorded information, but deliberately omit final identity
            # when reproducing the locality-only gate as an ablation. This is
            # not a fresh execution of the retained v2 Linux program.
            observation=row['observations']
            facts=observation.get('integrity_intervention',{})
            admitted=(observation.get('followup_carrier')=={'kind':'rejection','value':'checksum'}
                      and bool(facts) and all(facts.values()))
            if not admitted: verdict='INADMISSIBLE'
            else:
                require('followup' in observation,'owned follow-up absent')
                verdict='SATISFIED' if observation['followup']=={'kind':'rejection','value':'checksum'} else 'INCONSISTENT'
            limited[verdict]+=1
    direct=[r for r in rows if r['direct_integrity_verdict'] is not None]
    result={'source_summary_sha256':hashlib.sha256((root/'summary.json').read_bytes()).hexdigest(),
            'raw_sha256':hashlib.sha256(packed).hexdigest(),'raw_gzip_bytes':len(packed),
            'raw_uncompressed_bytes':len(unpacked),'raw_rows':len(rows),
            'integrity_interventions':{k:dict(v) for k,v in groups.items()},
            'locality_only_postcondition_ablation':dict(limited),
            'same_information_direct_checks':len(direct),
            'same_information_direct_disagreements':sum(r['verdict']!=r['direct_integrity_verdict'] for r in direct),
            'case_wall_median_seconds':statistics.median(r['case_seconds'] for r in rows),
            'case_wall_max_seconds':max(r['case_seconds'] for r in rows),
            'case_wall_sum_seconds':computed['case_wall_sum'],'case_cpu_sum_seconds':computed['case_cpu_sum'],
            'activity_wall_seconds':summary['activity_wall_seconds'],
            'direct_projection_sum_seconds':sum(r['direct_projection_seconds'] for r in rows),
            'scope':'Case cost includes acquisition/build/object execution/file I/O/direct projection/full case cleanup; direct projection alone excludes shared acquisition. Byte totals are experiment artifacts, not runtime memory/deployment lifecycle. Ablation is derived, not a rerun of old Linux code.'}
    return summary,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--check-sources',action='store_true',help='verify the six registered historical source byte identities only')
    parser.add_argument('--paper',type=Path)
    args=parser.parse_args()
    if args.check_sources:
        if args.out is not None or args.paper is not None:parser.error('--check-sources does not write outputs')
        summary=json.loads((args.run/'summary.json').read_text(encoding='utf-8'))
        print(json.dumps(verify_recorded_sources(summary),indent=2));return
    if args.out is None:parser.error('--out is required for derivation')
    if args.out.resolve().is_relative_to(ROOT.parent.resolve()) or args.out.resolve().is_relative_to(args.run.resolve()):
        parser.error('--out must be a new external derivation directory')
    if args.out.exists() or args.out.is_symlink():raise SystemExit('Refusing existing derivation output')
    summary,result=derive(args.run)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/'derived.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if args.paper is not None:
        require(not summary['small'],'Paper table must use the full frozen cohort')
        clean=summary['cohorts']['clean-workflow']
        challenge=summary['cohorts']['integrity-challenge']
        text=('\\begin{table}[t]\n\\caption{Separate owned native object activity.}\\label{tab:owned-native}\n\\small\n'
              '\\begin{tabularx}{\\textwidth}{@{}X r r r r@{}}\\toprule\nCohort & Attempted & Satisfied & Inconsistent & Inadmissible \\\\\n\\midrule\n'
              f"Clean workflow & {sum(clean.values())} & {clean.get('SATISFIED',0)} & {clean.get('INCONSISTENT',0)} & {clean.get('INADMISSIBLE',0)} \\\\\n"
              f"Integrity controls & {sum(challenge.values())} & {challenge.get('SATISFIED',0)} & {challenge.get('INCONSISTENT',0)} & {challenge.get('INADMISSIBLE',0)} \\\\\n"
              '\\bottomrule\\end{tabularx}\n\\end{table}\n')
        (args.paper/'generated/owned-native.tex').write_text(text,encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

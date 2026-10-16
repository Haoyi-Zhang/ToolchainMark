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

from run_owned_native import plan, versions
from owned_native_tool import tool
from owned_record_summary import require, validate_summary


def derive(root):
    summary=json.loads((root/'summary.json').read_text())
    require(summary['source_versions']==versions(),'owned source binding differs')
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
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--paper',type=Path)
    args=parser.parse_args()
    if args.out.exists():raise SystemExit('Refusing existing derivation output')
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

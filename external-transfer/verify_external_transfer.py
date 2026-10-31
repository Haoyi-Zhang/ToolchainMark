"""Read-only consumer for new available-output-v2 records, not old rerun evidence.

Ordinary output/exit/stability arithmetic is rederived without importing the
runner. No acquisition, compiler, watermark tool or host program is executed.
Matching source identities establishes consistency with the supplied manifest,
not execution authenticity or an upstream semantic-equivalence contract.
"""
import argparse
import csv
import hashlib
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAIRS = {'119': ('119_before.c', '119.c'), '2929': ('2929_old.c', '2929.c'),
         '363': ('363_old.c', '363.c')}
MODES = ('native', 'compatibility')
OPTS = ('O0', 'O1', 'O2', 'O3', 'Os')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def rows(path):
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def boolean(value):
    require(value in ('True', 'False'), 'non-Boolean observation flag')
    return value == 'True'


def returncode(value):
    require(type(value) is str and (value == '' or (len(value) <= 11 and str(int(value)) == value)),
            'return code must be an integer exit status or unavailable')


def identities():
    return {Path(r['upstream_path']).name: (r['github_blob_sha1'], r['sha256'])
            for r in rows(ROOT / 'acquisition_manifest.csv')}


def verify(directory, *, compilers=('gcc', 'clang'), optimizations=OPTS, source_identities=None):
    directory = Path(directory)
    summary = json.loads((directory / 'summary.json').read_text(encoding='utf-8'))
    require(summary.get('observation_schema') == 'available-output-v2',
            'new observation schema required; retained legacy rows are not a current rerun')
    require(type(summary.get('runner_sha256')) is str and len(summary['runner_sha256']) == 64 and
            all(c in '0123456789abcdef' for c in summary['runner_sha256']), 'runner digest format')
    require(summary['compilers'] == list(compilers) and summary['optimization_levels'] == list(optimizations)
            and summary['modes'] == list(MODES), 'declared plan differs from expected plan')
    source_identities = identities() if source_identities is None else source_identities
    require(set(source_identities) == {name for pair in PAIRS.values() for name in pair}, 'source frame')
    execution = rows(directory / 'execution_rows.csv')
    indexed = {}
    for row in execution:
        key = tuple(row[k] for k in ('mode', 'case', 'compiler', 'optimization', 'variant'))
        require(key not in indexed, 'duplicate execution row')
        indexed[key] = row
        mode, case, compiler, opt, variant = key
        require(case in PAIRS and variant in ('before', 'watermarked'), 'unknown source pair')
        name = PAIRS[case][variant == 'watermarked']
        require(row['source_label'] == name and
                (row['source_git_blob_sha1'], row['source_sha256']) == source_identities[name], 'source identity')
        require(boolean(row['compatibility_header_applied']) == (mode == 'compatibility'), 'compatibility intervention')
        available = boolean(row['output_available'])
        relocated = boolean(row['relocate_output_available'])
        for field in ('compile_rc', 'run_rc', 'relocate_rc'):
            returncode(row[field])
        if row['compile_rc'] != '0':
            require(row['run_rc'] == row['relocate_rc'] == '' and not available and not relocated,
                    'execution claimed after unavailable build')
        for prefix, observed, rc in (('', available, row['run_rc']),
                                      ('relocate_', relocated, row['relocate_rc'])):
            value, digest = row[prefix + 'output_text'], row[prefix + 'output_sha256']
            if observed:
                require(row['compile_rc'] == rc == '0', 'output without successful execution')
                require(digest == hashlib.sha256(value.encode('utf-8')).hexdigest(), 'observed text/hash mismatch')
                require(row[prefix+'output_unavailable_reason'] == '', 'available observation has failure reason')
            else:
                require(value == digest == '' and bool(row[prefix+'output_unavailable_reason']),
                        'unavailable output cannot carry a matching sentinel/value')
        admitted = row['compile_rc'] == row['run_rc'] == row['relocate_rc'] == '0' and available and relocated
        verdict = ('INADMISSIBLE' if not admitted else
                   'SATISFIED' if row['output_text'] == row['relocate_output_text'] else 'INCONSISTENT')
        require(row['relocation_verdict'] == verdict and boolean(row['relocation_match']) == (verdict == 'SATISFIED'),
                'relocation verdict')
    plan = set(product(MODES, PAIRS, compilers, optimizations, ('before', 'watermarked')))
    require(set(indexed) == plan, 'incomplete execution frame')

    expected = {}
    for mode, case in product(MODES, PAIRS):
        for compiler, opt in product(compilers, optimizations):
            pair = [indexed[mode, case, compiler, opt, v] for v in ('before', 'watermarked')]
            successful = all(r['compile_rc'] == r['run_rc'] == '0' for r in pair)
            observed = successful and all(boolean(r['output_available']) for r in pair)
            expected[mode, case, 'execution_only_baseline', compiler, opt, ''] = 'SATISFIED' if successful else 'INADMISSIBLE'
            expected[mode, case, 'host_observation_equivalence', compiler, opt, ''] = (
                'INADMISSIBLE' if not observed else 'SATISFIED' if pair[0]['output_text'] == pair[1]['output_text'] else 'INCONSISTENT')
        for variant in ('before', 'watermarked'):
            selected = [indexed[mode, case, c, o, variant] for c, o in product(compilers, optimizations)]
            observed = all(r['compile_rc'] == r['run_rc'] == '0' and boolean(r['output_available']) for r in selected)
            expected[mode, case, 'compiler_optimization_stability', 'all', 'all', variant] = (
                'INADMISSIBLE' if not observed else 'SATISFIED' if len({r['output_text'] for r in selected}) == 1 else 'INCONSISTENT')
        expected[mode, case, 'payload_recovery', 'all', 'all', ''] = 'INADMISSIBLE'
    relations = rows(directory / 'relation_verdicts.csv')
    actual = {}
    for row in relations:
        key = tuple(row.get(k, '') for k in ('mode', 'case', 'relation', 'compiler', 'optimization', 'variant'))
        require(key not in actual, 'duplicate relation row')
        actual[key] = row['verdict']
        mode, case, relation, compiler, opt, variant = key
        if relation == 'host_observation_equivalence' and key in expected:
            pair = [indexed[mode, case, compiler, opt, v] for v in ('before', 'watermarked')]
            require((row['before_sha256'], row['after_sha256']) ==
                    tuple(r['output_sha256'] for r in pair), 'relation output identities')
        if relation == 'compiler_optimization_stability' and key in expected:
            selected = [indexed[mode, case, c, o, variant] for c, o in product(compilers, optimizations)]
            distinct = '' if expected[key] == 'INADMISSIBLE' else str(len({r['output_text'] for r in selected}))
            require(row['distinct_outputs'] == distinct, 'stability distinct-output count')
    require(actual == expected, 'relation verdicts do not follow observed outputs/exits')

    sanitizers = rows(directory / 'sanitizer_rows.csv')
    san_keys = [(r['case'], r['compiler'], r['variant']) for r in sanitizers]
    require(len(san_keys) == len(set(san_keys)) and set(san_keys) == set(product(PAIRS, compilers, ('before', 'watermarked'))),
            'sanitizer frame')
    for row in sanitizers:
        returncode(row['compile_rc'])
        returncode(row['run_rc'])
        require(row['mode'] == 'compatibility' and (row['compile_rc'] == '0' or row['run_rc'] == ''),
                'sanitizer construction mismatch')
        clean = row['compile_rc'] == row['run_rc'] == '0' and 'ERROR:' not in row['run_stderr'] and 'runtime error:' not in row['run_stderr']
        require(boolean(row['sanitizer_clean']) == clean, 'sanitizer outcome arithmetic')
    compat_exit = [v for k,v in expected.items() if k[0] == 'compatibility' and k[2] == 'execution_only_baseline']
    compat_host = [v for k,v in expected.items() if k[0] == 'compatibility' and k[2] == 'host_observation_equivalence']
    native_host = [v for k,v in expected.items() if k[0] == 'native' and k[2] == 'host_observation_equivalence']
    totals = dict(source_pairs=3, source_files=6, source_identity_checks=6, source_identity_mismatches=0,
        execution_rows=len(execution), native_execution_rows=len(execution)//2,
        compatibility_execution_rows=len(execution)//2,
        native_semantic_checks=len(native_host), native_semantic_inadmissible=native_host.count('INADMISSIBLE'),
        compatibility_exit_only_checks=len(compat_exit), compatibility_exit_only_satisfied=compat_exit.count('SATISFIED'),
        compatibility_host_semantic_checks=len(compat_host), compatibility_host_semantic_satisfied=compat_host.count('SATISFIED'),
        compatibility_host_semantic_inconsistent=compat_host.count('INCONSISTENT'),
        relocation_attempts=len(execution), relocation_admitted=sum(r['relocation_verdict'] != 'INADMISSIBLE' for r in execution),
        relocation_inadmissible=sum(r['relocation_verdict'] == 'INADMISSIBLE' for r in execution),
        relocation_satisfied=sum(r['relocation_verdict'] == 'SATISFIED' for r in execution),
        sanitizer_checks=len(sanitizers), sanitizer_clean=sum(boolean(r['sanitizer_clean']) for r in sanitizers))
    case_rows = rows(directory / 'case_summary.csv')
    require(len(case_rows) == len(PAIRS) and {r['case'] for r in case_rows} == set(PAIRS), 'case-summary frame')
    totals.update(compatibility_pair_exit_only_pass=0, compatibility_pair_host_semantic_pass=0,
                  compatibility_pair_host_semantic_inconsistent=0)
    for case in PAIRS:
        exit_values = [v for k,v in expected.items() if k[0] == 'compatibility' and k[1] == case and k[2] == 'execution_only_baseline']
        host_values = [v for k,v in expected.items() if k[0] == 'compatibility' and k[1] == case and k[2] == 'host_observation_equivalence']
        native_values = [v for k,v in expected.items() if k[0] == 'native' and k[1] == case and k[2] == 'host_observation_equivalence']
        case_counts = dict(native_admitted_checks=sum(v != 'INADMISSIBLE' for v in native_values),
            native_inadmissible_checks=native_values.count('INADMISSIBLE'),
            compatibility_exit_only_satisfied=exit_values.count('SATISFIED'),
            compatibility_host_satisfied=host_values.count('SATISFIED'),
            compatibility_host_inconsistent=host_values.count('INCONSISTENT'), compatibility_configs=len(host_values))
        case_row = next(r for r in case_rows if r['case'] == case)
        require(all(case_row[k] == str(v) for k,v in case_counts.items()), 'case summary/raw mismatch')
        totals['compatibility_pair_exit_only_pass'] += all(v == 'SATISFIED' for v in exit_values)
        totals['compatibility_pair_host_semantic_pass'] += all(v == 'SATISFIED' for v in host_values)
        totals['compatibility_pair_host_semantic_inconsistent'] += 'INCONSISTENT' in host_values
    for name, value in totals.items():
        require(type(summary[name]) is int and summary[name] == value, 'summary/raw mismatch: '+name)
    require(summary['payload_recovery_verdict'] == 'INADMISSIBLE', 'missing extraction interface')
    return dict(execution_rows=len(execution), relation_rows=len(relations),
        observation_consistency_verified=True, source_identities_match_supplied_manifest=True,
        execution_authenticity_verified=False, watermark_semantic_equivalence_verified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), sort_keys=True))

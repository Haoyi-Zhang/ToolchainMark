from __future__ import annotations

import argparse
import gzip
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

from .catalog import checkout_root, load_relations, load_mutants
from .recheck import recheck


def checkout_environment(root: Path) -> dict:
    """Explicit checkout operations execute that checkout's Python analysis."""
    return dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                PYTHONPATH=str(root/'src')+os.pathsep+os.environ.get('PYTHONPATH',''))


def environment() -> dict:
    def first(command: list[str]) -> str:
        proc = subprocess.run(command, text=True, capture_output=True)
        return (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else ''
    return {
        'python': sys.version.split()[0], 'platform': platform.platform(),
        'gcc': first(['gcc', '--version']), 'clang': first(['clang', '--version']),
        'objcopy': first(['objcopy', '--version']), 'nm': first(['nm', '--version']), 'strip': first(['strip', '--version']),
        'executables': {name: f'PATH:{name}' for name in ['python3', 'gcc', 'clang', 'objcopy', 'nm', 'strip']},
        'path_recording_policy': 'Command names are recorded; machine-local absolute executable paths are intentionally omitted.',
    }


def derive_current_native(root: Path, output: Path) -> None:
    """Rederive canonical current records into a new, external directory.

    Published gzip bytes are unpacked only temporarily. Historical data and
    paper inputs are read-only; no table generator is part of this command.
    """
    output = output.resolve()
    if output.exists():
        raise SystemExit('Refusing to overwrite an existing derivation output')
    if output.is_relative_to(root.parent.resolve()):
        raise SystemExit('Derivation output must be outside the supplied project')
    current = root / 'results/current-native'
    with tempfile.TemporaryDirectory(prefix='tosem02-current-derive-') as temporary:
        temporary = Path(temporary)
        for name in ('first', 'second'):
            data = gzip.decompress((current / (name + '.csv.gz')).read_bytes())
            (temporary / (name + '.csv')).write_bytes(data)
        # Reserve the new destination; failed derivations retain their outputs.
        output.mkdir(parents=True, exist_ok=False)
        subprocess.run([
            sys.executable, str(root / 'scripts/derive_admission_study.py'),
            '--matrix', str(temporary / 'first.csv'),
            '--rerun', str(temporary / 'second.csv'),
            '--mutants', str(root / 'specs/mutants.json'),
            '--legacy', str(root / 'results/raw/robustness_matrix.csv'),
            '--out', str(output),
        ], check=True,env=checkout_environment(root))


def main() -> None:
    parser=argparse.ArgumentParser(description='Evidence-gated watermark validation; retained Boolean evidence is historical')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('catalog',help='print the packaged relation/operator catalogs; no checkout needed')
    for name in ('run','robustness'):
        p=sub.add_parser(name,help='execute the current evidence-gated protocol into a NEW file')
        p.add_argument('--out','--output',dest='out',type=Path,required=True)
        p.add_argument('--workers',type=int,default=4)
        p.add_argument('--design-only',action='store_true')
        p.add_argument('--clean-only',action='store_true')
        p.add_argument('--artifact-root',type=Path,help='artifact checkout, required outside a source checkout')
    p=sub.add_parser('derive',help='rederive results/current-native/first.csv.gz and second.csv.gz; never write paper inputs')
    p.add_argument('--out','--output',dest='out',type=Path,required=True,
                   help='NEW derivation directory outside the supplied project')
    p.add_argument('--artifact-root',type=Path,help='artifact checkout containing retained records')
    p=sub.add_parser('recheck',help='check a two-directory publication checkout; not bundled wheel data')
    p.add_argument('--artifact-root',type=Path,help='artifact checkout with sibling paper directory')
    args=parser.parse_args()
    if args.command=='catalog':
        print(json.dumps({'relations':load_relations(),'mutants':load_mutants()},indent=2));return
    try:
        root=checkout_root(args.artifact_root)
    except ValueError as error:
        parser.error(str(error))
    if args.command in ('run','robustness'):
        cmd=[sys.executable,str(root/'scripts/run_admission_study.py'),'--out',str(args.out),'--workers',str(args.workers)]
        if args.design_only:cmd.append('--design-only')
        if args.clean_only:cmd.append('--clean-only')
        subprocess.run(cmd,check=True,env=checkout_environment(root));return
    if args.command=='derive':
        derive_current_native(root,args.out);return
    report=recheck(root); print(json.dumps(report,indent=2))

if __name__=='__main__':main()

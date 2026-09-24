#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

EXPECTED_ROOT_ENTRIES = {'paper', 'artifact', 'research-plan.md', 'CURRENT-STATE.md'}
FORBIDDEN_NAMES = {'.git', '.DS_Store', '__pycache__'}
FORBIDDEN_SUFFIXES = {'.pyc', '.pyo', '.swp', '.tmp', '~'}
PRIVATE_PATH_MARKERS = (
    '/' + 'mnt/data',
    '/' + 'home/oai',
    'sand' + 'box:',
    'file_' + '000000',
    'tosem02_' + 'final_build',
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / 'artifact/audit/project_manifest.csv'
    checks: dict[str, object] = {}

    checks['root_name'] = root.name == 'TOSEM-02'
    checks['root_entries_exact'] = {p.name for p in root.iterdir()} == EXPECTED_ROOT_ENTRIES
    checks['manifest_present'] = manifest_path.is_file()
    if not checks['manifest_present']:
        print(json.dumps({'verdict': 'FAIL', 'checks': checks}, indent=2))
        return 1

    with manifest_path.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    expected_paths = {row['path'] for row in rows}
    actual_paths = {
        p.relative_to(root).as_posix()
        for p in root.rglob('*')
        if p.is_file() and p != manifest_path
    }
    checks['manifest_paths_unique'] = len(rows) == len(expected_paths)
    checks['manifest_covers_all_files_except_self'] = expected_paths == actual_paths

    row_results = {}
    for row in rows:
        rel = Path(row['path'])
        safe = not rel.is_absolute() and '..' not in rel.parts
        path = root / rel
        row_results[row['path']] = (
            safe
            and path.is_file()
            and sha256(path) == row['sha256']
            and path.stat().st_size == int(row['bytes'])
            and stat.S_IMODE(path.stat().st_mode) == int(row['mode'], 8)
        )
    checks['manifest_hash_size_mode_rows'] = all(row_results.values())

    all_nodes = list(root.rglob('*'))
    checks['no_symlinks'] = not any(p.is_symlink() for p in all_nodes)
    checks['no_shared_hardlinks'] = not any(p.is_file() and p.stat().st_nlink != 1 for p in all_nodes)
    checks['no_forbidden_names'] = not any(
        p.name in FORBIDDEN_NAMES or any(p.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)
        for p in all_nodes
    )

    private_hits = []
    for path in [p for p in all_nodes if p.is_file()]:
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for marker in PRIVATE_PATH_MARKERS:
            if marker in text:
                private_hits.append({'path': path.relative_to(root).as_posix(), 'marker': marker})
    checks['no_private_runtime_paths'] = not private_hits

    verdict = 'PASS' if all(value is True for value in checks.values()) else 'FAIL'
    print(json.dumps({
        'schema_version': '1.0',
        'root': root.name,
        'manifest_rows': len(rows),
        'checks': checks,
        'failed_manifest_rows': [path for path, ok in row_results.items() if not ok],
        'private_runtime_path_hits': private_hits,
        'verdict': verdict,
    }, indent=2))
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())

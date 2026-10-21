"""Generate only the current two-directory delivery inventory, not run evidence."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/'scripts/verify_package.py'
SPEC=importlib.util.spec_from_file_location('delivery_package_checker',SOURCE)
CHECKER=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def generate(root: Path) -> dict:
    root=CHECKER.filesystem_root(root)
    if {p.name for p in root.iterdir()} != {'paper','artifact'}:
        raise ValueError('Delivery root must contain only paper and artifact')
    files,links,shared=CHECKER.inventory(root)
    if links or shared:
        raise ValueError('Delivery inventory refuses links and shared hardlinks')
    output=root/CHECKER.MANIFEST
    rows=[]
    for path in files:
        if path==output:
            continue
        relative=path.relative_to(root).as_posix()
        if not CHECKER.safe_manifest_path(relative) or CHECKER.file_role(relative) not in {
                'ordinary','scientific-container','scientific-log'}:
            raise ValueError('Delivery inventory refuses invalid file roles: '+relative)
        rows.append(dict(path=relative,sha256=CHECKER.sha256(path),bytes=path.stat().st_size,
                         mode=CHECKER.publication_mode(relative)))
    buffer=io.StringIO(newline='')
    writer=csv.DictWriter(buffer,fieldnames=['path','sha256','bytes','mode'])
    writer.writeheader()
    # Retain the delivered Windows path ordering on every supported host.
    writer.writerows(sorted(rows,key=lambda row:tuple(part.casefold() for part in Path(row['path']).parts)))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(buffer.getvalue(),encoding='utf-8',newline='')
    return dict(scope='current-delivery-inventory',manifest=CHECKER.MANIFEST,rows=len(rows),
                sha256=CHECKER.sha256(output),certifies_native_execution=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_root',nargs='?',type=Path,default=SOURCE.parents[2])
    args=parser.parse_args()
    try:
        report=generate(args.project_root)
    except (OSError,ValueError) as error:
        parser.exit(1,str(error)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()

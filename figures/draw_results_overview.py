"""Draw fixed-suite and holdout sensitivity on comparable axes."""
import argparse
import csv
from fractions import Fraction
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from plot_font import PDF_METADATA

HERE = Path(__file__).resolve().parent
LABELS = {'artifact binding': 'Binding', 'authentication': 'Key', 'configuration': 'Build request',
          'embedding': 'Embedding', 'extraction': 'Extraction', 'false positive': 'Absent carrier',
          'integrity': 'Integrity', 'normalization': 'Normalization', 'semantic corruption': 'Host semantics',
          'stage routing': 'Stage routing', 'state': 'State', 'transformation': 'Removal'}


def refresh_data(derived, target):
    summary = json.loads((derived/'summary.json').read_text(encoding='utf-8'))
    with (derived/'class_holdout.csv').open(encoding='utf-8', newline='') as stream:
        classes = list(csv.DictReader(stream))
    rows = []
    for label, row in zip(['Round trip', '+ host', '+ build variation', 'Full catalog'], summary['suites']):
        rows.append(['fixed', row['suite'], label, row['design_exposed'], row['design_units']])
    for row in classes:
        rows.append(['holdout', row['fault_class'], LABELS[row['fault_class']], int(row['exposed']), int(row['test_units'])])
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['panel', 'identity', 'label', 'exposed', 'planned'])
        writer.writerows(rows)


def draw(data, output):
    from toolchain_panels import results
    with data.open(encoding='utf-8',newline='') as stream:
        rows=list(csv.DictReader(stream))
    fixed=[r for r in rows if r['panel']=='fixed']
    holdout=[r for r in rows if r['panel']=='holdout']
    if [int(r['exposed']) for r in fixed]!=[21,27,33,69] or any(int(r['planned'])!=72 for r in fixed):
        raise ValueError('Retained fixed-suite counts differ.')
    if len(holdout)!=12 or sum(int(r['exposed'])==0 for r in holdout)!=5:
        raise ValueError('Retained class population differs.')
    paths=[]
    for i,(name,selected) in enumerate((('fixed',fixed),('holdout',holdout))):
        for row in selected:
            if not 0<=int(row['exposed'])<=int(row['planned']) or int(row['planned'])==0:
                raise ValueError('Invalid exposed/planned pair')
        path=output/('results-overview-'+name+'.pdf')
        results(selected,path,i)
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=HERE/'results-overview.csv')
    parser.add_argument('--out-dir', type=Path, default=HERE)
    parser.add_argument('--refresh-data', type=Path, metavar='DERIVED', help='Read retained summary/class counts; do not execute experiments.')
    args = parser.parse_args()
    if args.refresh_data:
        refresh_data(args.refresh_data, args.data)
    for path in draw(args.data, args.out_dir):
        print(path.name)


if __name__ == '__main__':
    main()

"""Fault placement and observation scopes for the external utility matrix."""
import csv
import json
from pathlib import Path
from diagram_ink import Diagram, S, T, A, G

def intervention_loci():
    d=Diagram(420,100)
    steps=((41,'Build','code'),(151,'Transform','patch'),(266,'Extract','lens'),(380,'Verdict','trace'))
    for x,label,kind in steps:
        d.mark(kind,x,54,22,S)
        d.txt(x,80,label,9.8,bold=True)
    for a,b in zip(steps,steps[1:]):
        d.wire((a[0]+15,54),(b[0]-16,54),c=S)
    for x,label in ((41,'Compiler / payload'),(151,'Utility / integrity'),(266,'Extraction / rejection')):
        d.wire((x,30),(x,40),c=A,dash=True)
        d.txt(x,16,label,9.2,color=A)
    d.txt(369,18,'At most one operator',9.5,color=G)
    return d

def utility_observations():
    path=Path(__file__).resolve().parents[1]/'results/external_transformations_observation_scopes.summary.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    with (path.parents[1]/data['source_matrix']).open(encoding='utf-8',newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==data['rows']
    assert sum(r['pass']=='True' and r['host_outputs_equal']=='True' for r in rows)==data['preservation_verified_rows']
    assert sum(r['pass']=='True' and r['expected']=='reject' and r['observed']=='reject' for r in rows)==data['rejection_only_rows']
    assert sum(r['pass']=='False' for r in rows)==data['incompatible_rows']
    groups=((85,'Preservation',data['preservation_verified_rows'],T,'Host output compared'),
            (52,'Rejection only',data['rejection_only_rows'],S,'No host comparison'),
            (19,'Incompatible',data['incompatible_rows'],A,'No supported result'))
    assert sum(g[2] for g in groups)==data['rows']
    d=Diagram(420,104)
    d.mark('array',29,52,23,S)
    d.txt(32,25,f"{data['rows']} rows",9.6,bold=True)
    d.wire((45,52),(86,52),c=G,arrow=False)
    for y,label,n,color,meaning in groups:
        d.wire((86,52),(86,y),(115,y),c=color)
        d.txt(126,y,f'{n}  {label}',9.9,ha='left',color=color,bold=True)
        d.wire((238,y),(264,y),c=color)
        d.txt(274,y,meaning,9.7,ha='left')
    return d

FIGURES={'intervention-loci':intervention_loci,'utility-observations':utility_observations}

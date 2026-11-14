"""Fault placement and observation scopes for the external utility matrix."""
import csv
import json
from pathlib import Path
from diagram_ink import Diagram, S, T, A, G

def intervention_loci():
    d=Diagram(420,100)
    for x,lab,k in ((46,'Build','code'),(146,'Transform','patch'),
                    (246,'Extract','lens'),(351,'Verdict','trace')):
        d.mark(k,x,57,19,S)
        d.txt(x,78,lab,9.4)
    for x,x2 in ((46,146),(146,246),(246,351)):
        d.wire((x+13,57),(x2-15,57),c=S)
    for x,lab in ((46,'Compiler / payload'),(146,'Utility / integrity'),(246,'Extraction / rejection')):
        d.txt(x,19,lab,8.9,color=A)
        d.wire((x,30),(x,43),c=A,dash=True)
    d.txt(351,19,'Read only',8.8,color=G)
    return d

def utility_observations():
    from matplotlib.patches import Rectangle
    path=Path(__file__).resolve().parents[1]/'results/external_transformations_observation_scopes.summary.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    with (path.parents[1]/data['source_matrix']).open(encoding='utf-8',newline='') as stream:
        rows=list(csv.DictReader(stream))
    counts=(
        sum(r['pass']=='True' and r['host_outputs_equal']=='True' for r in rows),
        sum(r['pass']=='True' and r['expected']=='reject' and r['observed']=='reject' for r in rows),
        sum(r['pass']=='False' for r in rows),
    )
    total=len(rows)
    assert total==sum(counts)==data['rows']==378
    assert counts==tuple(data[k] for k in
                         ('preservation_verified_rows','rejection_only_rows','incompatible_rows'))
    d=Diagram(420,104)
    d.txt(11,90,f'{total} utility-matrix rows',9.7,ha='left',bold=True)
    origin,end=11,373
    edge=origin
    for i,(n,c,fill,hatch) in enumerate(zip(counts,(T,S,A),('#dceee8','#e3ecf3','#f6e8dd'),('','///','...'))):
        w=(end-origin)*n/total
        d.ax.add_patch(Rectangle((edge,59),w,16,facecolor=fill,edgecolor=c,
                                 linewidth=.75,hatch=hatch,zorder=3))
        center=edge+w/2
        label_x=(95,232,330)[i]
        y=(45,45,45)[i]
        d.wire((center,57),(center,52),(label_x,52),(label_x,49),
               c=c,lw=.65,arrow=False)
        d.txt(label_x,y,f'{n} {["preservation","rejection only","incompatible"][i]}',9.3,color=c)
        d.txt(label_x,21,["Host output compared","No host comparison","No supported result"][i],
              8.8,color=G)
        edge+=w
    return d

FIGURES={'intervention-loci':intervention_loci,'utility-observations':utility_observations}

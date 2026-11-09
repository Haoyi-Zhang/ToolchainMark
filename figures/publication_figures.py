"""Toolchain evidence diagrams and charts derived from retained counts."""
import csv
import json
from fractions import Fraction
from itertools import product
from pathlib import Path
from pictograms import icon
from matplotlib.patches import Polygon

from figure_style import (AMBER, BLUE, INK, LIGHT, MINT, MUTED, RULE, SAND, TEAL,
                          Plate, arguments, grid, paper_style, plot, plt, save)

HERE=Path(__file__).resolve().parent
RESULTS=HERE/'../results'

def polygon(d, pts, fill, edge, lw=.8, dash=False, z=2):
    d.ax.add_patch(Polygon(pts,closed=True,facecolor=fill,edgecolor=edge,
                           linewidth=lw,linestyle='--' if dash else '-',zorder=z))

def file_glyph(d,x,y,w,h,tone=BLUE,fill=LIGHT):
    f=min(8,w/4)
    polygon(d,[(x,y),(x+w,y),(x+w,y+h-f),(x+w-f,y+h),(x,y+h)],fill,tone,z=.5)
    d.rule(x+w-f,y+h,x+w-f,y+h-f,c=tone)
    d.rule(x+w-f,y+h-f,x+w,y+h-f,c=tone)

def cartridge(d,x,y):
    polygon(d,[(x,y+5),(x+5,y),(x+52,y),(x+57,y+5),(x+57,y+36),
               (x+52,y+41),(x+5,y+41),(x,y+36)],LIGHT,BLUE,z=.5)
    d.frame(x+11,y+10,34,22,'white',BLUE)
    for u in range(6,52,7):d.rule(x+u,y,x+u,y+6,c=BLUE,lw=.65)

def payload(d,x,y,solid=True):
    polygon(d,[(x-9,y-8),(x+9,y-8),(x+9,y+8),(x+3,y+8),(x+3,y+5),
               (x-3,y+5),(x-3,y+8),(x-9,y+8)],
            MINT if solid else 'white',TEAL if solid else RULE,dash=not solid,z=4)
    if solid:d.text(x,y,r'$p$',10,color=TEAL)

def lens(d,x,y):
    d.rule(x+6,y-6,x+13,y-13,c=INK,lw=1.3)
    d.dot(x,y,'',edge=INK,r=8)

def ink(d,xs,ys,color,lw=.85):
    d.ax.plot(xs,ys,color=color,lw=lw,solid_capstyle='round',zorder=6)

def motivation(out,preview):
    from diagram_ink import emit
    emit('motivating-counterexample',out,preview)

def architecture(out,preview):
    from diagram_ink import emit
    emit('architecture',out,preview)

def trace(out,preview):
    from diagram_ink import emit
    emit('trace-model',out,preview)

def coherence(out,preview):
    from diagram_ink import emit
    emit('snapshot-coherence',out,preview)

def external(out,preview):
    p=RESULTS/'external-transfer/case_summary.csv'
    with p.open(encoding='utf8',newline='') as f:rows=list(csv.DictReader(f))
    assert {r['case'] for r in rows}=={'119','2929','363'}
    labels={'119':'Newton–Raphson','2929':'Clustering','363':'Weighted mean'}
    f,a=plot(354,129,left=94,bottom=31,top=23,right=17)
    for i,r in enumerate(rows):
        y=2-i
        n=int(r['compatibility_configs'])
        x=int(r['compatibility_exit_only_satisfied']); z=int(r['compatibility_host_satisfied'])
        assert n==10 and 0<=z<=x<=n
        # Keep each case on one row. Nested marks show exact ties without jitter.
        a.hlines(y,z,x,lw=.8,color=RULE,zorder=1)
        a.scatter(x,y,marker='o',s=39,facecolors='white',edgecolors=BLUE,
                  linewidths=.85,zorder=3)
        a.scatter(z,y,marker='s',s=11,c=AMBER,linewidths=.4,zorder=4)
    a.set(xlim=(-.35,10.55),ylim=(-.48,2.48),xticks=[0,2,4,6,8,10],yticks=[2,1,0],
          yticklabels=[labels[r['case']] for r in rows],xlabel='Satisfied configurations (out of 10 per pair)')
    a.scatter([],[],marker='o',s=39,facecolors='white',edgecolors=BLUE,
              linewidths=.85,label='Exit only')
    a.scatter([],[],marker='s',s=11,c=AMBER,linewidths=.4,label='Host output')
    a.legend(ncol=2,loc='lower left',bbox_to_anchor=(0,1.02),fontsize=9)
    grid(a,'x');save(f,out,'external-transfer',preview)

def native(out,preview):
    r=json.loads((RESULTS/'owned-native-full-20261014-001/summary.json').read_text(encoding='utf8'))
    cohorts=r['cohorts']
    assert sum(sum(x.values()) for x in cohorts.values())==r['rows']==704
    assert r['direct_integrity_disagreements']==0
    f,a=plot(426,112,left=115,bottom=29,top=24,right=12)
    for i,(key,label,c,hatch) in enumerate([('SATISFIED','Satisfied',TEAL,''),('INCONSISTENT','Inconsistent',AMBER,'//'),
                                           ('INADMISSIBLE','Inadmissible',MUTED,'..')]):
        left=[sum(cohorts[k].get(prev,0) for prev in ['SATISFIED','INCONSISTENT','INADMISSIBLE'][:i])
              for k in ['clean-workflow','integrity-challenge']]
        vals=[cohorts[k].get(key,0) for k in ['clean-workflow','integrity-challenge']]
        a.barh([1,0],vals,left=left,height=.48,color=c,edgecolor='white',hatch=hatch,label=label)
        for y,(x,n) in enumerate(zip(left,vals)):
            if n:a.text(x+n/2,1-y+.35,str(n),color=c,va='center',ha='center',fontsize=8.6,fontweight='bold')
    a.set(xlim=(0,400),ylim=(-.34,1.55),yticks=[1,0],
          yticklabels=['Clean workflow','Integrity challenges'],xlabel='Retained relation checks (count)')
    a.legend(loc='lower left',bbox_to_anchor=(-.01,1.04),ncol=3,fontsize=8.5)
    save(f,out,'native-admission',preview)

def transition(out,preview):
    p=RESULTS/'current-native/derived/legacy_transitions.csv'
    with p.open(encoding='utf8',newline='') as f:
        n={(r['legacy'],r['evidence_gated']):int(r['rows']) for r in csv.DictReader(f)}
    assert sum(n.values())==18900
    assert (n['PASS','INCONSISTENT'],n['PASS','INADMISSIBLE'],n['FAIL','INADMISSIBLE'])==(270,540,468)
    old=['FAIL','PASS']
    totals=[sum(k for (src,_),k in n.items() if src==s) for s in old]
    assert totals==[4464,14436]
    f,a=plot(426,128,left=113,bottom=46,top=26,right=17)
    offsets=[0.,0.]
    for dest,label,c,hatch in [('INADMISSIBLE','Inadmissible',MUTED,'..'),
                               ('INCONSISTENT','Inconsistent',AMBER,'//'),
                               ('SATISFIED','Satisfied',TEAL,'')]:
        vals=[100*n.get((s,dest),0)/total for s,total in zip(old,totals)]
        a.barh([1,0],vals,left=offsets,color=c,edgecolor='white',linewidth=.5,hatch=hatch,
               height=.48,label=label)
        offsets=[x+y for x,y in zip(offsets,vals)]
    a.set(xlim=(0,100),ylim=(-.5,1.5),xticks=(0,25,50,75,100),yticks=[1,0],
          yticklabels=[f'Earlier fail · {totals[0]:,}',f'Earlier pass · {totals[1]:,}'],
          xlabel='Share within the earlier outcome (%)')
    a.legend(ncol=3,loc='lower left',bbox_to_anchor=(0,1.04),fontsize=8.7)
    a.tick_params(axis='y',length=0)
    f.text(.264,.072,'270 earlier passes used the wrong rejection kind.',
           color=AMBER,fontsize=8.9)
    grid(a,'x')
    save(f,out,'protocol-transition',preview)

def sensitivity(out,preview):
    with (HERE/'results-overview.csv').open(encoding='utf8',newline='') as f:
        rows=list(csv.DictReader(f))
    for key,w,h in [('fixed',184,115),('holdout',198,150)]:
        rr=[r for r in rows if r['panel']==key]
        assert len(rr)==(4 if key=='fixed' else 12)
        if key=='fixed':assert [int(r['exposed']) for r in rr]==[21,27,33,69]
        if key=='holdout':assert sum(int(r['exposed'])==0 for r in rr)==5
        f,a=plot(w,h,left=75 if key=='fixed' else 73,bottom=29,top=15 if key=='holdout' else 9,
                 right=14 if key=='fixed' else 49)
        if key=='holdout':
            a.text(1.065,1.025,'Count',transform=a.transAxes,
                   ha='left',va='bottom',fontsize=7.5,color=MUTED)
        for i,row in enumerate(rr):
            v=float(100*Fraction(int(row['exposed']),int(row['planned'])))
            y=len(rr)-i
            a.hlines(y,0,v,color=TEAL,lw=1.2)
            a.plot(v,y,marker='o' if v else 's',color=AMBER if v==0 else BLUE,
                   ms=3.6,mfc=BLUE if v else 'white',mew=.8,clip_on=False)
            count=f"{row['exposed']}/{row['planned']}"
            if key=='fixed':
                a.annotate(count,(v,y),xytext=(-2,4),ha='right',textcoords='offset points',fontsize=8.2)
            else:
                a.text(1.065,y,count,transform=a.get_yaxis_transform(),ha='left',
                       va='center',fontsize=8.7,color=AMBER if not v else INK)
        a.set(xlim=(-6 if key=='holdout' else 0,100),yticks=range(1,len(rr)+1),yticklabels=[r['label'] for r in rr[::-1]],
              ylim=(.7,len(rr)+.52),
              xticks=[0,50,100],xticklabels=['0','50','100'],xlabel='Exposed units (%)')
        a.xaxis.label.set_fontsize(8.8)
        a.tick_params(axis='y',length=0,labelsize=8.6)
        grid(a,'x');save(f,out,'results-overview-'+key,preview)

def evaluation(out,preview):
    from diagram_ink import emit
    emit('evaluation-design',out,preview)

def clause_coverage(out,preview):
    d=Plate(420,109)
    d.text(18,98,'Violation pattern',9.6,ha='left',weight='bold')
    d.text(237,98,r'Relation $R_1$',9.6,weight='bold')
    d.text(316,98,r'Relation $R_2$',9.6,weight='bold')
    d.text(408,98,'Domain',9.6,ha='right',weight='bold')
    d.band(8,65,404,20,LIGHT)
    d.band(8,15,404,47,MINT)
    for y,label,hits,group in ((75,'Both clauses',(True,True),'Observed'),
                              (49,'Only clause 1',(True,False),'Possible'),
                              (26,'Only clause 2',(False,True),'Possible')):
        d.text(18,y,label,9.5,ha='left')
        for x,hit in zip((237,316),hits):
            d.dot(x,y,'',fill=AMBER if hit else 'white',edge=AMBER if hit else MUTED,r=4.2)
        d.text(403,y,group,9.3,ha='right',color=MUTED)
    d.dot(13,8,'',fill=AMBER,edge=AMBER,r=3.0); d.text(23,8,'Distinguishes',8.6,ha='left')
    d.dot(96,8,'',fill='white',edge=MUTED,r=3.0); d.text(106,8,'Does not distinguish',8.6,ha='left')
    d.save(out,'clause-coverage',preview)


if __name__=='__main__':
    args=arguments();paper_style()
    for draw in (motivation,architecture,trace,coherence,external,native,transition,sensitivity,evaluation,clause_coverage):draw(args.outdir,args.previews)
    from diagram_ink import emit_supplemental
    emit_supplemental(args.outdir,args.previews)

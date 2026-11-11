"""Trace, admission, and artifact-binding diagrams for ToolchainMark."""
from diagram_ink import Diagram,S,T,A,K,G,F,L,P,O


def motivating_counterexample():
    d=Diagram(428,139)
    for x,title,c in [(12,'(a) Artifact-bound extraction',T),(218,'(b) Sidecar substitution',A)]:
        d.tag(x,126,title)
        d.mark('code',x+29,64,23,S)
        d.txt(x+29,42,'Artifact',9.3)
        d.mark('lens',x+103,64,19,c)
        d.txt(x+103,42,'Extractor',9.3)
        d.wire((x+117,64),(x+159,64),c=c)
        d.dotmark(x+170,64,7,c=c)
        d.node_label(x+170,64,r'$p$',9.9,color=c)
        if c==T:
            d.wire((x+45,64),(x+90,64),c=T)
            d.txt(x+68,76,'Reads carrier',8.8,color=T)
        else:
            d.mark('doc',x+29,101,18,A)
            d.txt(x+45,101,'Sidecar',8.9,ha='left',color=A)
            d.wire((x+29,90),(x+29,82),(x+103,82),(x+103,75),c=A,dash=True)
            d.wire((x+45,64),(x+74,64),c=F,arrow=False,dash=True)
            d.mark('reject',x+80,64,13,A)
        d.mark('check' if c==T else 'reject',x+41,16,16,c)
        d.txt(x+55,16,'Bound to artifact' if c==T else 'Binding violated',9.3,ha='left',color=c)
    return d


def trace_model():
    d=Diagram(428,133)
    stages=[(92,'Embed','code'),(146,'Compile','array'),(200,'Transform','patch'),
            (254,'Execute','trace'),(308,'Extract','lens')]
    for x,t,k in stages:d.txt(x,120,t,9.7)
    for y,proj,lab,obs,c in [(100,81,r'$\tau_s$',r'$O_R(\tau_s)$',S),
                             (51,27,r'$\tau_f$',r'$O_R(\tau_f)$',T)]:
        d.txt(24,y,lab,11,color=c)
        d.wire((36,y),(79,y),c=c)
        for (x,_,_),(x2,_,_) in zip(stages,stages[1:]):
            d.wire((x+11,y),(x2-12,y),c=c)
        for x,t,k in stages:d.mark(k,x,y,17,c)
        d.wire((318,y),(337,y),c=c,arrow=False)
        # A tap stays inside its own trace's projection path.
        for x in (164,337):
            d.dotmark(x,y,1.7,c=c,fill=c)
            d.wire((x,y-3),(x,proj),c=c,dash=True,arrow=False)
        d.wire((164,proj),(360,proj),c=c,dash=True)
        d.dotmark(337,proj,1.65,c=c,fill=c)
        d.node_label(388,proj,obs,9.9,color=c)
    d.wire((388,73),(388,64),c=S)
    d.wire((388,35),(388,44),c=T)
    d.dotmark(388,54,8,c=G)
    d.node_label(388,54,r'$R$',10,color=G)
    d.wire((24,12),(45,12),c=G,dash=True,arrow=False)
    d.txt(52,12,'Observation tap',8.8,ha='left',color=G)
    return d


def architecture():
    d=Diagram(428,134)
    y=77
    for x,kind,label in ((25,'trace',r'Source $\tau_s$'),
                         (135,'trace',r'Follow-up $\tau_f$'),
                         (250,'array',r'Project $O_R$')):
        d.mark(kind,x,y,23,S if x<200 else T)
        d.txt(x,101,label,9.7)
    for x,lab in ((78,r'Applicability $A_R$'),(194,r'Intervention $E_R$'),(306,r'Predicate $\varphi_R$')):
        d.diamond(x,y,6.6,S if x<200 else T)
        d.txt(x,54 if x<200 else 104,lab,9.3)
    for a,b in ((37,68),(88,123),(147,184),(204,237),(263,296)):
        d.wire((a,y),(b,y),c=S if b<200 else T)
    for yy,c,k,lab in ((103,T,'check','Satisfied'),(56,A,'trace','Inconsistent')):
        d.wire((315,y),(339,yy),(352,yy),c=c)
        d.mark(k,362,yy,17,c)
        d.txt(373,yy,lab,9.3,ha='left',color=c)
    for x,edge in ((78,40),(194,239)):
        d.wire((x,67),(x,64),(edge,64),(edge,28),c=G,dash=True,arrow=False)
    d.wire((40,28),(338,28),c=G,dash=True)
    d.dotmark(239,28,1.7,c=G,fill=G)
    d.mark('reject',348,28,17,G)
    d.txt(360,28,'Inadmissible',9.4,ha='left',color=G)
    return d


def evaluation_design():
    d=Diagram(428,137)
    for x,title in [(9,'Comparison'),(119,'Select on'),(232,'Evaluate on'),(346,'Keep fixed')]:
        d.txt(x,124,title,9.6,ha='left',bold=True)
    rows=[
        (91,'Subject replay','doc','1 design subject','array','17 other subjects','Carrier + operator',T,False),
        (58,'Carrier holdout','array','2 carriers','array','Excluded carrier','All 24 operators',A,True),
        (25,'Mechanism holdout','patch',r'$M\setminus H$','patch',r'Omitted $H$','All 3 carriers',A,True),
    ]
    for y,lab,kind,selection,kind2,evaluation,control,color,holdout in rows:
        d.txt(9,y,lab,9.5,ha='left')
        d.mark(kind,115,y,14,S)
        d.txt(126,y,selection,9.2,ha='left',color=S)
        d.wire((198,y),(216,y),c=color,dash=holdout,lw=1.0)
        d.mark(kind2,226,y,14,color)
        d.txt(237,y,evaluation,9.2,ha='left',color=color)
        d.txt(346,y,control,9.0,ha='left',color=G)
    # Label the arrow column, not just the first arrow.
    d.node_label(207,124,'Suite',8.8,color=G)
    return d


def snapshot_coherence():
    d=Diagram(428,125)
    d.mark('keyed',35,93,22,S)
    d.txt(35,112,r'Capture $F$',9.4)
    d.wire((50,93),(84,93),c=S)
    d.mark('vector',96,93,17,S)
    d.txt(111,93,'Integrity evidence',9.3,ha='left')
    d.wire((202,93),(293,93),c=S)
    for y,lab in ((61,'Live before test'),(28,'Live after test')):
        d.mark('doc',96,y,16,S)
        d.txt(111,y,lab,9.3,ha='left')
        d.wire((183,y),(200,y),(218,44),c=S,arrow=False)
    d.dotmark(218,44,2,c=S,fill=S)
    d.wire((222,44),(242,44),c=S)
    d.diamond(250,44,5.5,T)
    d.txt(250,61,r'Both $=F$?',9.3,color=T)
    d.wire((257,44),(304,44),(304,82),c=T)
    d.txt(280,54,'Yes',8.8,color=T)
    d.diamond(304,93,7,T)
    d.node_label(304,93,r'$\wedge$',8.7,color=T)
    d.wire((313,93),(351,93),c=T)
    d.txt(361,93,'Predicate',9.3,ha='left')
    d.wire((250,36),(250,13),(346,13),c=A,dash=True)
    d.txt(271,24,'No',8.8,color=A)
    d.mark('reject',357,13,15,A)
    d.txt(369,13,'Withhold',9.3,ha='left',color=A)
    return d


def rejection_taxonomy():
    d=Diagram(420,69)
    d.mark('trace',24,33,22,S)
    d.txt(43,33,'Observation',9.3,ha='left')
    d.wire((108,33),(147,33),c=S)
    d.diamond(154,33,6,S)
    for y,c,k,t,outcome in [(52,T,'doc','Typed response','Test relation'),
                             (14,A,'reject','Missing run data','Inadmissible')]:
        d.wire((163,33),(184,y),(211,y),c=c,dash=c==A)
        d.mark(k,221,y,16,c)
        d.txt(235,y,t,9.2,ha='left')
        d.wire((326,y),(345,y),c=c,dash=c==A)
        d.txt(353,y,outcome,9.2,ha='left',color=c)
    return d


def removal_gates():
    d=Diagram(420,63)
    y=38
    source,admit,remove,observe,compare=21,79,145,211,277
    d.mark('code',source,y,20,S)
    d.txt(source,18,'Source',9.1,color=S)
    d.mark('patch',remove,y,18,S)
    d.txt(remove,55,'Remove',9.1,color=S)
    for x,label,color in ((admit,'Source gate',S), (observe,'Removal gate',S),
                          (compare,'Compare',T)):
        d.diamond(x,y,5.5,color)
        d.txt(x,55,label,9.1,color=color)
    for start,end in ((source+13,admit-8),(admit+8,remove-12),
                      (remove+12,observe-8),(observe+8,compare-8)):
        d.wire((start,y),(end,y),c=S)

    for target,color,mark,label in ((49,T,'check','Same: satisfied'),
                                   (28,A,'reject','Other: inconsistent')):
        d.wire((compare+8,y),(297,target),(303,target),c=color)
        d.mark(mark,313,target,13,color)
        d.txt(325,target,label,9.1,ha='left',color=color)

    rail=9
    d.wire((admit,y-8),(admit,rail),(compare,rail),c=G,dash=True,arrow=False)
    for x in (observe,compare):
        d.wire((x,y-8),(x,rail),c=G,dash=True,arrow=False)
        d.dotmark(x,rail,1.5,c=G,fill=G)
    d.wire((compare+3,rail),(303,rail),c=G,dash=True)
    d.mark('lock',313,rail,12,G)
    d.txt(325,rail,'Inadmissible',9.1,ha='left',color=G)
    return d


def carrier_locations():
    d=Diagram(420,39)
    for x,title,kind,c in [(13,'Generated source','code',S),
                            (150,'Exported names','symbol',T),
                            (285,'ELF sections','array',A)]:
        d.mark(kind,x+8,27,13,c)
        d.txt(x+21,27,title,9.1,ha='left',bold=True)
    for x,segments,selected,c in [
        (10,(31,59,19),1,S),(150,(29,59,20),1,T),(285,(27,64,21),1,A)]:
        for j,w in enumerate(segments):
            at=x+sum(segments[:j])
            d.block(at,3,w,13,c if j==selected else F,
                    {S:L,T:P,A:O}[c] if j==selected else 'white')
    for x,label,c in [(70.5,'Payload bytes',S),(208.5,'Name payload',T),(344,'RO section',A)]:
        d.node_label(x,9.5,label,8.45,color=c)
    return d


FIGURES={f.__name__.replace('_','-'):f for f in (
    motivating_counterexample,trace_model,architecture,evaluation_design,snapshot_coherence,
    rejection_taxonomy,removal_gates,carrier_locations)}

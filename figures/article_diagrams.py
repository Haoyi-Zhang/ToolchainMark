"""Trace, admission, and artifact-binding diagrams for ToolchainMark."""
from diagram_ink import Diagram,S,T,A,K,G,F,L,P,O


def motivating_counterexample():
    d=Diagram(428,139)
    for x,title,c in [(12,'(a) Artifact-bound extraction',T),(218,'(b) Sidecar substitution',A)]:
        d.tag(x,126,title)
        d.mark('code',x+29,61,26,S)
        d.txt(x+29,39,'Artifact',8.8)
        d.mark('lens',x+105,61,22,c);d.txt(x+105,39,'Extractor',8.8)
        d.wire((x+120,61),(x+162,61),c=c)
        d.txt(x+175,61,r'$p$',10,color=c)
        if c==T:
            d.wire((x+46,61),(x+90,61),c=T)
            d.txt(x+69,73,'Read',8.6,color=T)
        else:
            d.mark('doc',x+29,97,20,A);d.txt(x+45,97,'Sidecar',8.6,ha='left',color=A)
            d.wire((x+30,83),(x+30,77),(x+105,77),(x+105,73),c=A,dash=True)
            d.wire((x+45,61),(x+76,61),c=F,arrow=False,dash=True)
            d.mark('reject',x+81,61,12,A)
        d.mark('check' if c==T else 'reject',x+50,15,17,c)
        d.txt(x+64,15,'Bound to artifact' if c==T else 'Binding violated',9,ha='left',color=c)
    return d


def trace_model():
    d=Diagram(428,133)
    nodes=[(105,'Embed'),(170,'Compile'),(235,'Transform'),
           (300,'Execute'),(366,'Extract')]
    for y,lab,c in [(79,r'Source $\tau_s$',S),(50,r'Follow-up $\tau_f$',T)]:
        d.txt(14,y,lab,9.4,ha='left',color=c)
        for (x,_),(x2,_) in zip(nodes,nodes[1:]):
            d.wire((x+4,y),(x2-5,y),c=c)
        for x,_ in nodes:d.dotmark(x,y,3.5,c=c)
    for x,label in nodes:
        d.txt(x,101,label,9.7,bold=True)
    for x in (170,366):
        d.wire((x,74),(x,55),c=F,dash=True,arrow=False)
        d.wire((x,45),(x,31),(255 if x<250 else 283,31),c=T)
    d.dotmark(269,31,3,c=T,fill=T)
    d.txt(269,11,r'Compare $O_R(\tau_s)$ and $O_R(\tau_f)$',9.4,color=T)
    return d


def architecture():
    d=Diagram(428,134)
    d.tag(7,116,'Isolated executions')
    for y,label,observation,c in [(88,r'Source $\tau_s$',r'$O_R(\tau_s)$',S),
                                   (42,r'Follow-up $\tau_f$',r'$O_R(\tau_f)$',T)]:
        d.txt(8,y,label,9.3,ha='left',color=c)
        d.wire((73,y),(100,y),c=c)
        d.txt(127,y,observation,10.8,color=c)
        d.wire((157,y),(178,y),(178,65),c=c,arrow=False)
    d.dotmark(178,65,2.2,c=G,fill=G)
    d.wire((181,65),(218,65),c=G)
    d.diamond(227,65,7,S)
    d.txt(227,86,'Admission gate',9.4,bold=True)
    d.wire((234,65),(290,65),c=T)
    d.diamond(298,65,7,T)
    d.txt(298,85,'Predicate',9.4,bold=True)
    d.wire((306,65),(334,65),(334,95),(366,95),c=T)
    d.wire((334,65),(334,48),(366,48),c=A)
    d.txt(374,95,'Satisfied',9.1,ha='left',color=T)
    d.txt(374,48,'Inconsistent',9.0,ha='left',color=A)
    d.wire((227,57),(227,18),(342,18),c=A,dash=True)
    d.txt(349,18,'Inadmissible',9.0,ha='left',color=A)
    return d


def evaluation_design():
    d=Diagram(428,137)
    d.tag(10,123,'(a) Subject replay')
    d.tag(151,123,'(b) Carrier holdout')
    d.tag(287,123,'(c) Mechanism holdout')
    d.txt(30,79,'1 subject',10.3,color=S)
    d.wire((54,79),(76,79),c=S)
    d.txt(104,79,'17 subjects',10.3,color=T)
    d.txt(30,61,'Design',9.2,color=G)
    d.txt(104,61,'Replay',9.2,color=G)
    d.txt(68,31,'Fix carrier and mechanism',9.1)
    for x in (159,176):d.block(x,74,12,10,S,'white')
    d.wire((196,79),(222,79),c=S)
    d.block(230,74,12,10,A,'white')
    d.txt(173,59,'Select',9.2,color=S)
    d.txt(236,59,'Hold out',9.2,color=A)
    d.txt(203,31,'Fix all 24 mechanisms',9.1)
    d.txt(311,79,r'$M\setminus H$',10.5,color=S)
    d.wire((339,79),(368,79),c=S)
    d.txt(383,79,r'$H$',10.5,color=A)
    d.txt(311,59,'Select',9.2,color=S)
    d.txt(383,59,'Hold out',9.2,color=A)
    d.txt(347,31,'Fix all three carriers',9.1)
    return d


def snapshot_coherence():
    d=Diagram(428,125)
    d.mark('keyed',43,83,24,S);d.txt(43,108,r'Capture $F$',9.2,bold=True)
    d.wire((58,83),(93,83),(93,103),(156,103),c=S)
    d.wire((93,83),(156,83),c=S)
    d.wire((93,83),(93,63),(156,63),c=S)
    d.mark('lens',170,103,20,T);d.txt(184,103,'Extract from capture',8.9,ha='left')
    for y,label in [(83,'Live before'),(63,'Live after')]:
        d.diamond(170,y,5.3,T)
        d.txt(184,y,label+r' $=F$?',8.8,ha='left')
        d.wire((267,y),(286,y),(286,88),c=T,arrow=False)
    d.wire((276,103),(286,103),(286,88),(330,88),c=T)
    d.mark('check',342,88,19,T);d.txt(358,88,'Predicate',8.9,ha='left')
    d.wire((286,63),(286,37),(330,37),c=A,dash=True)
    d.txt(298,50,'Mismatch',8.2,ha='left',color=A)
    d.mark('reject',342,37,19,A);d.txt(358,37,'Withhold',8.9,ha='left',color=A)
    d.txt(358,24,'attribution',8.3,ha='left',color=A)
    return d


def rejection_taxonomy():
    d=Diagram(420,69)
    d.mark('trace',25,34,22,S);d.txt(43,34,'Observation',9.3,ha='left')
    d.wire((100,34),(135,34),c=S)
    d.diamond(143,34,6,S)
    d.wire((149,34),(164,34),(164,54),(209,54),c=T)
    d.wire((164,34),(164,14),(209,14),c=A,dash=True)
    d.txt(219,54,'Typed response',9.1,ha='left')
    d.txt(219,14,'Infrastructure failure',9.0,ha='left')
    d.wire((303,54),(330,54),c=T)
    d.wire((311,14),(330,14),c=A,dash=True)
    d.txt(340,54,'Test relation',8.8,ha='left',color=T)
    d.txt(340,14,'Inadmissible',8.8,ha='left',color=A)
    return d


def removal_gates():
    d=Diagram(420,55)
    d.mark('code',24,32,22,S);d.txt(24,12,'Source',8.4)
    d.wire((38,32),(88,32),c=S)
    d.diamond(95,32,5,S);d.txt(95,45,'Observe source',8.5)
    d.wire((101,32),(181,32),c=S)
    d.mark('patch',191,32,19,T);d.txt(191,12,'Apply removal',8.5)
    d.wire((203,32),(259,32),c=T)
    d.diamond(266,32,5,T);d.txt(266,45,'Verify effect',8.5)
    d.wire((272,32),(343,32),c=T)
    d.mark('lens',354,32,19,T);d.txt(367,32,'Rejection',8.6,ha='left')
    d.txt(367,19,'kind',8.5,ha='left')
    return d


def carrier_locations():
    d=Diagram(420,39)
    d.txt(69,30,'Generated source',9.2,bold=True)
    d.txt(20,11,'const',8.6,ha='left')
    d.block(48,4,63,14,S,'white')
    d.txt(79,11,'payload bytes',8.4,color=S)
    d.txt(211,30,'ELF exported names',9.2,bold=True)
    d.block(152,4,118,14,F,'white')
    d.block(177,4,68,14,T,'white')
    d.txt(165,11,'...',8.4,color=G)
    d.txt(211,11,'payload in name',8.4,color=T)
    d.txt(258,11,'...',8.4,color=G)
    d.txt(353,30,'ELF sections',9.2,bold=True)
    for x,w,c in [(291,24,F),(315,76,A),(391,24,F)]:
        d.block(x,4,w,14,c,'white')
    d.txt(353,11,'dedicated section',8.4,color=A)
    return d


FIGURES={f.__name__.replace('_','-'):f for f in (
    motivating_counterexample,trace_model,architecture,evaluation_design,snapshot_coherence,
    rejection_taxonomy,removal_gates,carrier_locations)}

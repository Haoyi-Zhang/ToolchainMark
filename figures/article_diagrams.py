"""Trace, admission, and artifact-binding diagrams for ToolchainMark."""
from diagram_ink import Diagram,S,T,A,K,G,F,L,P,O


def motivating_counterexample():
    d=Diagram(428,139)
    d.tag(12,126,'Paired extraction traces')
    d.tag(216,126,'Contract-aware validation')
    d.txt(245,103,'Clean relocation',9.1,color=T)
    d.txt(319,101,'Admit pair?',8.6,bold=True,color=G)
    for y,lab,kind,c in ((77,'Carrier','code',T),(46,'Sidecar','doc',A)):
        d.mark(kind,22,y,19,c)
        d.txt(35,y,lab,9.2,ha='left',color=c)
        d.wire((71,y),(92,y),c=c,dash=y==46)
        d.block(96,y-8,101,16,c,'white')
        d.node_label(147,y,r'$p$',10.1,color=c)
        d.wire((200,y),(217,y),c=c)
        d.txt(248,y,r'$p\to p$' if y==77 else r'$p\to\bot$',10.3,color=c)
        d.wire((272,y),(310,y),c=c)
        d.diamond(319,y,6,G)
        d.wire((327,y),(341,y),c=c)
        d.mark('check' if y==77 else 'reject',353,y,13,c)
        d.txt(364,y,'Satisfied' if y==77 else 'Inconsistent',9.2,ha='left',color=c)
    d.txt(147,102,'Original extraction',9.1)
    d.txt(147,20,'Round trip: both pass',9.0,color=G)
    d.txt(245,25,'Artifact only',8.2,color=G)
    d.txt(245,13,'Same host result',8.2,color=G)
    # Each comparison independently reaches the admission decision.
    d.txt(345,88,'Yes',7.6,color=G)
    d.wire((319,69),(319,61),(331,61),c=A,dash=True)
    d.txt(336,61,'No: withhold verdict',8.1,ha='left',color=A)
    d.wire((319,38),(319,16),(331,16),c=A,dash=True)
    d.txt(336,16,'No: withhold verdict',8.1,ha='left',color=A)
    return d


def trace_model():
    d=Diagram(428,133)
    d.tag(12,121,'Two trace records')
    d.tag(241,121,'Payload projection')
    for x,label in ((82,'Build'),(121,'Artifact'),(160,'Host'),(199,'Extract')):
        d.txt(x,105,label,8.9,color=G)
    for y,t,c in ((81,'s',S),(40,'f',T)):
        d.txt(29,y,rf'$\tau_{t}$',11,color=c)
        for x,l in ((82,r'$\widehat{\theta}$'),(121,r'$a$'),(160,r'$\sigma$'),(199,r'$\rho$')):
            d.block(x-15,y-8,30,16,c if x==199 else F,'white')
            d.node_label(x,y,l,10,color=c if x==199 else G)
        d.wire((216,y),(244,y),c=c)
        d.txt(266,y,rf'$\rho_{t}$',10.3,color=c)
        d.wire((281,y),(314,y),(337,61),c=c,arrow=False)
    d.dotmark(344,61,7,c=G)
    d.node_label(344,61,r'$R$',9.8)
    d.txt(361,61,'Compare',9.2,ha='left')
    return d


def architecture():
    d=Diagram(426,140)
    d.mark('trace',26,88,16,S)
    d.txt(26,66,r'$\tau_s$',10,color=S)
    d.wire((37,88),(68,88),c=S)
    for x,label in ((75,'Applicable'),(186,'Intervention'),(268,'Observations')):
        d.diamond(x,88,5.5,T)
        d.txt(x,113,label,9.1)
        d.wire((x,81),(x,31),c=A,dash=True,arrow=False)
        d.dotmark(x,31,1.4,c=A,fill=A)
    d.wire((82,88),(102,88),c=T)
    d.mark('trace',121,88,16,T)
    d.txt(121,66,r'Follow-up $\tau_f$',9.1,color=T)
    d.wire((132,88),(178,88),c=T)
    d.wire((194,88),(260,88),c=T)
    d.txt(226,101,r'$E_R(\tau_s,\tau_f)$',8.9,color=G)
    d.wire((276,88),(307,88),c=T)
    d.dotmark(316,88,7,c=T)
    d.node_label(316,88,r'$\varphi_R$',9.0,color=T)
    d.txt(316,61,r'Polarity $\pi_R$',8.9,color=G)
    for y,lab,k,c in ((105,'Satisfied','check',T),(76,'Inconsistent','reject',A)):
        d.wire((325,88),(345,y),c=c)
        d.mark(k,356,y,11,c)
        d.txt(367,y,lab,8.9,ha='left',color=c)
    d.wire((75,31),(306,31),c=A,dash=True)
    d.mark('reject',316,31,11,A)
    d.txt(330,31,'Inadmissible',9.0,ha='left',color=A)
    d.txt(75,17,'Not applicable',8.3,color=A)
    d.txt(186,17,'Not established',8.3,color=A)
    d.txt(268,17,'Missing',8.3,color=A)
    return d


def evaluation_design():
    d=Diagram(428,137)
    d.tag(10,124,'Design subject')
    d.tag(174,124,'Replayed or held-out evidence')
    d.txt(12,100,'Replay',9.3,ha='left',bold=True)
    d.mark('array',84,100,14,S)
    d.wire((97,100),(164,100),c=S)
    d.mark('array',179,100,14,S)
    d.txt(195,100,'Same carrier and mechanism',9.1,ha='left')
    d.txt(412,100,'17 other subjects',9.0,ha='right',color=S)
    for y,left,labels,right,n in (
            (65,'Carrier',('1','2','3'),'Third carrier','18 subjects'),
            (32,'Class',('',r'$\ldots$','H'),'Held-out class','17 other subjects')):
        d.txt(12,y,left,9.3,ha='left',bold=True)
        for i,(x,l) in enumerate(zip((73,92,111),labels)):
            d.block(x-8,y-7,16,14,A if i==2 else T,'white' if i==2 else P)
            if l:
                d.node_label(x,y,l,8.6,color=A if i==2 else T)
        d.wire((121,y),(166,y),c=A,dash=True)
        d.block(172,y-7,15,14,A,'white')
        d.node_label(179.5,y,labels[-1],8.6,color=A)
        d.txt(195,y,right,9.1,ha='left')
        d.txt(412,y,n,9.0,ha='right',color=A)
    d.block(79,10,10,7,T,P)
    d.txt(94,13,'Selection pool',8.5,ha='left',color=T)
    d.block(169,10,10,7,A,'white')
    d.txt(184,13,'Held out',8.5,ha='left',color=A)
    return d


def snapshot_coherence():
    d=Diagram(428,117)
    d.mark('keyed',152,99,17,S)
    d.txt(169,99,r'Snapshot $F$',9.2,ha='left',color=S)
    for x,label in ((86,'Before: live = F?'),(228,'After: live = F?')):
        d.diamond(x,60,5.7,S)
        d.txt(x-12 if x<150 else x+12,86,label,8.9)
        d.wire((151,89),(x,68),c=S,dash=True)
        d.wire((x,53),(x,24),(132 if x<150 else 192,24),c=A,dash=True,arrow=False)
    d.wire((132,24),(153,24),c=A,dash=True,arrow=False)
    d.wire((192,24),(170,24),c=A,dash=True,arrow=False)
    d.mark('reject',161,24,11,A)
    d.txt(161,9,'Either differs: withhold verdict',8.9,color=A)
    d.txt(13,60,'Live set',9.1,ha='left')
    d.wire((52,60),(78,60),c=G)
    d.wire((94,60),(134,60),c=T)
    d.mark('lens',149,60,19,T)
    d.txt(149,40,'Extract',9.2,color=T)
    d.wire((162,60),(220,60),c=T)
    d.wire((236,60),(279,60),c=T)
    d.mark('check',293,60,16,T)
    d.txt(307,60,'Compare predicate',9.2,ha='left',color=T)
    return d


def rejection_taxonomy():
    d=Diagram(420,69)
    d.mark('trace',26,36,20,S)
    d.txt(44,36,'Run',9.3,ha='left')
    d.wire((67,36),(102,36),c=S)
    d.diamond(109,36,5.2,S)
    for y,c,k,t,outcome,glyph in ((52,T,'doc','Typed response','Test relation','graph'),
                                  (15,A,'reject','Missing run data','Inadmissible','reject')):
        d.wire((116,36),(140,y),(174,y),c=c,dash=y==15)
        d.mark(k,185,y,15,c)
        d.txt(201,y,t,9.2,ha='left')
        d.wire((281,y),(308,y),c=c,dash=y==15)
        d.mark(glyph,319,y,13,c)
        d.txt(332,y,outcome,9.2,ha='left',color=c)
    return d


def removal_gates():
    d=Diagram(420,106)
    d.mark('patch',23,61,16,S)
    d.wire((35,61),(72,61),c=S)
    d.diamond(79,61,5.3,S)
    d.txt(70,82,'Verified removal',9.0)
    d.wire((86,61),(142,61),c=T)
    d.diamond(149,61,5.3,T)
    d.txt(160,82,'Observed outcome',9.0)
    d.wire((79,54),(79,13),(190,13),c=G,dash=True,arrow=False)
    d.wire((149,54),(149,13),c=G,dash=True,arrow=False)
    d.dotmark(149,13,1.7,c=G,fill=G)
    d.wire((190,13),(224,13),c=G,dash=True)
    d.txt(70,31,'Not verified',8.1,ha='right',color=G)
    d.txt(157,27,'Unavailable',8.1,ha='left',color=G)
    d.txt(233,13,'Inadmissible',9.1,ha='left',color=G)
    for y,lab,k,out,c in ((61,'Expected rejection','check','Satisfied',T),
                           (39,'Other observed result','reject','Inconsistent',A)):
        d.wire((156,61),(178,y),(187,y),c=c,arrow=False)
        d.txt(197,y,lab,9,ha='left',color=c)
        d.wire((285,y),(308,y),c=c)
        d.mark(k,320,y,12,c)
        d.txt(333,y,out,9.1,ha='left',color=c)
    return d


def carrier_locations():
    d=Diagram(420,39)
    for x,title,kind,c in [(16,'Source byte array','code',S),
                            (152,'Exported name','symbol',T),
                            (286,'ELF section','array',A)]:
        d.mark(kind,x+8,27,13,c)
        d.txt(x+21,27,title,9.1,ha='left',bold=True)
    d.txt(22,10,r'$\{\ b_0,\ b_1,\ \ldots\ \}$',9.6,ha='left',color=S)
    d.txt(160,10,r'$\mathrm{name}(i,p_i)$',9.6,ha='left',color=T)
    d.block(296,4,42,12,F,'white')
    d.node_label(317,10,'Header',8.4,color=G)
    d.wire((340,10),(355,10),c=A)
    d.block(361,4,37,12,A,O)
    d.node_label(379,10,'Bytes',8.4,color=A)
    return d


FIGURES={f.__name__.replace('_','-'):f for f in (
    motivating_counterexample,trace_model,architecture,evaluation_design,snapshot_coherence,
    rejection_taxonomy,removal_gates,carrier_locations)}

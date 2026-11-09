"""Counterexample, trace, controlled design and quantitative transfer panels."""
import numpy as np
from matplotlib.ticker import PercentFormatter
from visual_grammar import *


def motivating(out):
    d=Diagram(h=160)
    for x,s in [(111,'Embed'),(197,'Compile'),(287,'Extract'),(391,'Binding')]:
        d.text(x,150,s,9.5,MUTED,bold=True)
    for y,tag,c in [(103,'Valid',TEAL),(41,'False assurance',RED)]:
        d.text(5,y+9,tag,9.5,c,'left',True)
        d.text(5,y-6,'request (H,p,k)',8.6,INK,'left')
        d.line((77,y),(321,y),c=GRID,lw=1.15)
        for x,s in [(111,'p'),(197,'a' if y==103 else 'b'),(287,'p')]:d.token(x,y,s,c)
        d.arrow((121,y),(185,y),c=c)
        d.arrow((208,y),(277,y),c=c)
        d.arrow((299,y),(368,y),c=c)
    d.text(197,83,'Carrier present',8.7,TEAL)
    d.text(197,21,'Carrier absent',8.7,RED)
    d.arrow((111,51),(111,69),(287,69),(287,52),c=RED,dash=True)
    d.text(199,69,'sidecar p',8.7,RED).set_bbox({'fc':'white','ec':'none','pad':1})
    d.check(389,103);d.cross(389,41)
    d.line((318,44),(318,101),c=MUTED,dash=True)
    d.text(326,72,'Same payload',8.8,MUTED,'left')
    d.text(389,20,'Binding fails',8.7,RED,bold=True)
    d.finish(out)


def trace(out):
    d=Diagram(h=133)
    xs=[116,187,259,331,401]
    for x,step in zip(xs,['Embed','Compile','Transform','Execute','Extract']):
        d.text(x,122,step,9.5,INK,bold=True)
        d.line((x,19),(x,109),c=GRID,dash=True)
    for y,name,c in [(94,'Source trace',BLUE),(61,'Follow-up trace',TEAL)]:
        d.text(8,y,name,9,c,'left',True)
        for x in xs:d.dot(x,y,3.5,c,'white')
        for a,b in zip(xs,xs[1:]):d.arrow((a+4,y),(b-5,y),c=c)
    for x,s in zip(xs,['Payload\nand key','Actual flags','Intervention\ncertificate',
                      'Output\nand exit','Artifact\nand extraction']):
        d.text(x,36,s,8.7)
    d.line((96,15),(415,15),c=MUTED)
    d.text(8,15,r'Projection $O_R$',9,MUTED,'left',True)
    d.finish(out)


def architecture(out):
    d=Diagram(h=152)
    d.title(7,141,'A','Relation-specific request')
    d.title(231,141,'B','Shared evidence path')
    d.line((217,14),(217,132),c=GRID,dash=True)
    d.doc(39,84)
    d.text(39,63,'Relation',9,BLUE,bold=True)
    for y,cap,c in [(111,'Source',BLUE),(57,'Follow-up',TEAL)]:
        d.arrow((48,84),(74,84),(74,y),(110,y),c=c)
        d.doc(123,y,c)
        d.text(150,y,cap,9,c,'left',True)
        d.arrow((199,y),(234,y),c=c)
        d.rect(236,y-13,58,26,PALE if y==111 else GREEN,GRID)
        d.text(265,y,'Isolated run',8.8,INK,bold=True)
        d.arrow((294,y),(314,y),(314,84),(334,84),c=c)
    d.doc(348,84)
    d.text(348,63,'Typed record',8.8)
    d.arrow((358,84),(386,84),c=BLUE)
    d.token(398,84,'V',TEAL)
    d.text(398,63,'Verdict',8.8,TEAL,bold=True)
    d.line((341,57),(341,35),c=BLUE,dash=True)
    d.text(348,24,'Immutable evidence',8.8,BLUE,bold=True)
    d.finish(out)


def evaluation(out):
    d=Diagram(h=184)
    d.title(7,173,'A','Factorial units')
    for i in [2,1,0]:
        x=37+11*i;y=59+11*i
        z=1+.4*(2-i)
        d.ax.add_patch(Rectangle((x,y),104,72,facecolor=PALE if i==0 else 'white',
                                 edgecolor=BLUE,lw=.7,zorder=z))
        for j in range(1,6):
            d.ax.plot((x+17*j,)*2,(y+.6,y+71.4),color=GRID,lw=.5,zorder=z+.16)
        for j in range(1,4):
            d.ax.plot((x+.6,x+103.4),(y+18*j,)*2,color=GRID,lw=.5,zorder=z+.16)
    d.text(97,161,'3 carrier planes',9,BLUE,bold=True)
    d.text(89,48,'24 mechanisms',9.3)
    d.text(35,34,'18 subjects',9.3,INK,'left')
    d.text(35,18,'1,296 faulty units; 756 clean executions',8.6,MUTED,'left')
    d.title(201,173,'B','Held-out slices')
    for cy,mode,cap,c in [(131,'row','Subject replay',BLUE),(85,'plane','Carrier holdout',TEAL),
                           (39,'col','Mechanism holdout',RED)]:
        for i in range(6):
            for j in range(3):
                hot=(mode=='row' and j==1) or mode=='plane' or (mode=='col' and i==2)
                d.rect(207+i*12,cy-11+j*8,10,6,c if hot else PALE,GRID if not hot else c,.35)
        d.text(290,cy,cap,9.4,c,'left',True)
    d.line((186,13),(186,154),c=GRID)
    d.finish(out)


def coherence(out):
    d=Diagram(h=140)
    xx=[43,124,213,302,388]
    for x,s in zip(xx,['Capture S','Capture F','Before read','Extraction','After read']):
        d.text(x,126,s,9.4,INK,bold=True)
    for a,b in zip(xx,xx[1:]):d.arrow((a+11,98),(b-11,98),c=BLUE)
    d.doc(43,98);d.doc(124,98)
    d.token(213,98,'=',TEAL);d.doc(302,98,TEAL,GREEN);d.token(388,98,'=',TEAL)
    d.text(124,71,'Frozen follow-up F',8.8,BLUE,bold=True)
    d.line((124,59),(388,59),c=TEAL,dash=True)
    for x in (213,388):
        d.line((x,86),(x,59),c=TEAL,dash=True)
    d.text(278,50,'Compare both live views with the same F',8.8,TEAL)
    d.cross(158,25)
    d.text(172,25,'Either differs: inadmissible',9,RED,'left',True)
    d.check(158,11)
    d.text(172,11,'Both match: evaluate the typed predicate',9,TEAL,'left',True)
    d.finish(out)


def results(selected,output,panel):
    height=181
    width=176 if panel==0 else 240
    fig=new(width,height)
    ax=plot_area(fig,(.43 if panel==0 else .38,.34 if panel==0 else .14,.35 if panel==0 else .43,
                     .46 if panel==0 else .72),'x')
    fig.text(.025,.93,'(a) Fixed suites' if panel==0 else '(b) Held-out classes',weight='bold',fontsize=9.8)
    amounts=np.array([int(row['exposed'])/int(row['planned']) for row in selected])
    yy=np.arange(len(selected))
    ax.set(xlim=(-.025,1.04),ylim=(len(yy)-.48,-.52),yticks=yy,yticklabels=[r['label'] for r in selected],
           xticks=[0,.5,1])
    ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.tick_params(axis='y',length=0,labelsize=9.6)
    ax.tick_params(axis='x',labelsize=9.6)
    ax.spines['left'].set_visible(False)
    for y,v,row in zip(yy,amounts,selected):
        c=BLUE if panel==0 else (TEAL if v else RED)
        ax.hlines(y,0,v,color=c,lw=1.65 if panel==0 else 1.3,zorder=3)
        ax.scatter(v,y,marker='o' if v else 'x',s=18,c=c,zorder=4,linewidths=1)
        ax.text(1.055,y,f"{row['exposed']}/{row['planned']}",transform=ax.get_yaxis_transform(),
                ha='left',va='center',fontsize=9.6,color=INK,
                weight='bold' if (v == 0 or v == 1) else 'normal')
    save(fig,output)


def external(rows,output):
    fig=new(393,128)
    ax=plot_area(fig,(.30,.32,.66,.49),'x')
    ys=list(range(len(rows)))
    ax.set(xlim=(-.30,10.45),xticks=range(0,11,2),ylim=(2.58,-.58),yticks=ys,
           yticklabels=[r['pair'].replace('--','–') for r in rows],
           xlabel='Accepted configurations (out of ten)')
    ax.tick_params(axis='y',length=0,labelsize=9.7)
    ax.tick_params(axis='x',labelsize=9.6)
    for j,r in enumerate(rows):
        a,b=(int(r[k]) for k in ('exit_only','host_semantic'))
        assert 0<=a<=10 and 0<=b<=10
        dy=.23 if a==b else 0
        ax.plot([a,b],[j-dy,j+dy],c=RED if a!=b else MUTED,lw=1,zorder=2)
        if a!=b:
            ax.annotate(f'{a} vs {b}',((a+b)/2,j),xytext=(0,8),textcoords='offset points',
                        ha='center',color=RED,weight='bold',fontsize=9.6)
        ax.scatter(a,j-dy,marker='o',facecolors='white',edgecolors=BLUE,s=27,zorder=4,
                   label='Exit-only baseline' if j==0 else None)
        ax.scatter(b,j+dy,marker='s',c=TEAL,s=22,zorder=4,label='Host-semantic oracle' if j==0 else None)
    ax.legend(loc='lower center',bbox_to_anchor=(.51,1),ncol=2,frameon=False,fontsize=9.6)
    save(fig,output)

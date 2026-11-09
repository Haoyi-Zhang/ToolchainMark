"""Rebuild the paper's mechanism schematics at their intended physical size."""
from pathlib import Path
from diagram_core import Figure, BLUE, GRAY, INK, RED

def below(f,x,y,icon,label):
    """Keep multiline labels clear of the glyph at actual print scale."""
    f.icon(icon,x,y)
    f.t(x,y+f.units(19.5)[1],label)

def row_lineage(f):
    f.node(43,39,'grid','Frozen design')
    f.route((57,39),(105,39))
    f.node(121,39,'rows','Relation rows')
    f.route((136,39),(194,39))
    below(f,209,39,'filter','Deterministic\nderivation')
    f.route((224,39),(289,39))
    f.line((289,19),(289,66),color=BLUE,check=True)
    for y,icon,label in [(19,'checkgrid','Paired exposure'),(42,'branch','Held-out selection'),(66,'trace','Diagnostic index')]:
        f.route((289,y),(314,y))
        f.node(329,y,icon,label,side='right')
    f.t(105,85,'Adverse runs stay separate',color=GRAY,style='italic')

def state_isolation(f):
    steps=((39,'B1','build P1'),(118,'B2','build P2'),(198,'X1','read P1'),
           (278,'X2','read P2'),(358,'X1','revisit P1'))
    for x, code, desc in steps:
        f.node(x,45,'binary' if code.startswith('B') else 'key',code)
        f.t(x,73,desc,color=GRAY)
    for left,right in zip(steps,steps[1:]):
        f.route((left[0]+15,45),(right[0]-15,45))
    f.span(198,358,21)
    f.t(277,10,'Both reads of P1 must agree',color=INK)
    f.icon('reject',263,91,color=RED,scale=.65)
    f.t(274,91,'P2 on revisit exposes state bleed',align='left',color=RED)

FIGURES = [('row_lineage', 420, 79), ('state_isolation', 420, 86)]

if __name__ == '__main__':
    for name,w,h in FIGURES:
        f=Figure(dict(media=(w,h),trim=(0,0,0,0),width=w))
        globals()[name](f)
        f.finish(Path(__file__).parent/(name.replace('_','-')+'.pdf'))

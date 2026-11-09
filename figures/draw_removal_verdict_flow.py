"""Build the vector diagram used in the main manuscript."""
from pathlib import Path
from visual_grammar import Diagram, BLUE, RED, MUTED, PALE, GRID

def draw(out):
    d=Diagram(w=408,h=116)
    # One object goes from marked, to visibly stripped, to an extractor result.
    for x,mark in ((61,True),(194,False)):
        d.doc(x,95)
        d.rect(x+3,87,8,8,BLUE if mark else 'white',BLUE if mark else GRID,.75,dash=not mark)
    d.rect(321,88,20,14,PALE,BLUE,.75)
    d.arrow((324,95),(338,95),c=BLUE)
    for x,tag,detail in ((61,'Source admitted','Carrier and payload verified'),
                         (194,'Removal observed','Accepted carrier absent'),
                         (331,'Extract again','Check the rejection kind')):
        d.text(x,74,tag,10,BLUE,bold=True)
        d.text(x,61,detail,9)
    for a,b in ((78,177),(211,315)):
        d.arrow((a,95),(b,95),c=BLUE)
    d.arrow((61,52),(61,43),(91,43),(91,30),c=MUTED,dash=True)
    d.line((194,52),(194,43),(91,43),c=MUTED,dash=True)
    d.text(91,18,'Inadmissible',9.4,MUTED,bold=True)
    d.line((331,52),(331,41),c=BLUE)
    d.arrow((331,41),(232,41),(232,31),c=RED)
    d.arrow((331,41),(350,41),(350,31),c=BLUE)
    d.text(232,18,'Payload: inconsistent',9.3,RED,bold=True)
    d.text(350,18,'Absence rejection: OK',9.3,BLUE,bold=True)
    d.text(43,45,'Fail',8.8,MUTED)
    d.text(212,45,'Fail',8.8,MUTED)
    d.finish(out)

if __name__ == '__main__':
    draw(Path(__file__).with_name('removal-verdict-flow.pdf'))

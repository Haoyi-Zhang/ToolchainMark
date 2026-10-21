"""Direct vector schematics for the declared relation, trace and admission model."""
from pathlib import Path
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

plt.rcParams.update({'font.family': 'STIXGeneral', 'mathtext.fontset': 'stix',
                     'font.size': 9, 'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'text.usetex': False, 'axes.unicode_minus': False})


class Drawing:
    def __init__(self, width, height):
        self.fig = plt.figure(figsize=(width/2.54, height/2.54))
        self.ax = self.fig.add_axes([0, 0, 1, 1], xlim=(0, width), ylim=(0, height))
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.labels = []

    def text(self, x, y, text, size=9, **kw):
        label = self.ax.text(x, y, text, ha='center', va='center',
                             fontsize=size, linespacing=1.15, zorder=4, **kw)
        self.labels.append(label)

    def box(self, x, y, width, height, text='', circle=False):
        patch = Circle((x, y), width/2) if circle else Rectangle((x-width/2, y-height/2), width, height)
        patch.set(edgecolor='black', facecolor='white', linewidth=.65, zorder=2)
        self.ax.add_patch(patch)
        if text:
            self.text(x, y, text)

    def line(self, points, arrow=False, dashed=False):
        xs, ys = zip(*points)
        self.ax.plot(xs, ys, color='black', lw=.65, linestyle='--' if dashed else '-', zorder=1)
        if arrow:
            self.ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle='-|>',
                             mutation_scale=8, lw=.65, color='black', zorder=1))

    def save(self, out, name):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        extent = self.fig.bbox
        for label in self.labels:
            box = label.get_window_extent(renderer)
            if box.x0 < extent.x0 or box.x1 > extent.x1 or box.y0 < extent.y0 or box.y1 > extent.y1:
                raise ValueError('Clipped label: ' + label.get_text())
        self.fig.savefig(out/(name+'.pdf'), metadata={'Creator': 'Python Matplotlib',
                         'Producer': None, 'CreationDate': None, 'ModDate': None})
        plt.close(self.fig)

def motivating(out):
    d = Drawing(16, 5.8)
    xs = [1, 3.2, 5.4, 7.6, 9.8, 12]
    for y, title, artifact, verdict in [
            (4.45, 'Contract-respecting trace', '$a$\ncarrier present', 'Satisfied'),
            (1.45, 'False-assurance trace', '$b$\ncarrier absent', 'Inconsistent')]:
        d.text(4, y+(.83 if y>3 else 1.7), title, 10)
        labels = ['request\n$(H,p,k)$', 'embed', 'compile', artifact,
                  'extract', 'payload $p$']
        for x, label in zip(xs, labels):
            d.ax.plot(x, y, 'ko', ms=2.2)
            d.text(x, y-.46, label, 8.5)
        for left, right in zip(xs, xs[1:]):
            d.line([(left+.14, y), (right-.14, y)], arrow=True)
        d.text(14.45, y-.02, verdict, 9)
    d.line([(3.2, 1.6), (3.2, 2.35), (9.8, 2.35), (9.8, 1.6)], arrow=True, dashed=True)
    d.text(6.5, 2.65, 'undeclared sidecar containing $p$', 8.5)
    d.text(7.6, 4.95, 'authoritative bytes', 8)
    d.line([(12.8, 4.45), (13.05, 4.45), (13.05, 1.45), (12.8, 1.45)])
    d.text(14.35, 2.9, 'same round-trip\nobservation', 8)
    d.text(14.35, .5, 'artifact binding fails', 8)
    d.save(out, 'motivating-counterexample')


def trace(out):
    d = Drawing(15.5, 4.9)
    xs = [1.35, 4.45, 7.55, 10.65, 13.75]
    names = ['Embed', 'Compile', 'Transform', 'Execute', 'Extract']
    obs = ['request\npayload, key', 'requested/actual\ncompiler, flags',
           'intervention\ncertificate', 'host output\nand exit',
           'artifact identity\nand extraction']
    for i, (x, name, evidence) in enumerate(zip(xs, names, obs), 1):
        d.box(x, 4.15, .5, .5, str(i), circle=True)
        d.text(x, 3.6, name, 9)
        d.line([(x, 3.25), (x, 2.75)], dashed=True)
        d.text(x, 2.15, evidence, 8.5)
    for a, b in zip(xs, xs[1:]):
        d.line([(a+.3, 4.15), (b-.3, 4.15)], arrow=True)
    d.line([(xs[0], 2.75), (xs[-1], 2.75)])
    d.line([(xs[0], .85), (xs[-1], .85)], arrow=True)
    d.text(3.5, 1.15, 'source trace $\\tau_s$', 8.5)
    d.text(11.5, 1.15, 'follow-up trace $\\tau_f$', 8.5)
    d.text(7.5, .35, '$R$ selects projection $O_R$', 9)
    d.save(out, 'trace-model')


def architecture(out):
    d = Drawing(15.5, 5.6)
    xs = [1.55, 4.65, 7.75, 10.85, 13.95]
    texts = ['1. Relation\ndeclaration\n\nadmission, polarity,\nprojection',
             '2. Case\nplanning\n\nsource and\nfollow-up requests',
             '3. Isolated\nexecution\n\nfresh workspace\nand process state',
             '4. Evidence\nnormalization\n\ntyped observations\nand certificates',
             '5. Verdict\nand witness\n\nthree-valued\nresult']
    for x, text in zip(xs, texts):
        d.box(x, 3.75, 2.65, 2.7, text)
    for a, b in zip(xs, xs[1:]):
        d.line([(a+1.325, 3.75), (b-1.325, 3.75)], arrow=True)
    for x in xs[1:]:
        d.line([(x, 2.4), (x, 1.7)], dashed=True)
    d.line([(xs[1], 1.7), (xs[-1], 1.7)])
    d.text(9.25, 1.2, 'Immutable evidence record', 9)
    d.text(9.25, .55, 'requests, artifacts, host outputs, extraction results,\nand intervention certificates', 8.5)
    d.save(out, 'architecture')


def evaluation(out):
    d = Drawing(15.3, 6.4)
    d.text(3.5, 5.85, 'Three carrier planes', 10)
    for shift, shade in [(.34, '.65'), (.17, '.4'), (0, '.1')]:
        for x in range(8):
            for y in range(5):
                d.ax.plot(1.8+x*.3+shift, 3.75+y*.28+shift,
                          'o', ms=2.1, color=shade)
    d.line([(1.3, 3.7), (1.3, 5.3)], arrow=True)
    d.text(.8, 4.5, '18 subjects', 8.5, rotation=90)
    d.line([(1.75, 3.4), (4.3, 3.4)], arrow=True)
    d.text(3, 3, '24 fault mechanisms', 8.5)
    d.line([(4.85, 4.45), (5.8, 4.45)], arrow=True)
    d.text(10, 4.45, '$18\\times3\\times24 = 1,296$ units\n14 relations per faulty unit\nplus 756 clean relation executions', 10)
    for x, title, desc, kind in [(2.5, 'Subject replay', 'hold out a row;\nkeep the mechanism', 'row'),
                (7.6, 'Carrier holdout', 'hold out one\nrepresentation plane', 'plane'),
                (12.6, 'Mechanism holdout', 'hold out a column\nor an entire class', 'column')]:
        d.text(x, 2.35, title, 9)
        for i in range(5):
            for j in range(3):
                d.ax.plot(x-.65+i*.32, 1.25+j*.25, 'ko', ms=2)
        if kind == 'row':
            d.ax.plot([x-.8, x+.8], [1.5, 1.5], color='.7', lw=4, zorder=0)
        elif kind == 'column':
            d.ax.plot([x, x], [1.12, 1.9], color='.7', lw=4, zorder=0)
        else:
            d.ax.add_patch(Rectangle((x-.82, 1.1), 1.65, .8, fill=False, lw=1.2, ls='--'))
        d.text(x, .55, desc, 8.5)
    d.save(out, 'evaluation-design')


def coherence(out):
    d = Drawing(14.8, 5.5)
    positions = [(1.8, 4.35), (5.5, 4.35), (9.2, 4.35), (12.9, 4.35),
                 (12.9, 2.25), (9.2, 2.25), (5.5, 2.25)]
    texts = ['capture\nsource $S$', 'intervene;\ncapture $F$',
             'one view:\nlocality + strict\nrejection', 'live bytes $=F$\nbefore extraction',
             'tested\nextraction', 'live bytes $=F$\nafter extraction', 'typed predicate\nand verdict']
    for (x, y), text in zip(positions, texts):
        d.box(x, y, 3.05, 1.45, text)
    for a, b in zip(positions, positions[1:]):
        if a[1] == b[1]:
            sign = 1 if b[0] > a[0] else -1
            d.line([(a[0]+sign*1.525, a[1]), (b[0]-sign*1.525, b[1])], arrow=True)
        else:
            d.line([(a[0], a[1]-.725), (b[0], b[1]+.725)], arrow=True)
    d.text(1.8, 2.25, 'detected change:\ninadmissible', 9)
    d.line([(9.2, 1.525), (9.2, .7), (1.8, .7), (1.8, 1.7)], arrow=True, dashed=True)
    d.save(out, 'snapshot-coherence')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    for draw in (motivating, trace, architecture, evaluation, coherence):
        draw(args.outdir)


if __name__ == '__main__':
    main()

"""Redraw retained evaluation tables as vector PDF; this is not an experiment.

The active categorical comparison is rendered by Matplotlib without a TeX
engine. CSV identities are checked against the retained source snapshot.
No project runner, evaluator, compiler, or network request is invoked.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "artifact/figures"))
from decimal import Decimal
import csv
import io
import math
import re
import struct
import subprocess
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
FAMILY = "libertine"
SNAPSHOTS = {
  "figures/external-transfer.csv": "pair,exit_only,host_semantic\nNewton--Raphson,10,10\nClustering,10,0\nWeighted mean,10,10\n"
}
CHARTS = [
  {
    "name": "external-transfer",
    "size": [
      334.15,
      135
    ],
    "box": [
      40,
      22,
      289.3,
      96.9
    ],
    "font": 8.47,
    "left_axes": True,
    "xlim": [
      0.6,
      3.4
    ],
    "ylim": [
      -0.2,
      10.8
    ],
    "xticks": [
      [
        1,
        "Newton–Raphson"
      ],
      [
        2,
        "Clustering"
      ],
      [
        3,
        "Weighted mean"
      ]
    ],
    "yticks": [
      [
        0,
        "0"
      ],
      [
        2,
        "2"
      ],
      [
        4,
        "4"
      ],
      [
        6,
        "6"
      ],
      [
        8,
        "8"
      ],
      [
        10,
        "10"
      ]
    ],
    "ylabel": "comparisons accepted (of 10)",
    "ylabel_x": 8,
    "series": [
      {
        "csv": "figures/external-transfer.csv",
        "x": "pair",
        "y": "exit_only",
        "categorical": True,
        "style": {
          "gray": 0.5,
          "marker": "open",
          "thickness": 0.65
        }
      },
      {
        "csv": "figures/external-transfer.csv",
        "x": "pair",
        "y": "host_semantic",
        "categorical": True,
        "style": {
          "marker": "circle",
          "thickness": 0.85
        }
      }
    ],
    "legend": {
      "items": [
        {
          "label": "exit-only baseline",
          "gray": 0.5,
          "marker": "open"
        },
        {
          "label": "host-semantic oracle",
          "marker": "circle"
        }
      ],
      "x": 52,
      "y": 128,
      "columns": 2
    }
  }
]
ROOT = HERE.parent


def tex_file(name):
    result = subprocess.run(["kpsewhich", name], check=True,
                            capture_output=True, text=True)
    path = Path(result.stdout.strip())
    if not result.stdout.strip() or not path.is_file():
        raise FileNotFoundError(name)
    return str(path)


class LibertineFace(pdfmetrics.EmbeddedType1Face):
    def _loadMetrics(self, tfm_path):
        data = Path(tfm_path).read_bytes()
        lf, lh, bc, ec, nw, nh, nd, ni, nl, nk, ne, np = struct.unpack(">12H", data[:24])
        if len(data) != 4 * lf or not (bc <= 0x15 and ec >= 126 and np >= 2):
            raise ValueError("Unexpected Libertine T1 metric layout.")
        start = 24 + 4 * lh
        widths_start = start + 4 * (ec - bc + 1)
        widths = struct.unpack(">" + "i" * nw,
                               data[widths_start:widths_start + 4 * nw])
        params_start = widths_start + 4 * (nw + nh + nd + ni + nl + nk + ne)
        space = struct.unpack(">i", data[params_start + 4:params_start + 8])[0]
        encoding = pdfmetrics.getEncoding("WinAnsiEncoding")
        self.glyphWidths = {}
        for code in range(32, 127):
            index = data[start + 4 * (code - bc)]
            width = space if code == 32 else widths[index]
            self.glyphWidths[encoding[code]] = 1000 * width / 2**20
        # Libertine T1/Cork slot 0x15 is /endash (WinAnsi uses byte 150).
        index = data[start + 4 * (0x15 - bc)]
        self.glyphWidths["endash"] = 1000 * widths[index] / 2**20
        self.glyphNames = sorted(self.glyphWidths)
        header = self._binaryData[:self._length1].decode("ascii")
        self.name = re.search(r"/FontName\s+/(\S+)", header).group(1)
        self.familyName = "Linux Libertine"
        bbox = re.search(r"/FontBBox\s*[{\[]\s*([^}\]]+)", header).group(1)
        self.bbox = [int(float(v)) for v in bbox.split()]
        self.ascent, self.descent = self.bbox[3], self.bbox[1]
        self.capHeight, self.xHeight, self.stemV = 643, 429, 79
        self.italicAngle = float(re.search(r"/ItalicAngle\s+([-\d.]+)", header).group(1))


def register_fonts(family):
    if family == "times":
        for alias, stem in [("Body", "utmr8a"), ("Variable", "utmri8a")]:
            face = pdfmetrics.EmbeddedType1Face(tex_file(stem + ".afm"),
                                              tex_file(stem + ".pfb"))
            pdfmetrics.registerTypeFace(face)
            pdfmetrics.registerFont(pdfmetrics.Font(alias, face.name, "WinAnsiEncoding"))
    else:
        for alias, stem in [("Body", "LinLibertineT"), ("Variable", "LinLibertineTI")]:
            face = LibertineFace(tex_file(stem + "-lf-t1.tfm"),
                                 tex_file(stem + ".pfb"))
            pdfmetrics.registerTypeFace(face)
            pdfmetrics.registerFont(pdfmetrics.Font(alias, face.name, "WinAnsiEncoding"))


def read_rows(path):
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    delimiter = "\t" if path.endswith(".tsv") else ","
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delimiter))
    expected = list(csv.DictReader(io.StringIO(SNAPSHOTS[path]), delimiter=delimiter))
    if rows != expected:
        raise ValueError("Retained CSV changed: " + path)
    return rows


def points(spec):
    rows = read_rows(spec["csv"])
    result = []
    for i, row in enumerate(rows):
        raw_x = row[spec["x"]]
        x = Decimal(i + 1) if spec.get("categorical") else Decimal(raw_x)
        if "domain" in spec and not spec["domain"][0] <= x <= spec["domain"][1]:
            continue
        if row[spec["y"]] == "" or row[spec["y"]].lower() == "nan":
            if spec.get("omit_missing"):
                continue
            raise ValueError("Missing executed value must not become a point.")
        y = Decimal(row[spec["y"]])
        if not y.is_finite():
            raise ValueError("Non-finite plot coordinate.")
        y /= Decimal(str(spec.get("y_divisor", 1)))
        result.append((float(x), float(y), row))
    return result


class Plot:
    def __init__(self, cfg):
        self.cfg = cfg
        w, h = cfg["size"]
        self.c = canvas.Canvas(str(HERE / (cfg["name"] + ".pdf")),
                               pagesize=(w, h), invariant=True,
                               initialFontName="Body")
        self.fontsize = cfg.get("font", 9)
        self.c.setFont("Body", self.fontsize)
        self.left, self.bottom, self.width, self.height = cfg["box"]
        self.axes()

    def xy(self, x, y):
        def ratio(v, bounds, logarithmic):
            if logarithmic:
                v, bounds = math.log10(v), [math.log10(a) for a in bounds]
            return (v - bounds[0]) / (bounds[1] - bounds[0])
        return (self.left + self.width * ratio(x, self.cfg["xlim"], self.cfg.get("xlog", False)),
                self.bottom + self.height * ratio(y, self.cfg["ylim"], self.cfg.get("ylog", False)))

    def label(self, x, y, text, anchor="center", angle=0, font="Body"):
        c = self.c
        c.saveState()
        c.translate(x, y)
        c.rotate(angle)
        c.setFillGray(0)
        c.setFont(font, self.fontsize)
        if isinstance(text, dict) and "parts" in text:
            parts = text["parts"]
            width = sum(pdfmetrics.stringWidth(t, f, self.fontsize) for f, t in parts)
            xx = -width/2 if anchor == "center" else -width if anchor == "right" else 0
            for face, string in parts:
                c.setFont(face, self.fontsize)
                c.drawString(xx, 0, string)
                xx += pdfmetrics.stringWidth(string, face, self.fontsize)
        else:
            {"center": c.drawCentredString, "right": c.drawRightString,
             "left": c.drawString}[anchor](0, 0, text)
        c.restoreState()

    def axes(self):
        c, cfg = self.c, self.cfg
        x0, y0 = cfg["xlim"][0], cfg["ylim"][0]
        c.setStrokeGray(.82)
        c.setLineWidth(.3)
        for x, label in cfg["xticks"]:
            px, _ = self.xy(x, y0)
            if cfg.get("xgrid", True):
                c.line(px, self.bottom, px, self.bottom + self.height)
            rotation = cfg.get("xrotation", 0)
            self.label(px, self.bottom - 12, label,
                       anchor="right" if rotation else "center", angle=rotation)
        for y, label in cfg["yticks"]:
            _, py = self.xy(x0, y)
            c.line(self.left, py, self.left + self.width, py)
            if isinstance(label, dict) and "power" in label:
                base, exponent = "10", str(label["power"])
                c.saveState()
                c.setFillGray(0)
                c.setFont("Body", self.fontsize)
                ew = pdfmetrics.stringWidth(exponent, "Body", self.fontsize * .72)
                bw = pdfmetrics.stringWidth(base, "Body", self.fontsize)
                xx, yy = self.left - 6 - ew - bw, py - self.fontsize * .32
                c.drawString(xx, yy, base)
                c.setFont("Body", self.fontsize * .72)
                c.drawString(xx+bw, yy+4, exponent)
                c.restoreState()
            else:
                self.label(self.left - 6, py - self.fontsize * .32, label, anchor="right")
        c.setStrokeGray(0)
        c.setLineWidth(.5)
        if cfg.get("left_axes"):
            c.line(self.left, self.bottom, self.left + self.width, self.bottom)
            c.line(self.left, self.bottom, self.left, self.bottom + self.height)
        else:
            c.rect(self.left, self.bottom, self.width, self.height)
        if cfg.get("xlabel"):
            self.label(self.left + self.width / 2, cfg.get("xlabel_y", 5), cfg["xlabel"])
        if cfg.get("ylabel_lines"):
            for n, label in enumerate(cfg["ylabel_lines"]):
                self.label(6 + n * 11, self.bottom + self.height / 2, label, angle=90)
        if cfg.get("ylabel"):
            self.label(cfg.get("ylabel_x", 9), self.bottom + self.height / 2,
                       cfg["ylabel"], angle=90)

    def line(self, values, dash=(), gray=0, marker=None, markers_every=1, thickness=.8, stepped=False):
        c = self.c
        c.setStrokeGray(gray)
        c.setLineWidth(thickness)
        c.setDash(dash)
        p = c.beginPath()
        for i, (x, y, _) in enumerate(values):
            if i == 0:
                p.moveTo(*self.xy(x, y))
            else:
                if stepped:
                    p.lineTo(*self.xy(x, values[i-1][1]))
                p.lineTo(*self.xy(x, y))
        c.drawPath(p)
        c.setDash()
        if marker:
            for i, (x, y, _) in enumerate(values):
                if i % markers_every == 0:
                    self.mark(*self.xy(x, y), marker, gray)

    def mark(self, x, y, marker="circle", gray=0, size=1.9):
        c = self.c
        c.setDash()
        c.setLineWidth(.65)
        c.setStrokeGray(gray)
        c.setFillGray(1 if marker in ("open", "open_square", "open_triangle") else gray)
        if marker in ("circle", "open"):
            c.circle(x, y, size, fill=1)
        elif marker in ("square", "open_square"):
            c.rect(x-size, y-size, 2*size, 2*size, fill=1)
        elif marker in ("triangle", "open_triangle"):
            p = c.beginPath()
            p.moveTo(x, y+size)
            p.lineTo(x-size, y-size)
            p.lineTo(x+size, y-size)
            p.close()
            c.drawPath(p, fill=1)
        elif marker == "diamond":
            p = c.beginPath()
            p.moveTo(x, y+size)
            p.lineTo(x-size, y)
            p.lineTo(x, y-size)
            p.lineTo(x+size, y)
            p.close()
            c.drawPath(p, fill=1)
        c.setFillGray(0)

    def reference(self, x=None, y=None):
        c = self.c
        c.setStrokeGray(.35)
        c.setLineWidth(.6)
        c.setDash(3, 2)
        if x is not None:
            px, _ = self.xy(x, self.cfg["ylim"][0])
            c.line(px, self.bottom, px, self.bottom + self.height)
        else:
            _, py = self.xy(self.cfg["xlim"][0], y)
            c.line(self.left, py, self.left + self.width, py)
        c.setDash()

    def bars(self, values, width, shift=0, gray=.3, annotation=None):
        c = self.c
        baseline = self.cfg["ylim"][0] if self.cfg.get("ylog") else 0
        for x, y, row in values:
            px, py = self.xy(x, y)
            _, bottom = self.xy(x, baseline)
            c.setStrokeGray(0)
            c.setFillGray(gray)
            c.setLineWidth(.45)
            c.rect(px+shift-width/2, bottom, width, py-bottom, fill=1)
            c.setFillGray(0)
            if annotation:
                label = row[annotation] if annotation != "_2dp" else format(y, ".2f")
                self.label(px+shift, py+5, label)

    def legend(self, items, x, y, columns=1, step=12):
        c = self.c
        widths = [30 + pdfmetrics.stringWidth(i["label"], "Body", self.fontsize) for i in items]
        column_width = max(widths) + 10
        for n, item in enumerate(items):
            xx, yy = x + (n % columns) * column_width, y - (n // columns) * step
            c.setStrokeGray(item.get("gray", 0))
            c.setLineWidth(item.get("thickness", .8))
            if item.get("bar"):
                c.setFillGray(item.get("gray", .3))
                c.rect(xx, yy-2, 16, 5, fill=1)
            else:
                c.setDash(item.get("dash", ()))
                c.line(xx, yy, xx+18, yy)
                c.setDash()
                if item.get("marker"):
                    self.mark(xx+9, yy, item["marker"], item.get("gray", 0))
            self.label(xx+24, yy-2.5, item["label"], anchor="left")
        c.setFillGray(0)

    def finish(self):
        self.c.showPage()
        self.c.save()


def render(cfg):
    if cfg["name"] == "external-transfer":
        from toolchain_panels import external
        external(read_rows("figures/external-transfer.csv"),HERE/"external-transfer.pdf")
        return
    plot = Plot(cfg)
    for series in cfg.get("series", []):
        values = points(series)
        style = series.get("style", {})
        if series.get("kind") == "bar":
            plot.bars(values, **style)
        elif series.get("kind") == "scatter":
            for x, y, row in values:
                px, py = plot.xy(x, y)
                plot.mark(px, py, marker=style.get("marker", "circle"),
                          gray=style.get("gray", 0), size=style.get("size", 2.3))
                if "label" in series:
                    plot.label(px+5, py-2.5, row[series["label"]], anchor="left")
        elif series.get("kind") == "interval":
            for x, y, row in values:
                low, high = Decimal(row["lower"]), Decimal(row["upper"])
                a, b = plot.xy(float(low), y), plot.xy(float(high), y)
                plot.c.setStrokeGray(0)
                plot.c.setLineWidth(1.4)
                plot.c.line(*a, *b)
                for px, py in (a, b):
                    plot.c.line(px, py-3, px, py+3)
                plot.mark(*plot.xy(float(Decimal(row["observed"])), y))
        else:
            plot.line(values, **style)
    for ref in cfg.get("references", []):
        plot.reference(**ref)
    if "legend" in cfg:
        plot.legend(**cfg["legend"])
    plot.finish()


def main():
    for chart in CHARTS:
        if chart["name"] != "external-transfer":
            register_fonts(FAMILY)
        render(chart)


if __name__ == "__main__":
    main()

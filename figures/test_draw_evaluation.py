"""Font-consumer regressions; retained CSVs are read, never remeasured."""
import struct
import unittest
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
import draw_evaluation as drawing


class EvaluationFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        drawing.register_fonts("libertine")

    def test_current_tick_characters_have_positive_advance(self):
        for chart in drawing.CHARTS:
            for _, label in chart["xticks"]:
                for char in label:
                    with self.subTest(label=label, char=char):
                        self.assertGreater(pdfmetrics.stringWidth(char, "Body", chart["font"]), 0)

    def test_endash_uses_t1_width_in_both_existing_faces(self):
        for alias, stem in [("Body", "LinLibertineT"), ("Variable", "LinLibertineTI")]:
            data = Path(drawing.tex_file(stem + "-lf-t1.tfm")).read_bytes()
            _, lh, bc, ec, nw, *_ = struct.unpack(">12H", data[:24])
            start = 24 + 4 * lh
            widths_start = start + 4 * (ec - bc + 1)
            widths = struct.unpack(">" + "i" * nw, data[widths_start:widths_start + 4 * nw])
            # The bundled Libertine T1 encoding assigns /endash to slot 0x15.
            expected = widths[data[start + 4 * (0x15 - bc)]] / 2**20
            with self.subTest(face=alias):
                self.assertEqual(pdfmetrics.getFont(alias).face.name, stem)
                self.assertGreater(expected, 0)
                self.assertAlmostEqual(pdfmetrics.stringWidth("–", alias, 1), expected)
                self.assertAlmostEqual(pdfmetrics.stringWidth("Newton–Raphson", alias, 1),
                                       pdfmetrics.stringWidth("NewtonRaphson", alias, 1) + expected)


if __name__ == "__main__":
    unittest.main()

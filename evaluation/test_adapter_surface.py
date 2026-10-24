import tempfile
from pathlib import Path
import unittest
from adapter_surface import GROUPS,measure,table

class Surface(unittest.TestCase):
    def test_all_declared_files_measured(self):
        rows=measure()
        self.assertEqual(len(rows),5)
        self.assertEqual(sum(x['files'] for x in rows),7)
        self.assertTrue(all(x['nonblank_lines']>0 and x['function_definitions']>0 for x in rows))
    def test_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):measure(Path(tmp))
    def test_table_has_every_component_once(self):
        text=table()
        self.assertEqual(len(text.splitlines()),6)
        for label in GROUPS:self.assertEqual(text.count(label+' &'),1)

if __name__=='__main__':unittest.main()

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from adapter_surface import GROUPS,measure,table
import verify_native_records

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

    def check_display(self, content):
        with tempfile.TemporaryDirectory(prefix='adapter-display-') as tmp:
            paper=Path(tmp)
            path=paper/'generated/adapter-surface.tex'
            path.parent.mkdir()
            path.write_bytes(content)
            verify_native_records.verify_adapter_surface(paper)

    def test_consumed_display_matches_current_ast(self):
        self.check_display(table().encode('utf-8'))

    def test_platform_line_endings_do_not_change_display(self):
        self.check_display(table().replace('\n','\r\n').encode('utf-8'))

    def test_stale_display_counts_are_rejected(self):
        row=next(x for x in measure() if x['component']=='Relations and admission')
        current=f"Relations and admission & {row['files']} & {row['nonblank_lines']} & {row['function_definitions']}"
        for stale in (
                f"Relations and admission & {row['files']} & {row['nonblank_lines']-1} & {row['function_definitions']}",
                f"Relations and admission & {row['files']} & {row['nonblank_lines']} & {row['function_definitions']-1}"):
            with self.subTest(stale=stale), self.assertRaisesRegex(ValueError,'adapter-surface.tex'):
                self.check_display(table().replace(current,stale).encode('utf-8'))

    def test_malformed_incomplete_or_extra_display_is_rejected(self):
        expected=table().encode('utf-8')
        for content in (b'', b'not a TeX surface table\n',
                        b'\n'.join(expected.splitlines()[:-1])+b'\n',
                        expected+b'% unexpected display content\n'):
            with self.subTest(content=content), self.assertRaisesRegex(ValueError,'adapter-surface.tex'):
                self.check_display(content)
        with self.assertRaises(UnicodeError):
            self.check_display(b'\xff')

    def test_missing_display_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='adapter-display-') as tmp:
            with self.assertRaises(FileNotFoundError):
                verify_native_records.verify_adapter_surface(Path(tmp))

    def test_paper_cli_rejects_stale_display_before_data_derivation(self):
        with tempfile.TemporaryDirectory(prefix='adapter-display-') as tmp:
            paper=Path(tmp)
            path=paper/'generated/adapter-surface.tex'
            path.parent.mkdir()
            stale=b'% stale consumed display\n'
            path.write_bytes(stale)
            for write_flag in ([],['--write-paper']):
                with self.subTest(write_flag=write_flag), \
                        patch('sys.argv',['verify_native_records.py','--paper',str(paper),*write_flag]), \
                        patch.object(verify_native_records,'verify_native_source_binding') as native:
                    with self.assertRaisesRegex(ValueError,'adapter-surface.tex'):
                        verify_native_records.main()
                    native.assert_not_called()
                    self.assertEqual(path.read_bytes(),stale)

if __name__=='__main__':unittest.main()

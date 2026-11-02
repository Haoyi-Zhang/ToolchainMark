"""Bundle only small public catalogs; never include retained research datasets."""
from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildCatalogs(build_py):
    def run(self):
        super().run()
        target = Path(self.build_lib) / 'tosem02' / 'data'
        target.mkdir(parents=True, exist_ok=True)
        for name in ('mrspec.json', 'mutants.json', 'evidence_relations.json'):
            shutil.copyfile(Path(__file__).parent / 'specs' / name, target / name)


setup(cmdclass={'build_py': BuildCatalogs})

"""Static integration surfaces, not measurements of human effort or transfer."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GROUPS={
    'Reference pipeline':('src/tosem02/pipeline.py',),
    'Relations and admission':('src/tosem02/relations.py','src/tosem02/admission.py'),
    'Record and integrity observation':('src/tosem02/record.py','src/tosem02/integrity.py'),
    'Owned object adapter':('owned_native_tool/adapter.py',),
    'Owned object tool':('owned_native_tool/tool.py',),
}

def measure(root=ROOT):
    rows=[]
    for label,paths in GROUPS.items():
        lines=functions=0
        for relative in paths:
            source=(root/relative).read_text(encoding='utf-8')
            tree=ast.parse(source,filename=relative)
            lines+=sum(bool(line.strip()) for line in source.splitlines())
            functions+=sum(isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) for node in ast.walk(tree))
        rows.append({'component':label,'files':len(paths),'nonblank_lines':lines,'function_definitions':functions,'paths':list(paths)})
    return rows

def table():
    rows=measure()
    return '% Current static source surface; nonblank lines include comments/docstrings.\n'+''.join(
        f"{x['component']} & {x['files']} & {x['nonblank_lines']} & {x['function_definitions']} \\\\\n" for x in rows)

if __name__=='__main__':print(table(),end='')

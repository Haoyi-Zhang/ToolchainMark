from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any


def artifact_root() -> Path:
    return checkout_root()


def checkout_root(root: Path | None = None) -> Path:
    candidate = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[2]
    if not all((candidate / name).is_dir() for name in ('specs', 'scripts', 'hosts', 'src/tosem02')):
        raise ValueError('This operation needs an artifact checkout; supply --artifact-root PATH. '
                         'The installed wheel contains catalogs, not campaigns or retained datasets.')
    return candidate


def load_document(name: str) -> dict:
    if name not in {'mrspec.json', 'mutants.json', 'evidence_relations.json'}:
        raise ValueError('unknown catalog')
    bundled = resources.files('tosem02').joinpath('data', name)
    if bundled.is_file():
        return json.loads(bundled.read_text(encoding='utf-8'))
    return json.loads((checkout_root() / 'specs' / name).read_text(encoding='utf-8'))


def load_relations() -> list[dict[str, Any]]:
    data = load_document('mrspec.json')
    return data['relations']


def load_mutants() -> list[dict[str, Any]]:
    data = load_document('mutants.json')
    return data['mutants']


def relation_map() -> dict[str, dict[str, Any]]:
    return {row['id']: row for row in load_relations()}


def mutant_map() -> dict[str, dict[str, Any]]:
    return {row['id']: row for row in load_mutants()}

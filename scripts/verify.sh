#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT/src"
cd "$ROOT"
python3 scripts/verify_package.py
python3 -m unittest discover -s tests -v
python3 -m tosem02.cli derive
python3 scripts/audit_references.py
python3 scripts/generate_ledgers.py
python3 -m tosem02.cli recheck
python3 scripts/verify_package.py

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python prepare_source.py
python strap-density-study/end-shell-audit/cuts.py
python strap-density-study/end-shell-audit/loops.py
python strap-density-study/end-shell-audit/split_paths.py
python normalize_paths.py
python strap-density-study/end-shell-audit/paint_boundary.py
python strap-density-study/end-shell-audit/export_interfaces.py
python strap-density-study/shell/build_ordered.py
python strap-density-study/shell/stitch_ordered.py
python strap-density-study/shell/attributes_ordered.py
python save_actual.py
python export_provenance.py
python retained_actual_audit.py

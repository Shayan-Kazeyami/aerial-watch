#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python prepare_source.py
for n in cuts loops split_paths;do python strap-density-study/end-shell-audit/$n.py;done
python normalize_paths.py
for n in export_interfaces paint_boundary;do python strap-density-study/end-shell-audit/$n.py;done
for n in build_uv stitch_uv;do PYTHONPATH=/tmp/strap-remesh-deps python strap-density-study/shell/$n.py;done
python fair_cap_fem.py
PYTHONPATH=/tmp/strap-remesh-deps python strap-density-study/shell/attributes_uv.py

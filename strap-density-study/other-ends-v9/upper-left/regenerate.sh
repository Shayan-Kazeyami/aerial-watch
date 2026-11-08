#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python prepare_source.py
# Input canonical arrays are actual upper-left source reflected X, winding reversed.
for n in cuts loops split_paths export_interfaces paint_boundary; do python strap-density-study/end-shell-audit/$n.py; done
# Own path ordering verified low-Z -> high-Z outer profile; bottom is inverse.
# Own bottom material-1 interval is edges16..23, not upper-right edges20..25.
for n in build_ordered stitch_ordered attributes_ordered; do PYTHONPATH=/tmp/strap-remesh-deps python strap-density-study/shell/$n.py; done
python export_actual.py

#!/usr/bin/env bash
set -euo pipefail
# Run from workspace root, after own-source wide-v13 geometry and
# material-boundary-study/loft-param-triangles.npz have been regenerated.
python strap-density-study/wide-uv14/source_domains.py
python strap-density-study/wide-uv14/project_loft_numpy.py
python strap-density-study/wide-uv14/transfer.py
python strap-density-study/wide-uv14/pslg.py
python strap-density-study/wide-uv14/repair_chart_slivers.py
python strap-density-study/wide-uv14/exact_interface_uv.py
python strap-density-study/wide-uv14/topology.py
python strap-density-study/wide-uv14/interface_check.py

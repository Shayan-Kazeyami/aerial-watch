#!/usr/bin/env bash
set -euo pipefail
python strap-density-study/wide-uv14-lower-left/loft_params.py
python strap-density-study/wide-uv14-lower-left/source_domains.py
python strap-density-study/wide-uv14-lower-left/project_loft_numpy.py
python strap-density-study/wide-uv14-lower-left/transfer.py
python strap-density-study/wide-uv14-lower-left/pslg.py
python strap-density-study/wide-uv14-lower-left/coalesce_chart_knots.py
python strap-density-study/wide-uv14-lower-left/repair_chart_slivers.py
python strap-density-study/wide-uv14-lower-left/exact_interface_uv.py
python strap-density-study/wide-uv14-lower-left/topology.py
python strap-density-study/wide-uv14-lower-left/interface_check.py
python strap-density-study/wide-uv14-lower-left/quality.py

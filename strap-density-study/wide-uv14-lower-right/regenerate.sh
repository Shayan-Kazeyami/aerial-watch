#!/usr/bin/env bash
set -euo pipefail
python strap-density-study/wide-uv14-lower-right/loft_params.py
python strap-density-study/wide-uv14-lower-right/source_domains.py
python strap-density-study/wide-uv14-lower-right/project_loft_numpy.py
python strap-density-study/wide-uv14-lower-right/transfer.py
python strap-density-study/wide-uv14-lower-right/pslg.py
python strap-density-study/wide-uv14-lower-right/repair_chart_slivers.py
python strap-density-study/wide-uv14-lower-right/exact_interface_uv.py
python strap-density-study/wide-uv14-lower-right/topology.py
python strap-density-study/wide-uv14-lower-right/interface_check.py
python strap-density-study/wide-uv14-lower-right/quality.py

#!/usr/bin/env bash
set -euo pipefail
python strap-density-study/wide-uv14-upper-right/loft_params.py
python strap-density-study/wide-uv14-upper-right/source_domains.py
python strap-density-study/wide-uv14-upper-right/project_loft_numpy.py
python strap-density-study/wide-uv14-upper-right/transfer.py
python strap-density-study/wide-uv14-upper-right/pslg.py
python strap-density-study/wide-uv14-upper-right/repair_chart_slivers.py
python strap-density-study/wide-uv14-upper-right/exact_interface_uv.py
python strap-density-study/wide-uv14-upper-right/topology.py
python strap-density-study/wide-uv14-upper-right/interface_check.py
python strap-density-study/wide-uv14-upper-right/quality.py

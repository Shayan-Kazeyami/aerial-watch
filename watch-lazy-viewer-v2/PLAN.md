# Prepared V2, not browser-executed
The original 298-file closure is validated before any clone; QA_CLOSURE.json explicitly declares the identical review instrumentation plus candidate-only helper replacement. Original manifests/bootstrap stay unchanged; copies are labeled QA overlays, not immutable releases.

`python run_all.py` materializes fresh roots and runs baseline-normal, baseline-fault, candidate-normal, candidate-fault in separate sandboxed browser processes, with 1000-second asyncio and 1080-second process-group ceilings. No reuse of existing outputs. Local server lifetime is bounded per arm and killed afterward. Dependencies: Python Playwright plus installed Chromium. This file is a preparation, not run authorization.

Hook removes its Three.js listener explicitly before invoking dispose. Hook and driver both require nonloading/nonfailed/nonlost/non-disposed interactive WebGL2. Normal ensures reuse the actual dial factory/loaded scene; fault injection uses the actual Three added event. Each screenshot records loaded viewer state, but hidden legacy dial creation under premium does not establish visible dial parity. Real pixel parity remains separate. No GPU memory, user-trigger incidence, phone or deployment claims.

Static validation: Python compile, node syntax, exact source pins and original closure validation pass. Browser runner has NOT run. Independent review required.

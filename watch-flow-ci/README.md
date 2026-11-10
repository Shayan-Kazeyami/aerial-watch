# Atelier navigation release checks

The published viewer is the immutable release `preview-b/releases/99d5275244fdabbc301fba262d59e612e7f511121e5e79a5dae5bf936e222e75/`.

The three source modules here match that release. Run `node --test watch-flow-ci/tests/*.test.mjs` for the 31 navigation, restored-state, task-feedback and capture-handoff regressions. `.github/workflows/navigation-release.yml` verifies every immutable local/reference identity, preserves the crown module identities, and exercises desktop/mobile flows in Chromium SwiftShader. It produces actual-render screenshots and reports, without claiming hardware GPU or physical-device coverage.

`qa.py` expects `watch-flow-output/build.json` to identify the staged release; the workflow creates that file. The earlier experimental builder remains on `qa/atelier-navigation-20261110`, not in this publication harness.

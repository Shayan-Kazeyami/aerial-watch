# Aerial Watch source-only candidate backup

This is a source-only backup, not a deployment or production release. It contains exact changed/new first-party source and source manifests for candidate release f22b8870c9f64c522918f0c4e372fcbd9617accfc33b4fb420a56291dcc8ab10. No CAD/GLB binaries, textures, third-party vendor libraries, screenshots, execution logs, tracking spreadsheets, private notes, credentials or workflows are included. Existing attribution and licensing remain unchanged.

The immutable source base is bfbaaf3576738da1930718602031607bbc6d5b57a1a504fd5c231be3ccc160c0. Its complete asset/source closure is preserved by GitHub Actions run 43681147390, artifact 14148715516 (`exact-linux-g317-payload`), ZIP SHA-256 `0ff8a95043d22364866cbbdeb4af5ffb90976986f95f5c9bec44ce62265e2c8b`. Provision and verify that exact base and referenced assets separately before applying this delta. This folder cannot run by itself.

`runtime/` paths are release-relative. `bootstrap/` contains root entry source files. The baseline and candidate deployment manifests pin the complete intended asset closures; this backup includes only the source delta. No absent release receipt is fabricated.

Validation is limited to local real-Three geometry, exact expanded attributes/triangle ordering, selected material/inspection subsystems, ownership tests and immutable source identities. Selected attached geometry arrays are 593,012 bytes smaller in the tested fixture. This is not a peak-memory, GPU, frame-rate, visibility or device result. Actual browser/PBR, physical attachment/clearance and production-adoption gates remain open. Do not infer full-project completion.

Run `python VERIFY_SOURCE.py` to check every bundled source file against `MANIFEST.json`. This bundle contains no workflows or deployment scripts.

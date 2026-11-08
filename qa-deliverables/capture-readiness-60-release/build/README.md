# Private capture-readiness successor builder

No publication, branch or main changes are performed by these scripts.

## Invocation in the full repository

```sh
node qa-deliverables/capture-readiness-60-release/build/build-release.mjs
```

Defaults:
- Owner: `preview-b/releases/a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473`
- Output: `preview-b`
- Receipt: `capture-readiness-60-output/sealed-release.json`
- Rollback main: `77989272c971724b90c932c48d4f769573c933a5`

The builder requires `build-release.mjs` and `patches.json` together. It imports the existing strict release utilities under `metal-recovery/integration-study/release-tools/`: all five `scripts/*.mjs` files plus `assembly-structural-support.js`. Keep these paths unchanged. Complete historical owner inventories must exist in the CI checkout. The local unpacked a8c129 artifact alone is not a complete historical-owner graph; do not bypass owner validation to make it seal locally.

## Exact scope

The only application change is one uniquely anchored `atelier-preview.js` capture-readiness timeout from 10000 to 60000 milliseconds. Its patch bytes are pinned by SHA256; the anchor must occur exactly once. Import-owner paths are checked unchanged. Frame acknowledgement, dimensions, stability, cancellation and cleanup guards remain untouched.

The builder updates build-transformed capture revision metadata and adds a scoped shared-build receipt. It preserves the existing transmission-budget metadata and all other application/asset buffers.

Exactly four sealed local paths change:
1. `atelier-preview.js`
2. `quality-study/viewer-revision.js`
3. `quality-study/viewer-revision.json`
4. `shared-release-build.json`

All 152 other local files, including all four transmission-budget modules and the UV15 geometry/maps, remain byte-identical. All 120 reference entries are preserved. The expected geometry is 8,579,970 bytes with SHA256 `8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7`.

## Local proof

```sh
node qa-deliverables/capture-readiness-60-release/build/test-transform.mjs
```

This passed against the locally unpacked exact a8c129 owner. It independently reconstructs the editable candidate from the previous tested source and proves its application SHA256 equals `9fa6ab550905e783fcc515b6764fa5ce92043d00035083d0865b1a8eb93516c1`. It rejects missing/duplicate anchors, compares every transformed buffer, verifies the exact four changed paths, checks unchanged references and validates the regenerated runtime revision file hashes and digest. Evidence is `transform-proof.json`.

This proof is not a full release seal, native screenshot acceptance, cross-origin export gate or live verification. The receipt explicitly retains `promotionAllowed: false`; publication remains root-owned after the requested sealed gates and review.

This is a distinct 60-second candidate. The previous 30-second builder and evidence are preserved unchanged. Neither candidate is authorized for publication by this builder.

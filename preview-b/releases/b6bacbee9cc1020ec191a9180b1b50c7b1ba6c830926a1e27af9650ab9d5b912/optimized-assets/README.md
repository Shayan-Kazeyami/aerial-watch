# Opt-in lossless delivery candidate

This folder changes storage, not visual quality. Native/source GLBs remain untouched.
Only `assets=meshopt` wiring opts into these variants; other assets/defaults stay raw.

| Original asset | Original bytes | Candidate bytes | Reduction |
|---|---:|---:|---:|
| rebuild/assembly.glb | 26,126,492 | 8,055,333 (explicit gzip) | 69.17% |
| premium-face/face-svg04.glb | 5,910,464 | 3,094,636 | 47.64% |
| quality-study/leather-craft-r11.glb | 10,026,592 | 8,492,276 | 15.30% |

`audit.json` records source/output SHA-256, every original bufferView hash,
codec identity, byte counts, local CPU measurements, and same-implementation
transport-compression comparisons. HTTP encoding is unknown; these are not browser
load-time, frame-rate, WebGPU, or GPU-memory claims.

## Reproduce and verify

```
node scripts/build-lossless-assets.mjs
node scripts/verify-lossless-assets.mjs
node --test tests/optimized-loading.test.mjs tests/lossless-assets.test.mjs tests/gzip-delivery.test.mjs
```

Codec is pinned official meshoptimizer v1.0, MIT; `vendor/meshopt/PROVENANCE.json`
records immutable commit and source hashes. Build checks those hashes first.
No package install or network access is needed. Build uses ATTRIBUTES v0 / NONE
and INDICES sequence; no reordering, quantization, simplification, texture encoding,
material editing, transform changes, or geometry regeneration. Smaller views remain
raw when compression would not cover a conservative metadata allowance.

Every serialized view is decoded and byte-compared, including all five R11 image
payloads. Non-storage JSON is deep-compared. Actual vendored r180 GLTFLoader scene
geometry, local transforms and source metadata are compared for assembly and face;
missing-decoder and corrupt compressed-stream rejection are checked. R11 browser
image decode/visual equivalence still requires browser QA; pixel payloads are exact.

## Runtime contract

`loadOptimizedGLTFAsset(originalURL, options, {optIn:true})` in
`assembly-optimized-loading.js` wraps the existing loader contract. It lazily imports
the local decoder, checks supported/ready, uses one overall 120-second default budget,
and falls back to the exact original URL on decoder or compressed-load failure.
Cancellation and exhausted deadlines do not trigger a second download. Late results
are disposed through `disposeUnused`; synchronous work is checked against elapsed
budget even before timers can run. Metrics add `assetDelivery` with requested/used
mode and fallback reason. Raw success after a failed compressed transfer may cost
extra bytes; reported final-transfer metrics do not represent that combined cost.

No workers or CSP relaxation are used. Restrictive WASM/module policy should select
raw fallback rather than broaden permissions. Browser validation must cover success,
fallback, abort, deadline, CSP, and complete showcase appearance before default use.

## Explicit gzip assembly delivery

The assembly delivery file is `rebuild__assembly.meshopt.glb.gz`. This is actual
gzip file content, **not** a claim that hosting sends `Content-Encoding: gzip`.
Serve the file unchanged without a gzip Content-Encoding header; the application
uses `DecompressionStream('gzip')` and then the existing GLTF parse path. If hosting
instead transparently decodes the file, the gzip attempt fails safely to raw.

Build emits only the 8,055,333-byte wrapper, not the oversized canonical optimized
GLB. Gunzip reconstructs its 14,359,312 bytes exactly; that canonical hash and every
geometry/image check remain in the audit. `path`, `deliveryBytes`, and
`deliverySha256` describe deployed bytes; `outputBytes` and `outputSha256` describe
the decoded meshopt GLB. Gzip timestamp is zero and repeated built-in compression
is checked deterministic for the recorded Node/zlib version. No dependency install.

Decoded output is capped at the audited 14,359,312-byte size. Missing gzip support,
corruption, or wrong decoded length selects raw fallback. Cancellation/timeout
cancels the decompression reader; late parsed scenes are disposed. No extra deadline
is granted for decompression or fallback. `bodyBytes` counts fetched gzip file bytes,
`decompressedBytes` counts the canonical GLB, `decompressionMs` measures that phase,
and `parseMsIncludesDecompression: true` prevents interpreting total parse time as
codec-only. `assetDelivery.pipelineMs` includes initialization/fallback overhead.
Actual HTTP wire bytes can differ if the server applies additional transfer encoding.

This package also fits the GitHub connector's request-size ceiling; no security
policy or permissions are changed. End-user network payload is reduced independently
of that packaging constraint. No claim of measured browser speedup is made here.

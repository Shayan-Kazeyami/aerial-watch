# KTX2 runtime dependency notices

The Three.js MIT notice alone does **not** cover every KTX2 dependency. Retain this file and the files in `ktx2-licenses/` with distributions containing these dependencies. Exact local file lengths, SHA256 hashes, and official upstream source URLs are recorded in [`ktx2-licenses/provenance.json`](ktx2-licenses/provenance.json). These are dependency-source records, not the watch asset/runtime provenance manifest.

## Three.js r180 — MIT

`loaders/KTX2Loader.js`, `utils/WorkerPool.js`, and `math/ColorSpaces.js` are from official Three.js r180, commit `0af9729d0c143a86a1d725d6e2c3ad83301f3f34`. Retain the existing [`THREE-LICENSE.txt`](THREE-LICENSE.txt).

## Basis Universal transcoder — Apache License 2.0

`libs/basis/basis_transcoder.js` and `libs/basis/basis_transcoder.wasm` are the unmodified official Three.js r180 vendored pair. The upstream r180 [Basis README](https://github.com/mrdoob/three.js/blob/r180/examples/jsm/libs/basis/README.md) explicitly identifies both files and their Apache 2.0 license; a verbatim local copy is [`ktx2-licenses/BASIS-r180-README.md`](ktx2-licenses/BASIS-r180-README.md).

Three.js commit [`302240259d4ae8ae54557f7be6f0515a662f256d`](https://github.com/mrdoob/three.js/commit/302240259d4ae8ae54557f7be6f0515a662f256d) describes this pair's upgrade to Basis Universal v1.50. The v1.50 upstream `transcoder/basisu_transcoder.h` carries **Copyright (C) 2019–2024 Binomial LLC. All Rights Reserved.** The full license from the official v1.50 tag is retained in [`ktx2-licenses/BASIS-APACHE-2.0.txt`](ktx2-licenses/BASIS-APACHE-2.0.txt). The tag resolves to `051ad6d8a64bb95a79e8601c317055fd1782ad3e`; this records the license source, not a claim that the shipped WASM was rebuilt locally. No top-level NOTICE file is present in that version's official root listing. The complete version-matched upstream BSD notice is additionally retained as [`ktx2-licenses/BASIS-v1.50-THIRDPARTY-BSD.txt`](ktx2-licenses/BASIS-v1.50-THIRDPARTY-BSD.txt), covering the upstream Zstandard directory and also mentioning an encoder-only TinyEXR component; retaining that notice does not assert that the encoder is shipped here. Do not substitute a later source release's dates/version for the shipped pair.

## KTX-Parse — MIT

`libs/ktx-parse.module.js` identifies its writer as **KTX-Parse v1.0.1**. Copyright (c) 2020 Don McCurdy. Full official v1.0.1 license: [`ktx2-licenses/KTX-PARSE-MIT.txt`](ktx2-licenses/KTX-PARSE-MIT.txt). Upstream: [donmccurdy/KTX-Parse](https://github.com/donmccurdy/KTX-Parse/tree/v1.0.1).

## zstddec wrapper and embedded Zstandard WASM — MIT AND BSD-3-Clause

`libs/zstddec.module.js` includes an embedded base64 WASM decoder, not only a JavaScript wrapper. The official zstddec combined license includes both:

- Wrapper: Copyright (c) 2020 Don McCurdy; MIT.
- Zstandard: Copyright (c) 2016-present, Yann Collet, Facebook, Inc. All rights reserved; BSD-3-Clause.

Retain the complete combined license, including the binary redistribution and no-endorsement provisions: [`ktx2-licenses/ZSTDDEC-MIT-ZSTD-BSD.txt`](ktx2-licenses/ZSTDDEC-MIT-ZSTD-BSD.txt). Official source: [donmccurdy/zstddec-wasm LICENSE](https://github.com/donmccurdy/zstddec-wasm/blob/ff24d680cc36af645d1e06d027f861e16ff79bf0/LICENSE). The shipped wrapper is identified by its exact r180 upstream bytes/hash; no unverified zstddec package or embedded Zstandard version is asserted.

No dependency source code or binary was modified in this notice-only change. Dependency licenses are separate from leather texture licenses and watch geometry attribution.

# Watch v8 preview candidate

Static runtime snapshot, 2026-11-18. Not deployed. GitHub Pages still serves main /(root); no production source or settings changed.

Contains cumulative v8 runtime and preview-only leather asset route fix. Entry index.html uses relative release base. Original deployment manifest predates the preview-only patch and must not be treated as a current whole-tree hash.

For independent Pages testing, use a separate preview repository or obtain approval for a publishing branch that preserves production and adds a preview subdirectory. Do not point existing Pages directly at this candidate: it would replace production.

300 runtime files preserved byte-for-byte from the locally rendered v8 candidate; deployment/browser QA still pending. Git tree object hashes identify exact content.

# Offline R18 final source recovery
Immutable restoration commit: 41a5cbba744c6211429dd0d2a4ad1d8893e56e6c.
Extract this archive into a fresh directory. source/ contains the entire restored editable source, assets, vendor modules, tests and scripts; no source files were excluded (small installation receipts retained).
This is NOT the transformed sparse deployment. It does not require its sibling asset owners to restore source.
Use Node22 and Python3. No GitHub credential or network is required to extract and verify source.
Run: python3 verify-composed.py source
Then: cd source && node scripts/validate.mjs && node --test --test-concurrency=1 tests/*.test.mjs
Serve with python3 -m http.server 8765 --directory source (from archive parent); open /atelier-preview.html?quality=efficient.
Expected source digest: 1d16cf3e5e653360db93e3ab23921161d741f9f372639fe59bb0929787002e4c.
Manifest SHA256: 2dfc71fed1007acb84ad13c4e7ccd25e7531713cc4f6fa82b21500e7862ddd8f.
Archive receipt is supplied alongside this archive; verify its SHA256 before extraction.
The source digest excludes model assets; existing deployment manifest and exact archive checksum cover additional boundaries.
Hardware/S24/WebGPU/usableWebM and intermittent capture timing remain unverified. Inherited pin/spring contact remains. Optional transmission/detour disabled. This backup does not mean all tasks complete.

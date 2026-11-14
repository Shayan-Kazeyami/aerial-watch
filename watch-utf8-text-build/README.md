# Remaining UTF8 UI token repairs, isolated build only
Base feature/explorer-labels-20261114 at482ee78bf8ef29a29ac07f9605aaee8681dbf731, immutable release94ad3066d775ac9b39dd95a4c52a70388d86df29e327e556edfeee0328624817.

After building prerequisite feature stages:
```
python watch-utf8-text-build/build.py
node watch-utf8-text-build/check.mjs
python watch-utf8-text-build/verify.py
```
Applies only19 remaining known mojibake tokens to current pinned assembly-review.js, not the older full candidate file. Twelve UI text lines change. All other source bytes remain identical, including newer framing code; existing corrected quality-status strings preserved. Crown and Explorer classifier unchanged. Ten VM expression cases and module syntax pass; not browser visual or aggregate app acceptance.

New immutable local release48438e79481a6258e2ae563e943d25a516c2e5a515f15a6335bdb08197ca752d,298 closure files. Only assembly-review.js and two viewer-revision identity files differ. Generated staging remains local; repository adds builder/checks/evidence only, no deployment workflow or main/source/release modifications.

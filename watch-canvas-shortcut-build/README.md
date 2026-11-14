# Canvas browser-shortcut guard, isolated build only
Base feature/utf8-ui-text-20261114 at1e1cd2a1478334a89207a19d19d932637584d97e. Apply exact reviewed handler replacement to latest immutable assembly-review.js, not old full-source candidate.

After prerequisite feature stages:
```
python watch-canvas-shortcut-build/build.py
node watch-canvas-shortcut-build/check.mjs
python watch-canvas-shortcut-build/verify.py
```
Ctrl/Meta/Alt events return before this handler cancels browser shortcuts or changes camera. Shift input stays allowed.33 VM cases pass,15 baseline interceptions reproduced, module syntax passes. Separate OrbitControls arrow behavior and crown listener unchanged. No native-browser page-zoom/OS/IME acceptance claimed.

New local immutable release9865b37ea1813c85badb404935f7710c688f04beef36da55d7d517ceef96b353 has298 verified closure files. Only assembly-review.js plus two revision identity files change. Exact whole-source replacement check preserves all other latest bytes, UTF8/Explorer/crown/framing included. Commit adds builder/tests/evidence only; no main/deployment or old immutable release edits.

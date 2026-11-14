# Pointer ownership selection guard, isolated build only
Base feature/saved-clock-validation-20261114 at30e01253f615a1ee87c266dccf4854ac00b7125e. Reuses independently reviewed current-compatible pointer block; requires exact single old-block match and pins complete resulting module hash.

After prerequisite feature stages:
```
python watch-pointer-ownership-build/build.py
node watch-pointer-ownership-build/check.mjs
node watch-pointer-ownership-build/regression.mjs
python watch-pointer-ownership-build/verify.py
```
10 handler cases plus9 regression cases pass: tap/drag, pointer identity, pinch release order, cancellation/blur/visibility and primary/secondary/auxiliary buttons. Module syntax passes. Earlier isolated native evidence exists, but no new native-browser test of this combined feature. Crown listener and OrbitControls code unchanged.

New immutable local releasec9468467517d37ca9f4fb34795443034169480d22d6e3a7924c9b03993fcb888 verifies298closure files. Only assembly-review pointer ownership block and two revision identity files change; all other latest bytes/known fixes preserved. Repository adds builder/tests/evidence only. No old release/main/deployment edits.

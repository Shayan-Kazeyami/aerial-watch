# Saved-clock safe-cycle validation, isolated build only
Base feature/canvas-shortcuts-20261114 atf5e12dcbf5da36db4ad9cf063d95cdedda90dacd. Uses exact verified assembly-story base and adds only safe-integer floor(mechanism*3.5) validation matching actual escapement guard.

After prerequisite feature stages:
```
python watch-saved-clock-build/build.py
node watch-saved-clock-build/check.mjs
python watch-saved-clock-build/verify.py
```
23 valid/default/invalid/boundary cases pass; huge imported mechanism instants reject before downstream calls in extracted latest restoreSavedView. Hands/other validation policies unchanged. No guarantee of atomicity for other errors, no guard against subsequent playback crossing range, no rendered-browser import acceptance.

New local immutable releasee01677cd86bd5840e29c8ec4753aaa707eca40d83efd46528f1a56551e733934 has298 verified closure files. Only assembly-story.js plus2revision identity files differ. Latest assembly-review.js is byte-identical, preserving framing/canvas/UTF8 work; crown/Explorer retained. Repository adds builder/tests/evidence only, not generated staging. No main/deploy or old release changes.

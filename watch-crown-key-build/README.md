# Crown keyboard parity candidate (not deployed)
Base: feature/normal-stream-inplace-20261114 at c728d5bbfad8b35713ddfcbf4e660506099e601c.

Fix: ArrowLeft emits -15 and ArrowRight +15, matching the visible Turn left/right controls. Up/down remains unchanged. Independent fake-DOM event review passed; no browser/physical-device claim.

After building the existing privacy + normal-stream feature inputs, run:
```
python watch-crown-key-build/build.py
node watch-crown-key-build/test.mjs
```
The builder verifies all 298 source closure files, changes one runtime module, regenerates immutable revision identities, and writes an isolated staging directory. It does not edit existing release files, bootstrap or main. Build-generated files are intentionally not committed.

Local release: bd55a594260f4627127bcdb1975c2f9902eede87d0528669e02a111552ba939d. Viewer integration remains pending. No deployment workflow is added.

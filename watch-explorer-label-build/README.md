# Explorer label corrections, isolated build only
Base feature/crown-key-parity-20261114 at efe03c1ec074bb0ab71a794af25e73f0074a2a9e. Preserve prior crown/normal/privacy fixes.

After building prerequisite feature stages, run:
```
python watch-explorer-label-build/build.py
python watch-explorer-label-build/verify.py
node watch-explorer-label-build/check.mjs
node --test watch-explorer-label-build/tests/*.mjs
```
Only five labels change: OM10 #58 sliding-pinion yoke, #74 crown-wheel screw, #84 mainspring, #116 pallet bridge, #141 barrel bridge. Source identities and descriptions remain searchable. Other161 labels unchanged, not all certified exact.

Builder verifies every base closure identity and emits a new immutable staging release with new viewer revision identities. Existing release/source files remain untouched. New local release94ad3066d775ac9b39dd95a4c52a70388d86df29e327e556edfeee0328624817 contains298 closure files. Commit includes builder/candidate/tests/evidence, not generated staging assets. No deployment workflow, main change, browser acceptance or release approval.

# Sealed 60-second capture readiness QA

Separate successor harness, not a rewrite of the 30-second evidence. Exact original served atelier-preview.js SHA256 must be `9fa6ab550905e783fcc515b6764fa5ce92043d00035083d0865b1a8eb93516c1` before private trace instrumentation. No timeout replacement or guard substitution. Receipt defaults to `capture-readiness-60-output/sealed-release.json`; immutable release/modules/geometry/hybrid are verified.

Five independent fixed jobs: native, cross-origin-1, cross-origin-2, cross-origin-3, cancel. Each cross-origin job uses exactly the same nested differing-origin topology and controlled 11-second stall. All three must pass actual matching-frame acknowledgement plus decoded PNG/dimension checks; no best-of selection. Cancel uses trusted Time click, requires no export, and retains the stricter prior <30-second measured cancellation bound.

Output: `capture-readiness-60-qa-output/<case>.json` and PNG where applicable. Every failed assertion exits nonzero; fail-fast is false and artifacts upload always. Existing 30-second failure evidence is untouched.

Workflow branch: `qa/capture-readiness-60-release-20261108`. Build: `qa-deliverables/capture-readiness-60-release/build/build-release.mjs`. Only strict build plus read-only inspection; no stage/publication/write job. Scoped software-rendered Efficient testing, not hardware/FPS, universal capture reliability, or real external host coverage.

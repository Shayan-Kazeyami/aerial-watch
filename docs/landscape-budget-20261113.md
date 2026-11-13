# Orientation-safe compact-touch startup budget

Verified candidate entering publication; public verification is recorded separately. Baseline main 8363a03959b06c92d02a03d64a1bb64e04986c1e and immutable release 5de340263d2bcb0a992914d7b0aa64176493934711907480b62bcad07bd486ca.

## Problem and scope

The existing primary-coarse-pointer default uses only viewport width ≤900 CSS px. Thus a fresh 430×932 phone starts Smooth, but the same 932×430 viewport starts Studio. The latter has materially heavier configured rendering and misses progressive normal startup. This is a policy inconsistency, not proof of physical-device FPS.

Use primary coarse pointer and short side ≤900 CSS px for the initial default. Explicit quality and normalStream parameters still win. Do not reactively change the selected quality when a loaded viewer rotates. Fine-primary-pointer desktop defaults remain Studio.

This is a compact-touch policy, not reliable phone detection. A 768×1024 tablet already started Smooth in portrait; now its 1024×768 landscape does too. Both dimensions above 900 remain Studio. A coarse-primary touchscreen with a short side ≤900 also gets Smooth. Users retain the visible quality selector.

## Preservation gates

- 33 unit tests cover default parameters, portrait/landscape pairs, 900/901 boundary, fine pointer, explicit quality and stream flags, alternate leather, unrelated/duplicate parameters and fragment.
- Browser gates must verify actual renderer settings and default URL through both root iframe and direct immutable entry, and stable model/context after rotation without overriding an explicit quality choice.
- No geometry, materials, camera, UI layout or renderer implementation changes are intended.
- Compare candidate Smooth to baseline explicit Smooth at matching camera/state. Do not claim visual equivalence to the former landscape Studio default: lower rendering budget is intentional and visible as Smooth.
- Production publication requires exact-release browser evidence, fresh main lease, public functional verification and current recovery backup.

## Verified stage result

Exact immutable release fad7fffe passed six-case run 43440024935 at QA commit ef9fc8242f688b22902e9d73511e5152399625cd. Portrait and landscape rendered Smooth at DPR1 with AO/shadows/bloom off. Explicit quality and normalStream, fine desktop and direct entry passed. Deliberate Balanced choice survived settled rotation twice without canvas replacement, navigation or model redownload. Screenshots were inspected. Studio cases checked initialized runtime policy, not full Studio renders. Screenshots paused motion through the existing user control; this is functional/still-view software-GPU evidence, not hardware phone FPS.

Earlier runs 43438936953 and 43439313368 passed functional assertions but timed out at the final Balanced screenshot (45 seconds). The final run uses recorded user-control pause and bounded 180-second screenshot/evaluation budgets; runtime unchanged. Retain these failures and do not describe them as a proven app crash.

Public deployment and recovery verification are recorded separately after publication.

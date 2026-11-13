# Progressive leather detail loading candidate (2026-11-13)

Status: immutable release gates passed; publishing this exact candidate. Public follow-through and recovery are recorded separately.

## User-visible purpose
Smooth can become interactive without waiting for the largest leather normal texture. It first uses the existing verified 2K mip chain, then replaces it with the exact original 4K detail. The intended default applies only to craft14 + Smooth. Explicit normalStream=0 and Studio/Sharp remain full-first. No geometry, silhouette, bevel, mechanical animation or final texture quality is reduced. Initial close-up detail can be lower while the upgrade is pending.

## Implementation and safeguards
- Reconstruct the exact audited 4K KTX from the already verified 2K payload, a small audited embedded header, the remaining range of existing part0, and existing part1. No new large assets.
- Require exact lengths, status/range headers, same-origin responses, component digests and the complete 4K SHA. A server ignoring Range can use its verified whole part0 once; that fallback adds 4.39 MB compared with direct 4K delivery.
- Resolve Basis workers through immutable asset routing rather than a missing relative path.
- Keep the usable initial texture on upgrade failure; abort pending work on disposal and dispose late decoded resources.
- Rebuild selected/inspection material variants after adoption so they do not retain the old texture.
- Record actually installed normal identity separately from requested final identity. Configuration export is available while pending. PNG and both offline/fallback video entry paths require full detail; PNG rechecks after awaited provenance.

## Evidence so far
56 integrity/policy/lifecycle CPU tests and 24 default-policy tests pass locally. These do not prove physical-device GPU performance.

Cold fresh-context Chromium SwiftShader, 430×932, DPR1, 4 Mbit/s / 80 ms:
- Run 43427696240: first interactive 101,406.4 ms direct versus 77,538 ms progressive. All three functional cases passed; image gate failed only on timed crown halo.
- Run 43429461121: 100,563.6 ms versus 76,923 ms; initial and final images identical after overlay isolation. Both capture branches and PNG entry guards checked with interception, not encoding.
- Run 43430189300: 101,255.9 ms versus 78,729 ms; final image identical. Selected/transparent/wireframe/solid-wire/clay bindings, actual held crown during upgrade, release-stop, failure retention and PNG post-await readiness guard passed. Initial screenshot contains a temporary root loading overlay, so its whole-image difference is not a texture comparison.

This is a repeatable lab first-interaction improvement, not a promised phone load time, frame-rate increase or hardware WebGPU result. The upgrade completion was deliberately gated until a real held input existed; full-completion wall times from those runs are not production latency measurements. Final 4K identity remains bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585.

Next gates: immutable default-path/actual PNG/config exports and quality changes, then main lease, deployment, public render and recovery backup.

## Immutable release gates
Release 5de340263d2bcb0a992914d7b0aa64176493934711907480b62bcad07bd486ca is unchanged across these gates:
- 43433471881: default Smooth at 430×932 passed real pending configuration, full PNG embedded identity and full configuration export. Explicit normalStream=0 and default Studio passed. Full-first quality-switch baselines passed.
- 43434573092: progressive quality switch at 320×568 passed. The earlier 15-second snapshot cutoff was premature: a successful software-renderer evaluation took 37.7 seconds. The 430×932 case reached full adoption but exceeded the separate 90-second budget for two additional software-rendered frames.
- 43435955214: unchanged 430×932 progressive Sharp→Smooth case passed with the frame-evaluation budget aligned to measured software rendering. Full identity, stable canvas/CSS after explicit quality changes, no additional resize on adoption, no model reload or JavaScript errors. No functional assertion was removed. This is functional evidence, not faster rendering or a device-FPS claim.
- 80 unit tests passed in CI. Actual PNG pixels were inspected. Full/fallback video routing is guarded; no new end-to-end video encoding claim.

Public deployment verification and backup follow separately. Earlier failed diagnostic runs remain recorded rather than represented as passes.

# Aerial optional transmission-MSAA trial — Three.js r180

`three.module.js` is Three.js r180 with exactly one local line changed. This is
not an upstream Three.js option or API. The MIT license remains unchanged in
`THREE-LICENSE.txt`; original source notices are preserved.

Upstream source: https://raw.githubusercontent.com/mrdoob/three.js/r180/build/three.module.js

The unmodified vendored file was byte-compared with that upstream URL before
patching on 2026-11-01.

- Original SHA-256: `c8211c69345d2e9949dc7a8ac969380497aa0600a5a8ac6a459c8cd02dd9cb8a`
- Modified SHA-256: `c1ed979f19d825336de66d4a2a15d4346cf2c2f9291e01f8f0619631803c1e06`

The only change is inside `renderTransmissionPass`, in the lazy creation of
`currentRenderState.state.transmissionRenderTarget[ camera.id ]`:

```diff
-                    samples: 4,
+                    samples: _this.aerialTransmissionSamples === 0 ? 0 : 4,
```

The displayed indentation is illustrative; all file bytes except that expression
are identical to upstream. The regression test reverses that one replacement
and verifies the complete upstream SHA-256.

## Opt-in and lifecycle

Set the custom property `renderer.aerialTransmissionSamples = 0` **before the
first transmission render**. Only numeric zero selects an unmultisampled target;
absent, undefined and all other values preserve the original four samples.
This is an initialization-only option for each lazily allocated camera target.
Changing the property after allocation does not reconfigure existing targets.
Use a fresh renderer/page for a matched A/B rather than implying it is a live
quality switch.

Root application wiring may enable this only for the explicit `antialias=smaa`
or `auditTransmissionMSAAoff` diagnostic trials. This patch does not itself
activate either trial or alter any default.

Composer target MSAA and the renderer's transmission target MSAA are independent.
This patch changes neither target dimensions nor transmission resolution scale,
shaders, mip generation, materials, geometry, optical settings or render ordering.
SMAA, if selected separately, belongs before OutputPass. It is a different AA
method requiring matched edge/specular visual validation, not an assurance of
identical appearance or phone frame-rate improvement.

## Reversal

Replace the single modified expression above with `samples: 4,` and verify the
original SHA-256. Remove the custom property assignment in any trial wiring.
No broad vendor upgrade or other vendor modification is included here.

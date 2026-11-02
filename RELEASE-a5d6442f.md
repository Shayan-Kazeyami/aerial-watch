# Studio wireframe inspection

Studio wireframe could become covered by dark rectangles. Controlled same-camera tests reproduce it with AO off, restore visible wire mesh with only bloom bypassed, and observe non-finite HDR samples spreading through bloom blur targets. Wireframe inspection now bypasses bloom only. Resolution, AO, shadows, normal materials and authored quality options stay unchanged. Leaving wireframe derives bloom from the current profile, including quality changes, reset and imported configurations. Normal Studio is restored.

Validation: 671 authoritative tests; 295 JavaScript syntax checks and 315-file source manifest; packaged render/interaction and live verification recorded separately. Native WebGL2 remains default with B face and SOURCE case. No geometry, material, lighting, global AA or hardware-WebGPU policy changes. All prior immutable namespaces remain unchanged.

Release: a5d6442fe1e1d7bc0582bf6024d125d184693b24f2e1f8e9d329bc3736052368. Raw source: f7df334ded3aa38579f461fd1c4b737a184a56b3bcf18a32a34a77f3a7c8a7a6. Packaged source: 6e587d5f9e70020526d66e77bc50b83bfebc66c08aa8d20b465be705602da742. Software rendering evidence only; no physical GPU or phone performance claim.

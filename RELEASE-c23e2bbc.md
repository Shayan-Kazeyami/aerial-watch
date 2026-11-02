# Node-on-WebGL2 glass transmission sampling

Native WebGL2 remains the default, with approved B face and SOURCE case. Only the optional node-on-WebGL2 opaque transmission target now resolves up to four samples, matching native WebGL transmission. Beauty/SMAA samples remain zero; hardware WebGPU transmission policy remains unchanged. No materials, geometry, lights or textures changed.

Matched paused camera/time/options Efficient control: glass-on mean absolute RGB error against native falls from 1.404 to 0.432 across the watch, and 1.944 to 0.184 around dial lettering (8-bit channel units). Glass-off pixels are identical before/after. Private instrumentation isolated transmission samples; sealed packaged native/node controls reproduce the result with no browser errors. Native watch pixels and node glass-off pixels remain unchanged. Deployment and live verification are recorded separately.

Validation: 669 authoritative tests, source syntax and 315-file manifest validation. Release c23e2bbc8a64658f2c7f29431cb144cf584e96d0eeac9a1e22c73697acb7b3bc; raw source 30c58340b08514eb8b2ef11241cd645b1809f407528cd4d91884aa5f1d8ef168; packaged source bb7d910c751da1a77a6b1c054d56cf572c696b61013f37bd83dc1e6db7155aca. All previous immutable releases and owners preserved. No physical WebGPU or phone performance claim.

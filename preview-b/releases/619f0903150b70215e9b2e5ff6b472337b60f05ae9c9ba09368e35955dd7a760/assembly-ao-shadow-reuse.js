// SSAOPass's normal/depth override does not sample lighting or shadows. In
// Three r180 its renderer.render() nevertheless redraws all shadow casters.
// Keep beauty's freshly rendered map and leave every quality setting intact.
// Scope this strictly to the normal override, not the beauty/transmission pass.
export function installAONormalShadowReuse(pass) {
  const original = pass._renderOverride;
  if (typeof original !== 'function') throw new TypeError('SSAO override renderer required.');
  let disposed = false;
  function wrapped(renderer, material, ...args) {
    if (disposed || material !== pass.normalMaterial || !renderer.shadowMap)
      return original.call(this, renderer, material, ...args);
    const shadow = renderer.shadowMap;
    const autoUpdate = shadow.autoUpdate, needsUpdate = shadow.needsUpdate;
    // needsUpdate also bypasses Three's autoUpdate guard; preserve a pending
    // request rather than consuming it during a non-lighting auxiliary pass.
    shadow.autoUpdate = false;
    shadow.needsUpdate = false;
    try {
      return original.call(this, renderer, material, ...args);
    } finally {
      shadow.autoUpdate = autoUpdate;
      shadow.needsUpdate = needsUpdate;
    }
  }
  pass._renderOverride = wrapped;
  return {dispose() {
    if (disposed) return;
    disposed = true;
    if (pass._renderOverride === wrapped) pass._renderOverride = original;
  }};
}

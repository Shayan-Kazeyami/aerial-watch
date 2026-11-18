// SSAOPass's normal/depth override does not sample lighting or shadows. In
// Native Three r180/r187 renderer.render() otherwise redraws shadow casters.
// Keep beauty's freshly rendered map and leave every quality setting intact.
// Scope this strictly to the normal override, not the beauty/transmission pass.
export function installAONormalShadowReuse(pass, {reuseSceneMatrices=false}={}) {
  const original = pass._renderOverride;
  if (typeof original !== 'function') throw new TypeError('SSAO override renderer required.');
  let disposed = false;
  function wrapped(renderer, material, ...args) {
    if (disposed || material !== pass.normalMaterial || !renderer.shadowMap)
      return original.call(this, renderer, material, ...args);
    const shadow = renderer.shadowMap;
    const autoUpdate = shadow.autoUpdate, needsUpdate = shadow.needsUpdate;
    const scene = reuseSceneMatrices ? pass.scene : null;
    const matrixAutoUpdate = scene?.matrixWorldAutoUpdate;
    // needsUpdate also bypasses Three's autoUpdate guard; preserve a pending
    // request rather than consuming it during a non-lighting auxiliary pass.
    shadow.autoUpdate = false;
    shadow.needsUpdate = false;
    // Opt in only after this composer's beauty RenderPass has updated matrices.
    // Auxiliary normals change visibility/materials, never object transforms.
    if (scene) scene.matrixWorldAutoUpdate = false;
    try {
      return original.call(this, renderer, material, ...args);
    } finally {
      shadow.autoUpdate = autoUpdate;
      shadow.needsUpdate = needsUpdate;
      if (scene) scene.matrixWorldAutoUpdate = matrixAutoUpdate;
    }
  }
  pass._renderOverride = wrapped;
  return {dispose() {
    if (disposed) return;
    disposed = true;
    if (pass._renderOverride === wrapped) pass._renderOverride = original;
  }};
}

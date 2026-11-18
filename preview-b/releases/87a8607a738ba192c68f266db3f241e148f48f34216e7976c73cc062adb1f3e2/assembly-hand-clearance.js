/** Premium-only, derived display stack. Original CAD buffers and mesh poses stay authoritative.
 * glTF uses Y for assembly depth. Clock rotations are about that same local Y axis,
 * so translating a private POSITION buffer remains compatible with clock poses,
 * explosion wrappers, picking, isolation and parent/sibling ordering.
 */
export const PREMIUM_HAND_CLEARANCE = Object.freeze({
  secondsDepthOffset: -.32,
  staffFixedBelow: 2.94,
  sourceStaffTop: 4,
  displayStaffTop: 3.68,
});

export function createHandClearance(exterior) {
  const find = id => {
    const matches = exterior.filter(mesh => mesh.userData?.assemblyId === id);
    if (matches.length !== 1 || !matches[0].geometry?.isBufferGeometry) {
      throw new TypeError(`Hand clearance requires exactly one baseline ${id} mesh.`);
    }
    return matches[0];
  };
  const seconds = find('SECONDS'), staff = find('SECONDS-STAFF');
  const variants = [];
  let enabled = false, disposed = false;
  try {
    for (const mesh of [seconds, staff]) {
      const original = mesh.geometry, derived = original.clone();
      variants.push({mesh, original, derived});
      if (mesh === seconds) {
        // Rigid translation: no shape, length, XY-pivot or normal changes.
        derived.translate(0, PREMIUM_HAND_CLEARANCE.secondsDepthOffset, 0);
      } else {
        const points = derived.attributes.position;
        if (!points || points.itemSize !== 3) throw new TypeError('Staff POSITION data missing.');
        const {staffFixedBelow: fixed, sourceStaffTop: top, displayStaffTop: target} = PREMIUM_HAND_CLEARANCE;
        const ratio = (target - fixed) / (top - fixed);
        for (let i = 0; i < points.count; i++) {
          const y = points.getY(i);
          if (y > fixed) points.setY(i, fixed + (y - fixed) * ratio);
        }
        points.needsUpdate = true;
        derived.computeVertexNormals();
      }
      derived.computeBoundingBox(); derived.computeBoundingSphere();
      derived.name = `${original.name || mesh.name} / premium clearance private clone`;
    }
  } catch (error) {
    for (const part of variants) part.derived.dispose();
    throw error;
  }
  return {
    get enabled() { return enabled && !disposed; },
    setEnabled(value) {
      if (disposed) return;
      const next = !!value;
      if (next) {
        // Never silently steal buffers owned by another geometry layer.
        for (const part of variants) {
          if (part.mesh.geometry !== part.original && part.mesh.geometry !== part.derived) {
            throw new Error(`Hand clearance geometry ownership conflict: ${part.mesh.name}`);
          }
        }
      }
      for (const part of variants) {
        if (next) part.mesh.geometry = part.derived;
        else if (part.mesh.geometry === part.derived) part.mesh.geometry = part.original;
      }
      enabled = next;
    },
    dispose() {
      if (disposed) return;
      disposed = true; enabled = false;
      for (const part of variants) {
        if (part.mesh.geometry === part.derived) part.mesh.geometry = part.original;
        part.derived.dispose();
      }
    },
  };
}

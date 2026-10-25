import {Vector3,Ray} from './vendor/three.module.js';

// Millimetre-scale inspection needs much more precision than a fixed .1/800
// frustum provides. Bounds are conservative world-space boxes, excluding floor.
export function updateInspectionDepth(camera,target,bounds,ao) {
  if(!bounds.length)return {minimumDistance:9,near:camera.near,far:camera.far};
  const direction=camera.position.clone().sub(target).normalize();
  const point=new Vector3();let reach=1;
  for(const box of bounds) for(const x of [box.min.x,box.max.x])
    for(const y of [box.min.y,box.max.y]) for(const z of [box.min.z,box.max.z])
      reach=Math.max(reach,point.set(x,y,z).distanceTo(target)+1);
  // Approach from outside the assembly to find the outer face on the viewing
  // ray. This prevents an orbit/dolly from entering a solid and slicing it open.
  const ray=new Ray(target.clone().addScaledVector(direction,reach),direction.clone().negate());
  let surface=0;
  for(const box of bounds) if(ray.intersectBox(box,point))
    surface=Math.max(surface,point.sub(target).dot(direction));
  const minimumDistance=Math.max(9,surface+.5);
  if(camera.position.distanceTo(target)<minimumDistance)
    camera.position.copy(target).addScaledVector(direction,minimumDistance);
  camera.lookAt(target);camera.updateMatrixWorld(true);
  let nearest=Infinity,farthest=0;
  for(const box of bounds) {
    let low=Infinity,high=-Infinity;
    for(const x of [box.min.x,box.max.x]) for(const y of [box.min.y,box.max.y])
      for(const z of [box.min.z,box.max.z]) {
        const depth=-point.set(x,y,z).applyMatrix4(camera.matrixWorldInverse).z;
        low=Math.min(low,depth);high=Math.max(high,depth);
      }
    if(high<=0)continue;
    nearest=Math.min(nearest,Math.max(.02,low));farthest=Math.max(farthest,high);
  }
  // Keep the studio floor/fog range while moving the near plane safely in front
  // of every visible bound. A quarter of the nearest depth leaves ample margin.
  const near=Number.isFinite(nearest)?Math.max(.005,nearest*.25):.1;
  const far=Math.max(800,farthest*1.1+1);
  if(camera.near!==near||camera.far!==far) {
    camera.near=near;camera.far=far;camera.updateProjectionMatrix();
  }
  // SSAOPass caches these only at construction/resize. Zoom, dolly and camera
  // transitions must use the same depth reconstruction as the colour pass.
  for(const material of [ao?.ssaoMaterial,ao?.depthRenderMaterial]) {
    const u=material?.uniforms;if(!u)continue;
    if(u.cameraNear)u.cameraNear.value=camera.near;
    if(u.cameraFar)u.cameraFar.value=camera.far;
    if(u.cameraProjectionMatrix)u.cameraProjectionMatrix.value.copy(camera.projectionMatrix);
    if(u.cameraInverseProjectionMatrix)u.cameraInverseProjectionMatrix.value.copy(camera.projectionMatrixInverse);
  }
  return {minimumDistance,near,far};
}

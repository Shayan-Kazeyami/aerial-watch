// QA-only fit. Preserve near/far/depth policy and full-scene visibility.
export function fitMacro(THREE,camera,controls,box,tilt,updateDepth){
 const sphere=box.getBoundingSphere(new THREE.Sphere());if(!(sphere.radius>0))throw Error('invalid target bounds');const direction=new THREE.Vector3(tilt,0,1).normalize();controls.target.copy(sphere.center);
 // Existing camera near can reflect previous whole-watch view. Never move target behind it.
 const distance=Math.max(controls.minDistance+1,sphere.radius*5,camera.near+sphere.radius+1);camera.position.copy(sphere.center).addScaledVector(direction,distance);camera.lookAt(sphere.center);camera.updateMatrixWorld(true);
 const depth=updateDepth();controls.minDistance=depth.minimumDistance;
 const actualDistance=camera.position.distanceTo(controls.target),tan=Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*Math.min(1,camera.aspect);camera.zoom=actualDistance*tan/(sphere.radius/.65);camera.updateProjectionMatrix();controls.update();camera.updateMatrixWorld(true);
 const projected=[];for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z])projected.push(new THREE.Vector3(x,y,z).project(camera).toArray());const result={projected,position:camera.position.toArray(),target:controls.target.toArray(),zoom:camera.zoom,near:camera.near,far:camera.far,distance:camera.position.distanceTo(controls.target),aspect:camera.aspect,depth};
 result.valid=projected.every(p=>Math.abs(p[0])<=.85&&Math.abs(p[1])<=.85&&p[2]>=-1&&p[2]<=1);return result;
}

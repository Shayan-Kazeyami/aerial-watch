// APPEND ONLY TO A VERIFIED QA COPY of assembly-review.js. Never sealed source.
// qaSubstitutionModule is imported by appended isolated module import, not production.
window.__mountingFootQA={
 register(){
  if(!openFrontFrame||!openFrontActive()||premiumActive()||!openFrontFrame.group.visible)throw Error('nonpremium visible frame required');
  const targets=openFrontFrame.group.children.filter(m=>/Seconds \/ axial mounting foot (350|110|250)$/.test(m.name));if(targets.length!==3)throw Error('three exact targets required');
  return targets.map(mesh=>{if(!qaSubstitutionModule.visibleAncestors(mesh))throw Error('hidden ancestor');mesh.updateWorldMatrix(true,false);const materials=(Array.isArray(mesh.material)?mesh.material:[mesh.material]);return{name:mesh.name,uuid:mesh.uuid,world:mesh.matrixWorld.toArray(),materials:materials.map(m=>({uuid:m.uuid,type:m.type,name:m.name,shaderKey:m.customProgramCacheKey(),roughness:m.roughness,metalness:m.metalness})),triangles:mesh.geometry.index.count/3,vertices:mesh.geometry.attributes.position.count}})
 },
 prepare(json){this.register();const mesh=openFrontFrame.group.children.find(m=>m.name===json.name);if(this.transaction)throw Error('transaction active');this.transaction=qaSubstitutionModule.prepareSubstitution(THREE,mesh,json);this.mesh=mesh;return mesh.uuid},
 activate(){this.transaction.activate();dirty=true},restore(){this.transaction.restore();dirty=true},dispose(){this.transaction.dispose();this.transaction=null;this.mesh=null;dirty=true},
 pick(origin,direction){this.register();const ray=new THREE.Raycaster(new THREE.Vector3(...origin),new THREE.Vector3(...direction).normalize());return ray.intersectObject(this.mesh,false).map(h=>({uuid:h.object.uuid,faceIndex:h.faceIndex,materialIndex:h.face.materialIndex,distance:h.distance,point:h.point.toArray(),uv:h.uv?.toArray()}))}
};

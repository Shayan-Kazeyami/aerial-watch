const __qaSources=()=>source.filter(m=>Number.isInteger(m.userData.sourceIndex));
const __qaPart=sid=>source.find(m=>m.userData.sourceIndex===sid);
const __qaAllGeometryBytes=()=>{const found=new Set();let n=0;scene.traverse(m=>{if(m.geometry&&!found.has(m.geometry)){found.add(m.geometry);n+=Object.values(m.geometry.attributes).reduce((s,a)=>s+(a.array?.byteLength??a.data?.array?.byteLength??0),0)+(m.geometry.index?.array.byteLength||0)}});return n;};
const __qaSnapshot=()=>{const batches=[];scene.traverse(m=>{if(m.isBatchedMesh)batches.push({name:m.name,vertices:m.geometry.attributes.position?.count,indexCount:m.geometry.index?.count,geometryBytes:Object.values(m.geometry.attributes).reduce((s,a)=>s+(a.array?.byteLength??a.data?.array?.byteLength??0),0)+(m.geometry.index?.array.byteLength||0),attributes:Object.keys(m.geometry.attributes),geometryCount:m._geometryCount,instanceCount:m._instanceCount})});return{batch:mechanismBatch?.snapshot(),batches,allSceneGeometryBytes:__qaAllGeometryBytes(),source:__qaSources().map(m=>({sourceIndex:m.userData.sourceIndex,name:m.name,position:m.position.toArray(),quaternion:m.quaternion.toArray(),scale:m.scale.toArray(),matrix:m.matrix.toArray(),matrixWorld:m.matrixWorld.toArray(),parent:m.parent?.name,visible:m.visible,vertices:m.geometry.attributes.position.count,indices:m.geometry.index.count,positionVersion:m.geometry.attributes.position.version,normalVersion:m.geometry.attributes.normal?.version,material:(Array.isArray(m.material)?m.material:[m.material]).map(a=>({name:a.name,type:a.type,color:a.color?.getHex(),metalness:a.metalness,roughness:a.roughness,opacity:a.opacity,transparent:a.transparent,transmission:a.transmission,wireframe:a.wireframe}))})),camera:{p:camera.position.toArray(),q:camera.quaternion.toArray(),t:controls.target.toArray(),zoom:camera.zoom,fov:camera.fov,near:camera.near,far:camera.far},framebuffer:[renderer.domElement.width,renderer.domElement.height],rendererInfo:{render:{...renderer.info.render},memory:{...renderer.info.memory},programs:renderer.info.programs?.length},backend:backendIdentity,explosion:explosion?.snapshot()};};
window.__reuseQa={
 snapshot:__qaSnapshot,
 hashSources(){const hash=array=>{const b=new Uint8Array(array.buffer,array.byteOffset,array.byteLength);let h=2166136261;for(const x of b)h=Math.imul(h^x,16777619);return(h>>>0).toString(16)};return __qaSources().map(m=>({sid:m.userData.sourceIndex,attributes:Object.fromEntries(Object.entries(m.geometry.attributes).map(([k,a])=>[k,hash(a.array)])),index:hash(m.geometry.index.array)}));},
 async show({sid=null,pose=0,explode=0,finish=true,display='solid',view='watch',zoom=1}={}){
  cameraTween=null;controls.enableDamping=false;clock.setRunning('mechanism',false);clock.setRunning('hands',false);$('animate').checked=false;$('animate-movement').checked=false;
  clock.seek(pose,{track:'mechanism'});clock.seek(pose,{track:'hands'});applyClockPose(clock.snapshot());
  explosion?.setAmount(explode,{instant:true});
  selected=[];isolated=sid===null?(view==='movement'?new Set(source):null):new Set([__qaPart(sid)]);
  $('movement-only').checked=view==='movement';$('finish').checked=finish;
  inspectionDisplay.wireframe=display==='wire';inspectionDisplay.solidWireframe=false;inspectionDisplay.transparent=display==='transparent';
  visibility();scene.updateMatrixWorld(true);
  const box=new THREE.Box3();if(sid!==null)box.setFromObject(__qaPart(sid));else if(view==='movement'){for(const m of source)if(m.visible)box.union(new THREE.Box3().setFromObject(m));}else box.setFromObject(model);
  if(sid!==null||view==='movement'){
   const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()),radius=Math.max(size.length()/2,.05);controls.target.copy(center);camera.position.copy(center).addScaledVector(new THREE.Vector3(1,.5,2).normalize(),zoom===12?.25:radius*4.5);camera.zoom=zoom;
  }else {controls.target.set(0,0,0);camera.position.set(62,52,90);camera.zoom=1;}
  camera.lookAt(controls.target);camera.updateProjectionMatrix();scene.updateMatrixWorld(true);
  const depth=updateInspectionDepth(camera,controls.target,depthBounds,ao,isolated?{distanceFloor:.25,surfacePadding:.05}:undefined);
  mechanismBatch?.build(source);renderer.info.reset();mechanismBatch?.beforeRender();try{composer.render();}finally{mechanismBatch?.afterRender();}
  dirty=false;
  const snapshot=__qaSnapshot();snapshot.depth=depth;snapshot.image=renderer.domElement.toDataURL('image/png');return snapshot;
 },
 sourceRayHits(){scene.updateMatrixWorld(true);const raycaster=new THREE.Raycaster();raycaster.setFromCamera(new THREE.Vector2(0,0),camera);return raycaster.intersectObjects(source,false).slice(0,8).map(x=>({sourceIndex:x.object.userData.sourceIndex,distance:x.distance,faceIndex:x.faceIndex,point:x.point.toArray()}));},
 validatePoses(){const rows=[];for(const t of [0,.25,1,30,3600]){clock.seek(t,{track:'mechanism'});clock.seek(t,{track:'hands'});applyClockPose(clock.snapshot());for(const amount of [0,.4,1]){explosion?.setAmount(amount,{instant:true});scene.updateMatrixWorld(true);rows.push({t,explode:amount,source:__qaSources().map(m=>({sid:m.userData.sourceIndex,m:m.matrix.toArray(),w:m.matrixWorld.toArray(),p:m.position.toArray(),q:m.quaternion.toArray()}))});}}return rows;},
 setBatchEnabled(value){mechanismBatch?.setEnabled(value);},
 mutateSource(sid){const m=__qaPart(sid);m.geometry.attributes.position.needsUpdate=true;return m.geometry.attributes.position.version;},
 selectSource(sid){selected=[__qaPart(sid)];updateMaterials();dirty=true;},
 ready:true
};

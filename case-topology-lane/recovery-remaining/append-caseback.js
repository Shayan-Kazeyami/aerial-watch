// Private QA only. Executes the actual viewer with source-guarded caseback A/B.
const casebackQAMarker='caseback-meridian-sixstrips-r1';
let cbMesh,cbSource,cbCandidate,cbDisplayBefore,cbDisplayAfter,cbMat,cbMatrix,cbPose,cbSourceAttrHashes,cbInitialDisplayHashes,cbCap;
const cbHash=async a=>{const b=new Uint8Array(a.buffer,a.byteOffset,a.byteLength);return [...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(v=>v.toString(16).padStart(2,'0')).join('')};
const cbHashes=async g=>{const o={};for(const [k,a]of Object.entries(g.attributes))o[k]=await cbHash(a.array);if(g.index)o.index=await cbHash(new Uint32Array(g.index.array));return o;};
window.casebackQA={
 async init(){
  scene.traverse(o=>{if(o.isMesh&&o.userData?.assemblyId==='CASEBACK')cbMesh=o});if(!cbMesh)throw Error('Actual CASEBACK missing');
  cbInitialDisplayHashes=await cbHashes(cbMesh.geometry);casebackFinish.setEnabled(false);cbSource=cbMesh.geometry;cbMat=cbMesh.material;cbMatrix=cbMesh.matrix.toArray();cbSourceAttrHashes=await cbHashes(cbSource);
  const data=await(await fetch('/case-topology-lane/recovery-remaining/caseback-package.json')).json();cbCandidate=new THREE.BufferGeometry();
  for(const [k,v]of Object.entries(data.candidate)){
   const zip=Uint8Array.from(atob(v.base64z),c=>c.charCodeAt(0));const raw=new Uint8Array(await new Response(new Blob([zip]).stream().pipeThrough(new DecompressionStream('deflate'))).arrayBuffer()),arr=new(k==='index'?Uint32Array:Float32Array)(raw.buffer);if(await cbHash(arr)!==v.sha256)throw Error('Candidate hash mismatch '+k);
   if(cbSourceAttrHashes[k]!==data.source[k].sha256)throw Error('Canonical source mismatch '+k);
   if(k==='index')cbCandidate.setIndex(new THREE.BufferAttribute(arr,1));else cbCandidate.setAttribute(k,new THREE.BufferAttribute(arr,k==='uv'?2:3));
  }
  const display=g=>{const m=new THREE.Mesh(g,cbMat);m.userData.assemblyId='CASEBACK';const finish=createCasebackFinish({mesh:m});finish.setEnabled(true);return {geometry:m.geometry,cap:finish.audit}};
  const a=display(cbSource),b=display(cbCandidate);cbDisplayBefore=a.geometry;cbDisplayAfter=b.geometry;cbCap={source:a.cap,candidate:b.cap};
  if(a.cap.capTriangles!==b.cap.capTriangles||Math.abs(a.cap.capAreaMM2-b.cap.capAreaMM2)>1e-9)throw Error('Cap finish geometry differs');
  if(JSON.stringify(cbInitialDisplayHashes)!==JSON.stringify(await cbHashes(cbDisplayBefore)))throw Error('QA source finish not actual runtime finish');
  casebackFinish.dispose();casebackFinish=null;cbMesh.geometry=cbDisplayBefore;cbDisplayBefore.computeBoundingBox();cbDisplayAfter.computeBoundingBox();controls.enableDamping=false;this.freeze();
  return {marker:casebackQAMarker,sourceHashes:cbSourceAttrHashes,candidateHashes:await cbHashes(cbCandidate),sourceDisplayMatchesRuntime:true,before:cbSource.index.count/3,after:cbCandidate.index.count/3,cap:cbCap,materialName:cbMat.name,materialType:cbMat.type,roughness:cbMat.roughness,metalness:cbMat.metalness,backend:backendIdentity,quality,renderer:renderer.getContext().getParameter(renderer.getContext().VERSION)};
 },
 freeze(){stopTour();for(const n of ['animate','animate-movement']){const e=$(n);e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}dirty=true;},
 settled(){return !cameraTween&&!crownInteraction.active&&!explosion?.animating&&!['upgrading','waiting-for-first-frame'].includes(progressiveNormalState)},
 pose(mode){cameraTween=null;cbMesh.geometry=cbDisplayBefore;cbMesh.material=cbMat;resetExplosion(true);if(mode!=='assembled'){isolated=new Set([cbMesh]);visibility();scene.updateMatrixWorld(true);const center=cbDisplayBefore.boundingBox.getCenter(new THREE.Vector3());let point,dir,dist;
   if(mode==='back'){point=center;dir=new THREE.Vector3(.2,-1,.3);dist=115;}
   else if(mode==='edge'){point=new THREE.Vector3(19.25,-3.25,0);dir=new THREE.Vector3(.8,-.7,.8);dist=10;}
   else if(mode==='bore'){point=new THREE.Vector3(18.2,-3.35,0);dir=new THREE.Vector3(.2,-1,.3);dist=15;}
   else {point=new THREE.Vector3(15.72,-3.3,0);dir=new THREE.Vector3(-.6,-.8,.5);dist=mode.includes('macro')?4.5:11;}
   point.applyMatrix4(cbMesh.matrixWorld);dir.transformDirection(cbMesh.matrixWorld);controls.target.copy(point);camera.position.copy(point).addScaledVector(dir,dist);camera.zoom=1;camera.lookAt(point);camera.updateProjectionMatrix();
   if(mode.includes('wire')){cbMesh.material=cbMat.clone();cbMesh.material.wireframe=true;}
  }controls.update();cbPose={p:camera.position.clone(),q:camera.quaternion.clone(),t:controls.target.clone(),z:camera.zoom};dirty=true;},
 async set(candidate){cbMesh.geometry=candidate?cbDisplayAfter:cbDisplayBefore;cameraTween=null;camera.position.copy(cbPose.p);controls.target.copy(cbPose.t);camera.quaternion.copy(cbPose.q);camera.zoom=cbPose.z;camera.updateProjectionMatrix();controls.update();const f=renderer.info.render.frame;dirty=true;await new Promise(resolve=>{const poll=()=>renderer.info.render.frame>f?resolve():requestAnimationFrame(poll);requestAnimationFrame(poll)});
  if(cbMesh.geometry!==(candidate?cbDisplayAfter:cbDisplayBefore))throw Error('Display geometry overwritten');if(JSON.stringify(cbMesh.matrix.toArray())!==JSON.stringify(cbMatrix))throw Error('Caseback transform altered');if(JSON.stringify(cbSourceAttrHashes)!==JSON.stringify(await cbHashes(cbSource)))throw Error('Canonical source mutated');
  return {marker:casebackQAMarker,candidate,camera:{position:camera.position.toArray(),target:controls.target.toArray(),quaternion:camera.quaternion.toArray(),zoom:camera.zoom},triangleCount:cbMesh.geometry.attributes.position.count/3,materialPreserved:cbMesh.material===cbMat||cbMesh.material.wireframe,displayHashes:await cbHashes(cbMesh.geometry),cap:cbCap,calls:renderer.info.render.calls};
 }
};

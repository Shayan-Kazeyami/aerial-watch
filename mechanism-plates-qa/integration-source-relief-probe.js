// Isolated QA only: appended inside exact current application module.
const pqIds=[41,70,100,116,141],pqMeshes=new Map(),pqGeometries=new Map(),pqOriginals=new Map();
const pqHash=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a.buffer.slice(a.byteOffset,a.byteOffset+a.byteLength)))).map(x=>x.toString(16).padStart(2,'0')).join('');
const pqArray=a=>a.isInterleavedBufferAttribute?a.data.array:a.array;
const pqVisible=o=>{for(let p=o;p;p=p.parent)if(!p.visible)return false;return true};
const pqMaterial=m=>({name:m.name,type:m.type,color:m.color?.getHexString(),roughness:m.roughness,metalness:m.metalness});
let pqCamera,pqMaterials,pqState='baseline';
window.plateIntegrationQA={
 ready(){return !loading&&!failed&&!cameraTween&&!crownInteraction.active&&!crownVisual?.active&&!explosion?.animating&&!['waiting-for-first-frame','upgrading'].includes(progressiveNormalState)},
 async init(){
  scene.traverse(o=>{if(o.isMesh&&pqIds.includes(o.userData.sourceIndex)&&o.userData.originalGeometry)pqMeshes.set(o.userData.sourceIndex,o)});
  if(pqMeshes.size!==5)throw Error('Expected exactly five source plates');
  for(const [sid,o]of pqMeshes){pqOriginals.set(sid,o.geometry);const row={baseline:o.geometry};
   for(const mode of ['candidate','bevel']){if(mode==='candidate'&&sid===100){row[mode]=o.geometry;continue;}if(mode==='bevel'&&sid!==100)continue;const path=mode==='candidate'?'exact-seams':'source-preserving-front-bevel',g=new THREE.BufferGeometry();for(const [k,T,size]of [['position',Float32Array,3],['normal',Float32Array,3],['index',Uint32Array,1]]){const response=await fetch(`/mechanism-plates-qa/${path}/${sid}/${k}.bin`);if(!response.ok)throw Error('Missing fixture');const a=new THREE.BufferAttribute(new T(await response.arrayBuffer()),size);if(k==='index')g.setIndex(a);else g.setAttribute(k,a)}if(o.geometry.attributes.uv)g.setAttribute('uv',new THREE.BufferAttribute(new Float32Array(g.attributes.position.count*2),2));g.computeBoundingBox();g.computeBoundingSphere();row[mode]=g}pqGeometries.set(sid,row);
  }
  controls.enableDamping=false;stopTour();resetMotion();ao.enabled=false;bloom.enabled=false;dirty=true;
  return {release:location.pathname.split('/releases/')[1]?.split('/')[0],renderer:{revision:THREE.REVISION,backend:backendIdentity.actual,quality,pixelRatio:renderer.getPixelRatio()},source:await this.snapshot()};
 },
 async pose(spec){
  stopTour();resetMotion();resetExplosion(true);isolated=null;interiorView=false;$('movement-only').checked=false;visibility();
  if(spec.time)applyClockPose(clock.seek(spec.time,{track:'mechanism'}));
  if(spec.pulled){setCrownPulled(true);crownVisual.finish()}
  if(spec.explode)explosion.setAmount(spec.explode,{instant:true});
  view(spec.view||'showcase',false,{explosionEnvelope:!!spec.explode});cameraTween=null;controls.enableDamping=false;controls.update();ao.enabled=false;bloom.enabled=false;scene.updateMatrixWorld(true);
  pqCamera={p:camera.position.clone(),q:camera.quaternion.clone(),t:controls.target.clone(),zoom:camera.zoom};pqMaterials=new Map([...pqMeshes].map(([sid,o])=>[sid,o.material]));dirty=true;return this.snapshot();
 },
 async set(mode){pqState=mode;for(const [sid,o]of pqMeshes){const row=pqGeometries.get(sid);o.geometry=mode==='bevel'?(row.bevel||row.candidate):row[mode]}
  cameraTween=null;camera.position.copy(pqCamera.p);camera.quaternion.copy(pqCamera.q);controls.target.copy(pqCamera.t);camera.zoom=pqCamera.zoom;camera.updateProjectionMatrix();controls.update();const frame=renderer.info.render.frame;dirty=true;await new Promise(resolve=>{const tick=()=>renderer.info.render.frame>frame?resolve():requestAnimationFrame(tick);requestAnimationFrame(tick)});return this.snapshot();
 },
 async snapshot(){scene.updateMatrixWorld(true);const targets=[];for(const [sid,o]of pqMeshes){const g=o.geometry;targets.push({sid,name:o.name,matrix:o.matrixWorld.toArray(),visible:pqVisible(o),material:pqMaterial(o.material),materialSame:!pqMaterials||o.material===pqMaterials.get(sid),positionHash:await pqHash(pqArray(g.attributes.position)),normalHash:await pqHash(pqArray(g.attributes.normal)),indexHash:await pqHash(g.index.array),triangles:g.index.count/3})}return {state:pqState,targets,camera:{p:camera.position.toArray(),q:camera.quaternion.toArray(),t:controls.target.toArray(),zoom:camera.zoom},explosion:explosion.snapshot(),clock:clock.snapshot(),crown:crownInteraction.snapshot(),loading,failed,AO:ao.enabled,bloom:bloom.enabled};},
 contacts(){scene.updateMatrixWorld(true);const boxes=[...pqMeshes.values()].filter(pqVisible).map(o=>new THREE.Box3().setFromObject(o).expandByScalar(.03));const rows=[];model.traverse(o=>{if(!o.isMesh||!o.geometry?.attributes.position||!pqVisible(o)||o.isBatchedMesh||o.isInstancedMesh)return;const box=new THREE.Box3().setFromObject(o);if(!boxes.some(b=>b.intersectsBox(box)))return;rows.push({id:o.userData.assemblyId||`source-${o.userData.sourceIndex}-${o.name}`,sid:o.userData.sourceIndex??null,name:o.name,matrix:o.matrixWorld.toArray(),position:Array.from(pqArray(o.geometry.attributes.position)),index:o.geometry.index?Array.from(o.geometry.index.array):null,target:pqMeshes.get(o.userData.sourceIndex)===o})});return {state:pqState,rows};}
};

// Diagnostic-only append to a hash-verified immutable module response.
// Never imported by production. Runtime semantic observations are not finalization.
const censusGeometryCache=new Map(),censusObjectIds=new WeakMap();let censusNextId=0;const censusIdentity=o=>{if(!o)return null;if(!censusObjectIds.has(o))censusObjectIds.set(o,++censusNextId);return censusObjectIds.get(o)};
const censusSha=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new Uint8Array(a.buffer,a.byteOffset,a.byteLength)))).map(v=>v.toString(16).padStart(2,'0')).join('');
const censusUserData=(x,depth=0)=>{
 if(x===null||['string','number','boolean'].includes(typeof x))return x;
 if(depth>3)return '[nested]';
 if(Array.isArray(x))return x.slice(0,100).map(v=>censusUserData(v,depth+1));
 if(typeof x==='object'&&Object.getPrototypeOf(x)===Object.prototype)return Object.fromEntries(Object.entries(x).filter(([k,v])=>typeof v!=='function').map(([k,v])=>[k,censusUserData(v,depth+1)]));
 return '[nonplain]';
};
const censusVisible=o=>{let p=o;while(p){if(!p.visible)return false;if(p===scene)return true;p=p.parent;}return false;};
async function censusGeometry(g){
 const attributes=Object.entries(g.attributes),signature=JSON.stringify([attributes.map(([n,a])=>[n,censusIdentity(a),censusIdentity(a.array||a.data?.array),a.version,a.data?.version,a.count,a.itemSize,a.normalized,a.array?.byteLength,a.data?.array?.byteLength]),censusIdentity(g.index),censusIdentity(g.index?.array),g.index?.version,g.index?.count,g.drawRange,g.groups]);
 const old=censusGeometryCache.get(g);if(old?.signature===signature)return old.record;
 const record={id:g.uuid,attributes:{},index:null,drawRange:{start:g.drawRange.start,count:Number.isFinite(g.drawRange.count)?g.drawRange.count:'Infinity'},groups:g.groups.map(v=>({...v})),morphAttributeNames:Object.keys(g.morphAttributes)};
 for(const [name,a]of attributes){const data=a.array||a.data?.array;record.attributes[name]={sha256:await censusSha(data),arrayType:data.constructor.name,bytes:data.byteLength,count:a.count,itemSize:a.itemSize,normalized:a.normalized,version:a.version??null,interleaved:!!a.isInterleavedBufferAttribute,stride:a.data?.stride??null,offset:a.offset??null,hashScope:a.isInterleavedBufferAttribute?'entire interleaved backing array':'complete attribute typed-array bytes'};}
 if(g.index)record.index={sha256:await censusSha(g.index.array),count:g.index.count,arrayType:g.index.array.constructor.name,version:g.index.version};
 censusGeometryCache.set(g,{signature,record});return record;
}
function censusCollections(o){const list=[];for(const [n,a]of [['source',source],['exterior',exterior],['premiumFace',premiumFace?.meshes||[]],['leather',leatherDetails?.meshes||[]],['openPlates',openPlates],['craftParts',craftParts],['backplate',backplate?.mesh?[backplate.mesh]:[]],['floor',floor?[floor]:[]]]){const i=a.indexOf(o);if(i>=0)list.push({name:n,index:i});}return list;}
window.runtime421Snapshot=async label=>{
 if(clock.snapshot().running.hands||clock.snapshot().running.mechanism)throw Error('Snapshot requires both clocks paused');
 scene.updateMatrixWorld(true);const meshes=[];scene.traverse(o=>{if(o.isMesh)meshes.push(o)});
 const original=meshes.map(o=>o.visible),enabled=mechanismBatch.snapshot().enabled,suppressed=new Set(),activeProxies=[];
 mechanismBatch.setEnabled(true);censusManualProbe=true;
 try{mechanismBatch.beforeRender();meshes.forEach((o,i)=>{if(original[i]&&!o.visible)suppressed.add(o.uuid);if(o.isBatchedMesh&&o.visible)activeProxies.push(o.uuid)});}finally{mechanismBatch.afterRender();mechanismBatch.setEnabled(enabled);censusManualProbe=false}
 if(meshes.some((o,i)=>o.visible!==original[i]))throw Error('Census changed source visibility');
 const geometryMap=new Map(),rows=[];
 for(const o of meshes){if(!geometryMap.has(o.geometry.uuid))geometryMap.set(o.geometry.uuid,await censusGeometry(o.geometry));const materials=(Array.isArray(o.material)?o.material:[o.material]).map(m=>({id:m.uuid,name:m.name,type:m.type,color:m.color?.toArray(),roughness:m.roughness,metalness:m.metalness,transmission:m.transmission,opacity:m.opacity,transparent:m.transparent,side:m.side,depthWrite:m.depthWrite,maps:Object.fromEntries(['map','normalMap','roughnessMap','metalnessMap','alphaMap'].map(k=>[k,m[k]?{id:m[k].uuid,name:m[k].name,width:m[k].image?.width??null,height:m[k].image?.height??null,channel:m[k].channel}:null]))}));rows.push({id:o.uuid,name:o.name,userData:censusUserData(o.userData),collections:censusCollections(o),parent:o.parent?.uuid??null,parentName:o.parent?.name??null,geometry:o.geometry.uuid,materials,visible:o.visible,effectivelyVisible:censusVisible(o),batchSuppressedSource:suppressed.has(o.uuid),isBatchedMesh:!!o.isBatchedMesh,isInstancedMesh:!!o.isInstancedMesh,worldMatrix:o.matrixWorld.elements.slice(),layers:o.layers.mask,renderOrder:o.renderOrder});}
 const gl=renderer.getContext(),e=gl.getExtension('WEBGL_debug_renderer_info');
 return {label,url:location.href,clock:clock.snapshot(),crown:crownInteraction.snapshot(),camera:camera.matrixWorld.elements.slice(),projection:camera.projectionMatrix.elements.slice(),threeRevision:THREE.REVISION,webgl2:gl instanceof WebGL2RenderingContext,renderer:e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),batch:mechanismBatch.snapshot(),activeProxyIds:activeProxies,rows,geometries:[...geometryMap.values()],captureSource:captureConfiguration().sourceAtCapture,inspection:assemblyInspect(),scope:'Executed semantic census only; visibility is scene-graph visibility, not occlusion; no object finalization or physical GPU claim'};
};
window.runtime421Freeze=()=>{cancelCrownGesture();bottleneckQA.freeze();settingSeconds=0;applyClockPose(clock.seek(0));crownVisual?.finish();dirty=true;};
// Toggle-only batch control for calendar calibration. Unlike bottleneckQA.sample,
// this deliberately does not call visibility(), updateMaterials(), or applyClockPose().
window.runtime421ToggleBatch=async enabled=>{
 if(typeof enabled!=='boolean')throw Error('Boolean batch state required');
 const before=renderer.info.render.frame;mechanismBatch.setEnabled(enabled);dirty=true;
 await new Promise(resolve=>{const wait=()=>renderer.info.render.frame>before?resolve():requestAnimationFrame(wait);requestAnimationFrame(wait)});
 return mechanismBatch.snapshot();
};
// Layer overview can start a camera tween. Wait for a stable rendered camera pose
// rather than taking the next frame as the overview baseline.
window.runtime421WaitStableCamera=async()=>{
 let previous=null,stable=0;const deadline=performance.now()+10000;
 while(performance.now()<deadline){await new Promise(requestAnimationFrame);const now=[...camera.matrixWorld.elements,...camera.projectionMatrix.elements];
  if(previous&&now.every((v,i)=>Math.abs(v-previous[i])<1e-9))stable++;else stable=0;
  if(stable>=4)return {stableFrames:stable+1,camera:now};previous=now;
 }
 throw Error('Camera did not settle within 10 seconds');
};
window.runtime421Calendar=async seconds=>{
 if(!Number.isFinite(seconds))throw Error('Finite calendar time required');
 if(clock.snapshot().running.hands||clock.snapshot().running.mechanism)throw Error('Pause both clocks');
 const matches=source.filter(m=>[148,159].includes(m.userData.sourceIndex));if(matches.length!==2)throw Error('Exact spring IDs unavailable');
 const state=calendar.apply(seconds);dirty=true;
 const before=renderer.info.render.frame;await new Promise(resolve=>{const wait=()=>renderer.info.render.frame>before?resolve():requestAnimationFrame(wait);requestAnimationFrame(wait)});
 return {scope:'Direct calendar-only override, not synchronized full clock or physical kinematics',seconds,state,snapshot:await runtime421Snapshot('calendar-'+seconds)};
};

// Observe actual render hooks without altering eligibility or geometry. Bounded at 16 calls.
let censusManualProbe=false;
const censusEarlyFrames=[],censusHookInstall=mechanismBatch.snapshot();
const censusOriginalBefore=mechanismBatch.beforeRender.bind(mechanismBatch);
mechanismBatch.beforeRender=function(...args){
 const sample=!censusManualProbe&&censusEarlyFrames.length<16;
 const springs=sample?source.filter(m=>[148,159].includes(m.userData.sourceIndex)):[];
 const rows=springs.map(m=>({mesh:m,sourceIndex:m.userData.sourceIndex,geometry:m.geometry.uuid,positionVersion:m.geometry.attributes.position.version,normalVersion:m.geometry.attributes.normal.version,position:m.geometry.attributes.position.array.slice(),normal:m.geometry.attributes.normal.array.slice(),visible:m.visible,effectivelyVisible:censusVisible(m)}));
 const result=censusOriginalBefore(...args);
 if(sample&&rows.length)censusEarlyFrames.push({renderFrame:renderer.info.render.frame,clock:clock.snapshot(),batch:mechanismBatch.snapshot(),rows:rows.map(r=>{const suppressed=r.visible&&!r.mesh.visible;delete r.mesh;return {...r,suppressedIntoBatch:suppressed}})});
 return result;
};
window.runtime421EarlyFrames=async()=>({hookInstall:censusHookInstall,scope:'First bounded actual beforeRender hook calls; full spring buffers hashed without changing render eligibility',frames:await Promise.all(censusEarlyFrames.map(async f=>({...f,rows:await Promise.all(f.rows.map(async r=>{const {position,normal,...meta}=r;return {...meta,positionSha256:await censusSha(position),normalSha256:await censusSha(normal),positionCount:position.length/3}}))}))) });

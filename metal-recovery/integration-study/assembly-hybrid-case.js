// PRIVATE integration preparation. Geometry acceptance remains pending.
import {CASE_SOURCE_BUFFERS} from './assembly-parametric-case-source.js';
import {HYBRID_CASE_DATA as DEFAULT_DATA} from './assembly-hybrid-case-data.js';
import {loadGLTFAsset} from './assembly-loading.js';
const bytes=a=>new Uint8Array(a.array.buffer,a.array.byteOffset,a.array.byteLength);
const sha=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),x=>x.toString(16).padStart(2,'0')).join('');
const identity=m=>m?.elements?.every((v,i)=>v===(i%5===0?1:0));
const attr=(g,n)=>n==='index'?g.index:g.attributes[n];
function resources(root){const geometries=new Set(),materials=new Set(),textures=new Set();root.traverse(o=>{if(!o.isMesh)return;geometries.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material])if(m){materials.add(m);for(const v of Object.values(m))if(v?.isTexture)textures.add(v);}});return {geometries,materials,textures};}
function releaseCandidate(root,protectedResources){if(!root)return;const r=resources(root),errors=[];for(const kind of ['geometries','materials','textures'])for(const x of r[kind])if(!protectedResources[kind].has(x))try{x.dispose();}catch(e){errors.push(e);}if(errors.length)throw new AggregateError(errors,'Candidate cleanup failed.');}
export function loadHybridCaseAsset(options={},data=DEFAULT_DATA){return loadGLTFAsset(data.url,{disposeUnused:gltf=>releaseCandidate(gltf.scene,{geometries:new Set(),materials:new Set(),textures:new Set()}),...options,expectedSHA256:data.glbSHA256});}
export async function installHybridCase(root,{loadCandidate,signal,privateStudy=false,data=DEFAULT_DATA}={}){
 signal?.throwIfAborted();
 if(data.acceptance!=='verified'&&!privateStudy)throw Error('Hybrid CASE has not passed release acceptance.');
 if(typeof loadCandidate!=='function')throw TypeError('A verified candidate loader is required.');
 const cases=[];root.traverse(o=>{if(o.isMesh&&o.userData?.assemblyId==='CASE')cases.push(o);});
 if(cases.length!==1)throw Error('Expected exactly one original CASE mesh.');
 const mesh=cases[0],original=mesh.geometry,material=mesh.material,protectedResources=resources(root);mesh.updateMatrix();
 if(!identity(mesh.matrix))throw Error('Unexpected source CASE local transform.');
 const sourceFields={position:CASE_SOURCE_BUFFERS.POSITION,normal:CASE_SOURCE_BUFFERS.NORMAL,uv:CASE_SOURCE_BUFFERS.TEXCOORD_0,index:CASE_SOURCE_BUFFERS.indices};
 const snapshots=[];
 for(const [name,spec] of Object.entries(sourceFields)){
  const a=attr(original,name),Type=name==='index'?Uint16Array:Float32Array;
  if(!a||a.isInterleavedBufferAttribute||a.normalized||a.itemSize!==spec.itemSize||a.count!==spec.count||!(a.array instanceof Type))throw Error(`Unexpected source CASE ${name} layout; refinements must not stack.`);
  const snapshot=bytes(a).slice();if(await sha(snapshot)!==spec.sha256)throw Error(`Unexpected source CASE ${name} hash; cap/R5/hybrid refinements must not stack.`);snapshots.push({name,a,snapshot});
 }
 const unchanged=()=>{mesh.updateMatrix();return mesh.geometry===original&&mesh.material===material&&identity(mesh.matrix)&&snapshots.every(s=>attr(original,s.name)===s.a&&bytes(s.a).length===s.snapshot.length&&bytes(s.a).every((b,i)=>b===s.snapshot[i]));};
 signal?.throwIfAborted();if(!unchanged())throw Error('Source CASE changed during preparation.');
 let loadedRoot,candidate;
 try{
  const loaded=await loadCandidate();loadedRoot=(loaded.gltf||loaded).scene;
  if(!loadedRoot?.traverse)throw Error('Candidate scene is required.');
  signal?.throwIfAborted();
  if(loaded.metrics?.verifiedSHA256!==data.glbSHA256)throw Error('Candidate transfer digest was not verified.');
  const meshes=[];loadedRoot.traverse(o=>{if(o.isMesh)meshes.push(o);});loadedRoot.updateMatrixWorld(true);
  if(meshes.length!==1||meshes[0].userData?.assemblyId!=='CASE')throw Error('Candidate must contain only CASE.');
  const m=meshes[0];m.updateMatrix();if(!identity(m.matrix)||!identity(m.matrixWorld))throw Error('Unexpected candidate transform.');
  if(protectedResources.geometries.has(m.geometry))throw Error('Candidate aliases baseline geometry.');
  if(Object.keys(m.geometry.morphAttributes).length||Object.keys(m.geometry.attributes).some(k=>!Object.hasOwn(data.fields,k)))throw Error('Unexpected unverified candidate attributes.');
  for(const [name,spec] of Object.entries(data.fields)){
   const a=attr(m.geometry,name),Type=name==='index'?Uint32Array:Float32Array;
   if(!a||a.isInterleavedBufferAttribute||a.normalized||a.itemSize!==spec.itemSize||a.count!==spec.count||!(a.array instanceof Type))throw Error(`Candidate ${name} layout mismatch.`);
   if(await sha(bytes(a))!==spec.sha256)throw Error(`Candidate ${name} digest mismatch.`);
  }
  const ix=m.geometry.index.array,n=m.geometry.attributes.position.count;
  if(ix.length%3||ix.some(i=>i>=n))throw Error('Candidate topology index range invalid.');
  if(['position','normal','uv'].some(k=>!attr(m.geometry,k).array.every(Number.isFinite)))throw Error('Candidate attributes are not finite.');
  signal?.throwIfAborted();if(!unchanged())throw Error('Source CASE changed during preparation.');
  candidate=m.geometry.clone();candidate.clearGroups();candidate.computeBoundingBox();candidate.computeBoundingSphere();
  // No candidate material/texture is installed. Existing finish registries retain ownership.
  const temporaryRoot=loadedRoot;loadedRoot=null;releaseCandidate(temporaryRoot,protectedResources);
  signal?.throwIfAborted();if(!unchanged())throw Error('Source CASE changed before installation.');
  mesh.geometry=candidate;
 }catch(error){candidate?.dispose();try{releaseCandidate(loadedRoot,protectedResources);}catch(cleanup){throw new AggregateError([error,cleanup],'Hybrid preparation and cleanup failed.');}throw error;}
 let disposed=false;
 return {mesh,audit:Object.freeze({revision:data.revision,privateOnly:data.acceptance!=='verified',glbSHA256:data.glbSHA256,triangles:candidate.index.count/3,capRadiusMM:data.capsRadiusMM,sourceMaterialPreserved:true,fixedGeometry:true}),
  get active(){return !disposed&&mesh.geometry===candidate;},get ownsGeometry(){return !disposed&&mesh.geometry===candidate;},
  dispose(){if(disposed)return;disposed=true;if(mesh.geometry===candidate)mesh.geometry=original;candidate.dispose();}};
}

import * as THREE from './vendor/three.module.js';
export const PHOTO_LEATHER_ASSETS=Object.freeze({photo:'quality-study/leather-craft-r09.glb',craft:'quality-study/leather-craft-r10.glb',craft10:'quality-study/leather-craft-r10.glb',craft11:'quality-study/leather-craft-r11.glb',craft12:'quality-study/leather-r12/leather.gltf',craft12ktx:'quality-study/leather-r12/leather.gltf'});
export function leatherAnisotropy(quality,maxSupported=1){const limit=Number.isFinite(maxSupported)?Math.max(1,Math.floor(maxSupported)):1;return Math.min(limit,quality==='efficient'?2:['detail','studio'].includes(quality)?16:8);}
export const photoLeatherAsset=variant=>Object.hasOwn(PHOTO_LEATHER_ASSETS,variant)?PHOTO_LEATHER_ASSETS[variant]:null;
/** Authored PBR candidate. Owns private copies, including textures. */
export function createPhotoLeatherDetails({candidateScene,originalStraps=[],shadow='baseline',anisotropy=1}){
 const group=new THREE.Group(),meshes=[],geometries=new Set(),materials=new Map(),textures=new Map(),previous=new Map(),revisions=new Set();let enabled=false,disposed=false,backfaceMaterials=0,unshadowedLiningMeshes=0,mixedLiningMeshesSkipped=0;
 let effectiveAnisotropy=Number.isFinite(anisotropy)?Math.max(1,Math.min(16,Math.floor(anisotropy))):1;
 group.name='Aerial photographed leather';candidateScene.updateMatrixWorld(true);
 const material=(source,backface=false)=>{
  // Keep separate clones if a source material is shared with stitch geometry.
  const cacheKey=backface?`${source.uuid}/r11-backface-shadow`:source;
  if(materials.has(cacheKey))return materials.get(cacheKey);
  const copy=source.clone();
  if(backface){copy.shadowSide=THREE.BackSide;backfaceMaterials++;}
  for(const key of Object.keys(copy))if(copy[key]?.isTexture){const t=copy[key];if(!textures.has(t)){const c=t.clone();c.anisotropy=effectiveAnisotropy;c.needsUpdate=true;textures.set(t,c);}copy[key]=textures.get(t);}
  materials.set(cacheKey,copy);return copy;
 };
 const release=()=>{geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());};
 try{
  candidateScene.traverse(source=>{
   if(!source.isMesh)return;let owner=source;while(owner&&!owner.userData.designPart)owner=owner.parent;
   if(!owner||!['QUALITY-STRAP','QUALITY-STITCH'].includes(owner.userData.designPart)||!['R09','R10','R11','R12'].includes(owner.userData.leatherPbrRevision)||source.userData.sourceIndex!==undefined)throw Error('Unexpected photographed leather candidate');
   revisions.add(owner.userData.leatherPbrRevision);
   const geometry=source.geometry.clone();geometries.add(geometry);
   const backface=shadow==='backface'&&owner.userData.leatherPbrRevision==='R11'&&owner.userData.designPart==='QUALITY-STRAP';
   const mesh=new THREE.Mesh(geometry,Array.isArray(source.material)?source.material.map(m=>material(m,backface)):material(source.material,backface));mesh.name=source.name;mesh.matrix.copy(source.matrixWorld);mesh.matrixAutoUpdate=false;mesh.userData={...owner.userData,...source.userData};mesh.castShadow=true;mesh.receiveShadow=true;mesh.visible=false;group.add(mesh);meshes.push(mesh);
   if(shadow==='lining-unshadowed'&&owner.userData.leatherPbrRevision==='R11'&&owner.userData.designPart==='QUALITY-STRAP'){
    const lining=(Array.isArray(mesh.material)?mesh.material:[mesh.material]).map(m=>/^lining(?:\s|\/)/i.test(m.name));
    // GLTFLoader splits R11 primitives by material. Never disable receiving
    // for unrelated surfaces if a different caller supplies a mixed mesh.
    if(lining.every(Boolean)){mesh.receiveShadow=false;unshadowedLiningMeshes++;}
    else if(lining.some(Boolean))mixedLiningMeshesSkipped++;
   }
  });
  const ids=new Set(meshes.filter(m=>m.userData.designPart==='QUALITY-STRAP').map(m=>m.userData.replacesAssemblyId));
  if(revisions.size>1)throw Error('Mixed photographed leather revisions');
  if(ids.size!==2||!ids.has('STRAP-UPPER')||!ids.has('STRAP-LOWER'))throw Error('Incomplete photographed strap pair');
 }catch(error){release();throw error;}
 const setEnabled=value=>{if(disposed)return;value=!!value;if(value&&!enabled)originalStraps.forEach(m=>previous.set(m,m.visible));if(value)originalStraps.forEach(m=>m.visible=false);else if(enabled){previous.forEach((v,m)=>m.visible=v);previous.clear();}enabled=value;meshes.forEach(m=>m.visible=value);};
 const shadowAudit=Object.freeze({requested:shadow==='backface'||shadow==='lining-unshadowed',mode:shadow==='backface'||shadow==='lining-unshadowed'?shadow:'baseline',active:backfaceMaterials>0||unshadowedLiningMeshes>0,materialCount:backfaceMaterials,unshadowedLiningMeshes,mixedLiningMeshesSkipped,scope:'Opt-in private R11 strap shadow diagnostic only; visible materials and stitches unchanged'});
 return {group,meshes,setAnisotropy(value){if(disposed)return;const next=Number.isFinite(value)?Math.max(1,Math.min(16,Math.floor(value))):1;if(next===effectiveAnisotropy)return;effectiveAnisotropy=next;textures.forEach(t=>{t.anisotropy=next;t.needsUpdate=true;});},get filtering(){return {anisotropy:effectiveAnisotropy,textureCount:textures.size,textures:[...textures.values()].map(t=>({name:t.name,compressed:!!t.isCompressedTexture,width:t.image?.width,height:t.image?.height,format:t.format,colorSpace:t.colorSpace,mipLevels:t.mipmaps?.length||0,anisotropy:t.anisotropy}))};},revision:[...revisions][0],shadowAudit,materialFor:m=>m.material,setEnabled,dispose(){if(disposed)return;setEnabled(false);disposed=true;group.removeFromParent();release();group.clear();}};
}

import * as THREE from './vendor/three.module.js';
/** Authored PBR candidate. Owns private copies, including textures. */
export function createPhotoLeatherDetails({candidateScene,originalStraps=[]}){
 const group=new THREE.Group(),meshes=[],geometries=new Set(),materials=new Map(),textures=new Map(),previous=new Map();let enabled=false,disposed=false;
 group.name='Aerial R09 photographed leather';candidateScene.updateMatrixWorld(true);
 const material=source=>{
  if(materials.has(source))return materials.get(source);
  const copy=source.clone();
  for(const key of Object.keys(copy))if(copy[key]?.isTexture){const t=copy[key];if(!textures.has(t)){const c=t.clone();c.needsUpdate=true;textures.set(t,c);}copy[key]=textures.get(t);}
  materials.set(source,copy);return copy;
 };
 const release=()=>{geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());};
 try{
  candidateScene.traverse(source=>{
   if(!source.isMesh)return;let owner=source;while(owner&&!owner.userData.designPart)owner=owner.parent;
   if(!owner||!['QUALITY-STRAP','QUALITY-STITCH'].includes(owner.userData.designPart)||owner.userData.leatherPbrRevision!=='R09'||source.userData.sourceIndex!==undefined)throw Error('Unexpected photographed leather candidate');
   const geometry=source.geometry.clone();geometries.add(geometry);
   const mesh=new THREE.Mesh(geometry,Array.isArray(source.material)?source.material.map(material):material(source.material));mesh.name=source.name;mesh.matrix.copy(source.matrixWorld);mesh.matrixAutoUpdate=false;mesh.userData={...owner.userData,...source.userData};mesh.castShadow=true;mesh.receiveShadow=true;mesh.visible=false;group.add(mesh);meshes.push(mesh);
  });
  const ids=new Set(meshes.filter(m=>m.userData.designPart==='QUALITY-STRAP').map(m=>m.userData.replacesAssemblyId));
  if(ids.size!==2||!ids.has('STRAP-UPPER')||!ids.has('STRAP-LOWER'))throw Error('Incomplete photographed strap pair');
 }catch(error){release();throw error;}
 const setEnabled=value=>{if(disposed)return;value=!!value;if(value&&!enabled)originalStraps.forEach(m=>previous.set(m,m.visible));if(value)originalStraps.forEach(m=>m.visible=false);else if(enabled){previous.forEach((v,m)=>m.visible=v);previous.clear();}enabled=value;meshes.forEach(m=>m.visible=value);};
 return {group,meshes,materialFor:m=>m.material,setEnabled,dispose(){if(disposed)return;setEnabled(false);disposed=true;group.removeFromParent();release();group.clear();}};
}

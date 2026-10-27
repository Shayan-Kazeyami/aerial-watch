import * as THREE from './vendor/three.module.js';
import {createAssemblyMaterials} from './assembly-materials.js';
export const LEATHER_CRAFT_ROLES=Object.freeze(['leather','lining','edgepaint','thread']);
export const LEATHER_CRAFT_FINISH=Object.freeze({leather:{linearColor:[.025,.031,.035],roughness:.59},lining:{linearColor:[.12,.061,.031],roughness:.77},edgepaint:{linearColor:[.014,.018,.020],roughness:.47},thread:{linearColor:[.075,.080,.078],roughness:.83}});
export function leatherMaterialRole(name){for(const [r,re] of [['leather',/fine pebble graphite calf/i],['lining',/warm fine lining/i],['edgepaint',/thin burnished edge paint/i],['thread',/charcoal linen thread/i]])if(re.test(name))return r;throw Error(`Unknown authored leather material: ${name}`);}
/** Private copies own their resources. Loaded GLB can be disposed after construction. */
export function createLeatherDetails({candidateScene,originalStraps=[]}){
 const group=new THREE.Group(),meshes=[],geometries=new Set(),materials=new Map(),previous=new Map(),finishes=createAssemblyMaterials(null);let enabled=false,disposed=false;
 group.name='Aerial R05 leather craft';candidateScene.updateMatrixWorld(true);
 const get=role=>{
  if(materials.has(role))return materials.get(role);
  const m=role==='edgepaint'?new THREE.MeshPhysicalMaterial():finishes.apply({userData:{finishKind:role}}).clone();
  // R05's saved native warm lining is plain. Keep its cloned finish settings,
  // but do not transfer the generic lining preset's exterior leather grain.
  if(role!=='edgepaint'&&role!=='lining'){
   const reference=finishes.apply({userData:{finishKind:role}});m.onBeforeCompile=reference.onBeforeCompile;m.customProgramCacheKey=reference.customProgramCacheKey;
   if(role==='leather'){
    const compile=m.onBeforeCompile;m.onBeforeCompile=shader=>{compile(shader);shader.fragmentShader=shader.fragmentShader.replace('p*4.8','p*7.').replace('p*28.','p*31.').replace('.65*pores+.35*fine','.78*pores+.22*fine').replace('-.025*finishGrad','-.014*finishGrad').replace('.08500','.12000');};m.customProgramCacheKey=()=> 'aerial-leather-r05-7-31-v1';
   }
  }
  const spec=LEATHER_CRAFT_FINISH[role];m.color.setRGB(...spec.linearColor);m.roughness=spec.roughness;m.metalness=0;m.name=`Aerial R05 / ${role}`;m.userData.finish=role;materials.set(role,m);return m;
 };
 try{
  candidateScene.traverse(source=>{
   if(!source.isMesh)return;let owner=source;while(owner&&!owner.userData.designPart)owner=owner.parent;
   if(!owner||!['QUALITY-STRAP','QUALITY-STITCH'].includes(owner.userData.designPart))throw Error('Unexpected leather candidate mesh');
   const roles=(Array.isArray(source.material)?source.material:[source.material]).map(m=>leatherMaterialRole(m.name));
   const g=source.geometry.clone();geometries.add(g);const mesh=new THREE.Mesh(g,Array.isArray(source.material)?roles.map(get):get(roles[0]));mesh.name=source.name;mesh.matrix.copy(source.matrixWorld);mesh.matrixAutoUpdate=false;mesh.userData={...owner.userData,...source.userData,finishKind:roles[0],leatherRoles:roles};delete mesh.userData.finishKinds;mesh.castShadow=true;mesh.receiveShadow=true;mesh.visible=false;group.add(mesh);meshes.push(mesh);
  });
  const ids=new Set(meshes.filter(m=>m.userData.designPart==='QUALITY-STRAP').map(m=>m.userData.replacesAssemblyId));
  if(ids.size!==2||!ids.has('STRAP-UPPER')||!ids.has('STRAP-LOWER')||!LEATHER_CRAFT_ROLES.every(r=>materials.has(r)))throw Error('Incomplete two-strap leather candidate');
 }catch(e){geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());finishes.dispose();throw e;}
 const setEnabled=value=>{if(disposed)return;value=!!value;if(value&&!enabled)originalStraps.forEach(m=>previous.set(m,m.visible));if(value)originalStraps.forEach(m=>m.visible=false);else if(enabled){previous.forEach((v,m)=>m.visible=v);previous.clear();}enabled=value;meshes.forEach(m=>m.visible=value);};
 return {group,meshes,materialFor:m=>m.material,setEnabled,dispose(){if(disposed)return;setEnabled(false);disposed=true;group.removeFromParent();geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());finishes.dispose();group.clear();}};
}

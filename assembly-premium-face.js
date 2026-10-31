import * as THREE from './vendor/three.module.js';

export const PREMIUM_HIDDEN_SOURCES = Object.freeze([0, 149, 155]);
export function premiumFaceVisible({enabled, openWork, movementOnly, isolated, interior}) {
  return !!enabled && !!openWork && !movementOnly && !isolated && !interior;
}
/** Authored dial overlay, not a replacement movement. Model mount matches baseline glTF. */
export function preparePremiumFace(root) {
  const meshes=[];
  root.traverse(mesh=>{
    if(!mesh.isMesh)return;
    if(mesh.userData.premiumFacePart!==true || mesh.userData.sourceIndex!==undefined)throw new Error('Invalid premium face asset: expected authored face parts only.');
    meshes.push(mesh);mesh.castShadow=true;mesh.receiveShadow=true;
  });
  if(!meshes.length)throw new Error('Premium face asset contains no meshes.');
  let texture;
  if(typeof document!=='undefined'){
    const canvas=document.createElement('canvas');canvas.width=canvas.height=256;
    const context=canvas.getContext('2d');
    if(context){
      const pixels=context.createImageData(256,256);let seed=29;
      for(let i=0;i<pixels.data.length;i+=4){seed=(Math.imul(seed,1664525)+1013904223)>>>0;const c=110+(seed>>>27);pixels.data.set([c,c,c,255],i);}
      context.putImageData(pixels,0,0);texture=new THREE.CanvasTexture(canvas);texture.wrapS=texture.wrapT=THREE.RepeatWrapping;texture.repeat.set(20,20);texture.name='Fine charcoal grain';
    }
  }
  const materials=new Set(meshes.flatMap(m=>Array.isArray(m.material)?m.material:[m.material]));
  for(const material of materials){
    if(/Graphite/i.test(material.name)){
      material.color.setHex(0x19191b);material.metalness=.12;material.roughness=.48;
      if(texture){material.bumpMap=texture;material.bumpScale=.025;}
    }
    if(/champagne/i.test(material.name)){material.color.setHex(0xb89b70);material.metalness=.85;material.roughness=.26;}
  }
  root.visible=false;
  return {root,meshes,texture,revision:'B-02'};
}

/** Restrained appearance of the approved B reference; original BOM is untouched. */
export function premiumMovementFinishKind(data={}, name='') {
  if(data.sourceIndex===undefined)return null;
  const label=`${data.description||''} ${name}`.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  if(/\bpierre\b|contre pivot|cheville de plateau|^palette/.test(label))return 'steel';
  if(/serge de balancier|planche/.test(label))return 'steel';
  return null;
}

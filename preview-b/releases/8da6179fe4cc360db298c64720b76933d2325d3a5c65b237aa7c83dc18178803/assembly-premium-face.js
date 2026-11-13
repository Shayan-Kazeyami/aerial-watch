import {bindGraphiteFragmentValidity} from './assembly-fragment-validity.js';
import {createTickBatch} from './assembly-premium-tick-batch.js';
import * as THREE from './vendor/three.module.js';
import {createMarkerBevelNormals} from './assembly-marker-bevel-normals.js';

export const premiumFaceAsset=variant=>variant==='svg04'?'premium-face/face-svg04.glb?v=constant04':variant==='svg03'?'quality-study/face-svg03-rim-candidate.glb':variant==='svg'?'premium-face/face-svg-b.glb?v=svg02':'premium-face/face-b.glb';
export const PREMIUM_HIDDEN_SOURCES = Object.freeze([0, 149, 155]);
// Rear inspection removes the rear cover, not the selected front design.
export function premiumFaceVisible({enabled, openWork, movementOnly, isolated, interior}) {
  return !!enabled && !!openWork && !movementOnly && !isolated;
}
/**
 * SVG04's authored planar UVs span 32.8 mm in both directions. Bake continuous,
 * straight brushing into a single data map: R = height, G = roughness.
 * No albedo grain, geometry edits, shader noise, or animation-time work.
 */
export function createBrushedFaceTexture() {
  const size=1024,data=new Uint8Array(size*size*4);
  let seed=0x4a03;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296*2-1;};
  // Continuous straight abrasion, not independent short noise patches. The
  // .128/.224 mm components survive phone-size mip filtering; .064 mm detail
  // is secondary. Gentle 8.2 mm envelope variation never reverses a strand.
  const layers=[[4,.62],[7,.23],[2,.15]].map(([spacing,weight])=>{
    const width=Math.ceil(size/spacing);
    return {spacing,weight,width,values:Float32Array.from({length:width},random)};
  });
  const smooth=t=>t*t*(3-2*t),profile=new Float32Array(size);
  for(let x=0;x<size;x++)for(const {spacing,weight,width,values} of layers){
    const gx=x/spacing,ix=Math.floor(gx),t=smooth(gx-ix);
    profile[x]+=(values[ix%width]*(1-t)+values[(ix+1)%width]*t)*weight;
  }
  const mean=profile.reduce((sum,v)=>sum+v,0)/size;
  const envelopes=Float32Array.from({length:4},random);
  for(let y=0;y<size;y++){
    const gy=y/256,iy=Math.floor(gy),t=smooth(gy-iy);
    const envelope=1+.06*(envelopes[iy]*(1-t)+envelopes[(iy+1)%4]*t);
    for(let x=0;x<size;x++){
      const grain=(profile[x]-mean)*envelope,i=(y*size+x)*4;
      data[i]=Math.round(128+grain*48);
      // Preserve .48 mean satin roughness. Shared direction, less contrast
      // than height: broad lighting should not resolve isolated bright dust.
      data[i+1]=Math.round(226+grain*20);
      data[i+2]=0;data[i+3]=255;
    }
  }
  const texture=new THREE.DataTexture(data,size,size,THREE.RGBAFormat,THREE.UnsignedByteType);
  texture.name='SVG04 directional charcoal · height R / roughness G';
  texture.colorSpace=THREE.NoColorSpace;
  texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
  texture.minFilter=THREE.LinearMipmapLinearFilter;texture.magFilter=THREE.LinearFilter;
  texture.generateMipmaps=true;texture.anisotropy=1;texture.needsUpdate=true;
  texture.userData={finish:'brushed',brushRevision:2,spanMm:32.8,texelMm:32.8/size,channels:{r:'height',g:'roughness'}};
  return texture;
}

/** Authored dial overlay, not a replacement movement. Model mount matches baseline glTF. */
export function preparePremiumFace(root,{finish='baseline',smoothMarkers=false,enableTickBatch=false}={}) {
  const meshes=[];
  root.traverse(mesh=>{
    if(!mesh.isMesh)return;
    if(mesh.userData.premiumFacePart!==true || mesh.userData.sourceIndex!==undefined)throw new Error('Invalid premium face asset: expected authored face parts only.');
    meshes.push(mesh);mesh.castShadow=true;mesh.receiveShadow=true;
  });
  if(!meshes.length)throw new Error('Premium face asset contains no meshes.');
  const revisions=new Set(meshes.map(mesh=>mesh.userData.designRevision).filter(Boolean));
  if(revisions.size>1)throw new Error('Invalid premium face asset: mixed design revisions.');
  const revision=[...revisions][0]||'B-02',svgDerived=revision.startsWith('B-SVG-');
  const fineGrain=revision.startsWith('B-SVG-04');
  const brushed=finish==='brushed'&&fineGrain;
  const finishTrial=(finish==='atelier2'||finish==='atelier3')&&fineGrain;
  let texture=brushed?createBrushedFaceTexture():undefined;
  if(!brushed&&typeof document!=='undefined'){
    const canvas=document.createElement('canvas');const size=fineGrain?1024:256;canvas.width=canvas.height=size;
    const context=canvas.getContext('2d');
    if(context){
      const pixels=context.createImageData(size,size);let seed=29;
      for(let i=0;i<pixels.data.length;i+=4){seed=(Math.imul(seed,1664525)+1013904223)>>>0;const c=110+(seed>>>27);pixels.data.set([c,c,c,255],i);}
      context.putImageData(pixels,0,0);texture=new THREE.CanvasTexture(canvas);texture.wrapS=texture.wrapT=THREE.RepeatWrapping;texture.repeat.set(svgDerived?1:20,svgDerived?1:20);texture.name='Fine charcoal grain';
    }
  }
  const materials=new Set(meshes.flatMap(m=>Array.isArray(m.material)?m.material:[m.material]));
  for(const material of materials){
    if(/Graphite/i.test(material.name)){
      bindGraphiteFragmentValidity(material);
      // SVG-derived material scalars come from the inspected Blender export.
      if(!svgDerived){material.color.setHex(0x19191b);material.metalness=.12;material.roughness=.48;}
      // A small linear-light lift retains the exported charcoal hue. The
      // trial is restricted to SVG04; earlier assets keep their authored look.
      if(finishTrial){
        // Optional art-directed charcoal readability study, not measured
        // reflectance. Mutate the Color object using explicit linear values.
        if(finish==='atelier3')material.color.setRGB(.045,.05,.058,THREE.LinearSRGBColorSpace);
        else material.color.multiplyScalar(1.18);
      }
      if(texture){material.bumpMap=texture;material.bumpScale=finishTrial?.003:fineGrain?.008:svgDerived?.12:.025;}
      if(brushed){
        material.color.setRGB(.045,.05,.058,THREE.LinearSRGBColorSpace);
        material.bumpScale=.035;material.roughness=.54;material.roughnessMap=texture;
      }
    }
    if(!svgDerived&&/champagne/i.test(material.name)){material.color.setHex(0xb89b70);material.metalness=.85;material.roughness=.26;}
  }
  const markerNormals=smoothMarkers?meshes.filter(m=>/^SVG[ _]hour-\d{2}$/.test(m.name)).map(createMarkerBevelNormals):[];
  const setMarkerSmoothing=enabled=>markerNormals.forEach(m=>m.setEnabled(enabled));
  setMarkerSmoothing(smoothMarkers);
  const tickBatch=enableTickBatch&&revision==='B-SVG-04'?createTickBatch(root):{supported:false,reason:enableTickBatch?'Not SVG04.':'Not requested.'};
  root.visible=false;
  return {root,meshes,texture,revision,tickBatch,setMarkerSmoothing,markerNormalAudit:markerNormals.map(m=>m.audit)};
}

/** Restrained appearance of the approved B reference; original BOM is untouched. */
export function premiumMovementFinishKind(data={}, name='') {
  if(data.sourceIndex===undefined)return null;
  // Exact verified source identities, before the legacy neutral-bearing
  // appearance rule below. Pallet stones and the roller jewel are not steel.
  if(data.sourceIndex===114||data.sourceIndex===115)return 'palletRuby';
  if(data.sourceIndex===136)return 'ruby';
  // Verified front shock jewels and pallet bearing; adjacent mounts remain metal.
  if([11,12,27].includes(data.sourceIndex))return 'ruby';
  // Verified lower structural bridges, not neighbouring wheel plates/screws.
  // Appearance override only: retain the original source BOM and geometry.
  if(data.sourceIndex===100||data.sourceIndex===141)return 'brass';
  if([4,92,93,106,157].includes(data.sourceIndex))return 'steel';
  const label=`${data.description||''} ${name}`.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  if(/\bpierre\b|contre pivot|cheville de plateau|^palette/.test(label))return 'steel';
  if(/serge de balancier|planche/.test(label))return 'steel';
  return null;
}

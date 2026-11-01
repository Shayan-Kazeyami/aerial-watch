import * as THREE from './vendor/three.module.js';
import {addRefractionEdgeFallback} from './assembly-refraction.js';

// Authored appearance proposals, not a released material BOM. Coordinates and
// grain periods are local millimetres; source geometry/materials stay untouched.
const finishes={
  satin:{color:0xbfc7cd,metalness:1,roughness:.36,texture:'linear',strength:.065},
  steel:{color:0xb6c1ce,metalness:1,roughness:.23,texture:'linear',strength:.025},
  brass:{color:0xcba35c,metalness:1,roughness:.28,texture:'circular',strength:.04},
  spring:{color:0x34435a,metalness:1,roughness:.28,texture:'linear',strength:.015},
  blued:{color:0x1a4d80,metalness:1,roughness:.20,clearcoat:.18,texture:'linear',strength:.015},
  // The bundled renderer's sapphire background pass excludes other
  // transmissive objects. Render small jewels as opaque absorption-coloured
  // dielectrics so a front crystal cannot erase them from its sampled scene.
  // This is a bounded nested-transmission approximation, not a volume solver.
  ruby:{color:0x9d173c,metalness:0,roughness:.105,transmission:0,thickness:.32,ior:1.76,clearcoat:.7},
  // Confirmed OM10-00106 pallet stones: a polished dielectric interface,
  // not steel and not a varnished red metal. The restrained body colour is
  // the same bounded nested-transmission approximation described above.
  // transmission=0 keeps them in the sapphire background pass; this is not
  // a claim of physically opaque ruby or a solved multi-layer optical path.
  palletRuby:{color:0x711d38,metalness:0,roughness:.10,transmission:0,thickness:.31,ior:1.76,specularIntensity:1,clearcoat:0},
  polished:{color:0xd4dbe1,metalness:1,roughness:.115,texture:'linear',strength:.008},
  case:{color:0xb3bec9,metalness:1,roughness:.31,texture:'linear',strength:.04},
  graphite:{color:0x29343a,metalness:.82,roughness:.39,texture:'circular',strength:.035},
  dial:{color:0xe8e2d2,metalness:.08,roughness:.38,texture:'circular',strength:.018},
  ink:{color:0x131b25,metalness:.22,roughness:.25},
  leather:{color:0x242a2e,metalness:0,roughness:.73,sheen:.2,sheenRoughness:.8,sheenColor:0x4c545b,texture:'leather',strength:.085},
  lining:{color:0x70513b,metalness:0,roughness:.86,texture:'leather',strength:.055},
  thread:{color:0x5f6462,metalness:0,roughness:.88},
  // One polished sapphire dielectric interface: no second clearcoat lobe.
  // The small nonzero roughness retains a highlight without unnecessarily
  // selecting blurred transmission mips over the finely printed mechanism.
  crystal:{color:0xffffff,metalness:0,roughness:.006,transmission:1,thickness:.35,ior:1.76,specularIntensity:.28,clearcoat:0},
};

// Optional visual rebuild; units remain millimetres, no invented crystal depth.
export const ATELIER_FINISH_OVERRIDES=Object.freeze({
 crystal:Object.freeze({roughness:.008,specularIntensity:.45,attenuationColor:0xeaf5f3,attenuationDistance:30,dispersion:0}),
 satin:Object.freeze({color:0xb9bec4,roughness:.32,strength:.045}),
 steel:Object.freeze({color:0xc6cbd0,roughness:.20,strength:.018}),
 polished:Object.freeze({color:0xd4d7db,roughness:.085,strength:.004}),
 case:Object.freeze({color:0xb9bec4,roughness:.29,strength:.025}),
 brass:Object.freeze({color:0xc5a56d,roughness:.25,strength:.025}),
});

// Optional studio4 response separation. Source-only overrides distinguish
// broad bridge caps, crisp steel edges and warmer existing brass wheels;
// classification and source geometry are unchanged.
export const STUDIO4_MOVEMENT_FINISHES=Object.freeze({
 satin:Object.freeze({color:0xa9b0b7,roughness:.41,strength:.04}),
 steel:Object.freeze({color:0xc6cbd0,roughness:.19,strength:.015}),
 brass:Object.freeze({color:0xbfa16f,roughness:.30,strength:.02}),
 spring:Object.freeze({color:0x34435a,roughness:.25,strength:.012}),
});
const STUDIO4_EXTERIOR_FINISHES=Object.freeze({
 case:Object.freeze({roughness:.26,strength:.018}),
 polished:Object.freeze({roughness:.13,strength:.004}),
 crystal:Object.freeze({specularIntensity:.30}),
});

// Measured axial extents of the two original solid crystal meshes, in mm.
// Explicit part identity avoids making the rear window optically thicker than
// its geometry; a generic authored crystal still uses the front default.
export const ASSEMBLY_CRYSTAL_THICKNESS_MM=Object.freeze({'FRONT-CRYSTAL':.35,'REAR-CRYSTAL':.30});

// Exposed for reproducible finish comparisons. These are authored appearance
// parameters, not measured spectral reflectance or a manufacturing specification.
export const ASSEMBLY_FINISH_SPECIFICATIONS=Object.freeze(Object.fromEntries(
  Object.entries(finishes).map(([kind,specification])=>[kind,Object.freeze({...specification})]),
));

export function classifyAssemblyMaterial(mesh) {
  const data=mesh.userData||{},id=data.assemblyId||'';
  if(Object.hasOwn(finishes,data.finishKind))return data.finishKind;
  if(data.sourceIndex===114||data.sourceIndex===115)return 'palletRuby';
  const name=`${data.description||''} ${mesh.name||''}`.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  if(data.sourceIndex!==undefined){
    if(/\bpierre\b|contre pivot|cheville de plateau/.test(name)||/^palette(?:\s|$)/.test(name))return 'ruby';
    if(/spiral/.test(name))return 'spring';
    if(/\bpont\b|platine|\bcoq\b|plaque|couvre mecanisme/.test(name))return 'satin';
    if(/pignon|\bvis\b|axe|tige|arbre|goupille|tenon|echappement|roue couronne|ressort|corps d.ancre|double plateau/.test(name))return 'steel';
    if(/planche|roue|barillet|rochet|chaton|lyre|serge de balancier/.test(name))return 'brass';
    return 'steel';
  }
  if(data.inspectionTransparent||/CRYSTAL/.test(id))return 'crystal';
  if(/^(STRAP|KEEPER)/.test(id))return /lining|underside/.test(name)?'lining':'leather';
  if(['HOUR','MINUTE','SECONDS'].includes(id))return 'blued';
  if(['DIAL','CHAPTER'].includes(id))return /mark/.test(name)?'ink':/baton/.test(name)?'polished':id==='DIAL'?'dial':'satin';
  if(/^(BEZEL|CROWN|BUCKLE|BACK-SCREW|SECONDS-STAFF|SPRINGBAR)/.test(id))return 'polished';
  if(id==='DIAL-CARRIER')return 'satin';
  return 'case';
}

// Material.copy intentionally omits custom shader callbacks. Explicitly keep
// these on selection variants so highlighting never erases the finish grain.
export function cloneAssemblyMaterial(material){
  if(Array.isArray(material))return material.map(cloneAssemblyMaterial);
  const clone=material.clone();
  clone.onBeforeCompile=material.onBeforeCompile;
  clone.customProgramCacheKey=material.customProgramCacheKey;
  return clone;
}

function addSurface(material,type,strength,axis=[1,0,0],kind='',faceAxis=[0,1,0]){
  const grainAxis=new THREE.Vector3(...axis).normalize().toArray().map(value=>value.toFixed(6)).join(',');
  const capAxis=faceAxis.map(value=>value.toFixed(6)).join(',');
  material.onBeforeCompile=shader=>{
    shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vFinishPosition;\nvarying vec3 vFinishNormal;')
      .replace('#include <begin_vertex>','#include <begin_vertex>\nvFinishPosition = position;\nvFinishNormal = normal;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
varying vec3 vFinishPosition;
varying vec3 vFinishNormal;
float finishHash(vec3 p){p=fract(p*.1031);p+=dot(p,p.yzx+33.33);return fract((p.x+p.y)*p.z);}
float finishNoise(vec3 p){
  vec3 q=floor(p),f=fract(p);f=f*f*(3.-2.*f);
  return mix(mix(mix(finishHash(q),finishHash(q+vec3(1,0,0)),f.x),mix(finishHash(q+vec3(0,1,0)),finishHash(q+vec3(1,1,0)),f.x),f.y),mix(mix(finishHash(q+vec3(0,0,1)),finishHash(q+vec3(1,0,1)),f.x),mix(finishHash(q+vec3(0,1,1)),finishHash(q+vec3(1,1,1)),f.x),f.y),f.z);
}
float finishWave(float phase){return sin(phase)*(1.-smoothstep(.45,2.5,fwidth(phase)));}
float finishFilteredNoise(vec3 p){return mix(.5,finishNoise(p),1.-smoothstep(.35,1.3,length(fwidth(p))));}
// Fixed projection bases keep a cap's machining direction independent of CAD
// edge-normal interpolation. Aperiodic elongated grain avoids visible ruler-
// straight sinusoidal bands at macro distance; unresolved detail averages out.
float finishLinearField(vec3 p,vec3 planeNormal){
  vec3 travel=vec3(${grainAxis}),tangent=travel-planeNormal*dot(travel,planeNormal);
  if(dot(tangent,tangent)<.01){travel=abs(planeNormal.z)<.8?vec3(0,0,1):vec3(0,1,0);tangent=travel-planeNormal*dot(travel,planeNormal);}
  tangent=normalize(tangent);vec3 across=normalize(cross(planeNormal,tangent));
  float scratch=finishFilteredNoise(vec3(dot(p,across)*145.,dot(p,tangent)*.8,dot(p,planeNormal)*2.));
  ${type==='cross'?'scratch=.65*scratch+.35*finishFilteredNoise(vec3(dot(p,tangent)*120.,dot(p,across)*.8,dot(p,planeNormal)*2.));':''}
  return .5+.22*(scratch-.5)+.06*(finishFilteredNoise(p*45.)-.5);
}
float finishSurface(vec3 p){
  vec3 n=normalize(vFinishNormal),w=pow(abs(n),vec3(6.));w/=max(dot(w,vec3(1.)),.001);
  ${type==='leather'?`float pores=finishFilteredNoise(p*4.8),fine=finishFilteredNoise(p*28.);return .65*pores+.35*fine;`:type==='circular'?`// Blend projected fields, never their phase/radius: changing normal
  // weights must not bend an otherwise circular tool mark across triangles.
  float rings=w.x*finishWave(length(p.yz)*205.)+w.y*finishWave(length(p.xz)*205.)+w.z*finishWave(length(p.xy)*205.);
  return .5+.12*rings+.08*(finishFilteredNoise(p*40.)-.5);`:`return w.x*finishLinearField(p,vec3(1,0,0))+w.y*finishLinearField(p,vec3(0,1,0))+w.z*finishLinearField(p,vec3(0,0,1));`}
}
`);
    shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
float finishHeight=finishSurface(vFinishPosition);
roughnessFactor=clamp(roughnessFactor+(finishHeight-.5)*${strength.toFixed(5)},.065,1.);
${kind==='satin'?`// Satin caps and cleaner reflections on actual vertical cut walls.
roughnessFactor=mix(roughnessFactor,.20,smoothstep(.12,.65,1.-abs(dot(normalize(vFinishNormal),vec3(${capAxis})))));`:''}
${type==='leather'?'diffuseColor.rgb *= .91+.16*finishHeight;':''}
`);
    if(type==='leather')shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
vec3 finishQ0=dFdx(-vViewPosition),finishQ1=dFdy(-vViewPosition);
vec3 finishR0=cross(finishQ1,normal),finishR1=cross(normal,finishQ0);
float finishDet=dot(finishQ0,finishR0);
vec3 finishGrad=sign(finishDet)*(dFdx(finishHeight)*finishR0+dFdy(finishHeight)*finishR1);
normal=normalize(abs(finishDet)*normal-.025*finishGrad);
`);
  };
  material.customProgramCacheKey=()=>`om10-finish-v3-${type}-${strength}-${grainAxis}-${kind}-${capAxis}`;
}

// Object-space machining avoids the degenerate imported case UVs and missing
// source UVs. The analytic frame is used by Three's physical anisotropic BRDF;
// this is not texture filtering anisotropy. All lengths below are millimetres.
export const STUDIO4_METAL_MICROFINISH=Object.freeze({
 case:Object.freeze({anisotropy:.22,heightMm:.00035,maxSlope:.012,roughnessVariation:.009}),
 satin:Object.freeze({anisotropy:.18,heightMm:.00035,maxSlope:.012,roughnessVariation:.010}),
 steel:Object.freeze({anisotropy:.12,heightMm:.00015,maxSlope:.008,roughnessVariation:.006}),
 brass:Object.freeze({anisotropy:.18,heightMm:.00025,maxSlope:.010,roughnessVariation:.009}),
 polished:Object.freeze({anisotropy:.035,heightMm:.00004,maxSlope:.003,roughnessVariation:.002}),
});
function addStudioMetalSurface(material,axis,kind,faceAxis){
  const spec=STUDIO4_METAL_MICROFINISH[kind],vector=v=>v.map(x=>x.toFixed(6)).join(',');
  const travel=vector(axis),cap=vector(faceAxis);
  // A fixed perpendicular fallback prevents zero-length frames on end caps.
  const a=new THREE.Vector3(...axis),fallback=new THREE.Vector3(Math.abs(a.x)<.8?1:0,Math.abs(a.x)<.8?0:1,0);
  fallback.addScaledVector(a,-fallback.dot(a)).normalize();const alt=vector(fallback.toArray());
  const frameBranch=/#ifdef USE_TANGENT\n[\s\S]*?\n\t#endif/;
  if(!frameBranch.test(THREE.ShaderChunk.normal_fragment_begin))throw new Error('Studio metal tangent-frame shader anchor changed');
  material.anisotropy=spec.anisotropy;material.anisotropyRotation=0;
  material.userData.microfinish={...spec,revision:2,frame:'analytic-object-space',correlationScalesMm:[.03,.07],field:'nonperiodic-filtered-1d'};
  material.onBeforeCompile=shader=>{
    shader.vertexShader=shader.vertexShader.replace('#include <common>',`#include <common>
varying vec3 vMetalPosition;
varying vec3 vMetalLocalNormal;
varying vec3 vMetalTravel;
varying vec3 vMetalAlternate;`)
      .replace('#include <begin_vertex>',`#include <begin_vertex>
vMetalPosition=position;vMetalLocalNormal=normal;
vMetalTravel=mat3(modelViewMatrix)*vec3(${travel});
vMetalAlternate=mat3(modelViewMatrix)*vec3(${alt});`);
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
varying vec3 vMetalPosition;
varying vec3 vMetalLocalNormal;
varying vec3 vMetalTravel;
varying vec3 vMetalAlternate;
mat3 finishMetalFrame(vec3 n){
  vec3 t=vMetalTravel-n*dot(vMetalTravel,n);
  if(dot(t,t)<.01)t=vMetalAlternate-n*dot(vMetalAlternate,n);
  t=normalize(t);return mat3(t,normalize(cross(n,t)),n);
}
// Small arithmetic hash, not a sinusoidal carrier. Independent strand
// heights have no fixed spacing of bright/dark extrema like the rejected v1.
float finishMetalHash(float x){
  x=fract(x*.1031);x*=x+33.33;x*=x+x;return fract(x)*2.-1.;
}
float finishMetalNoise(float x){
  float cell=floor(x),t=fract(x);t=t*t*(3.-2.*t);
  float value=mix(finishMetalHash(cell),finishMetalHash(cell+1.),t);
  // Resolve grain only when several pixels cover a correlation cell.
  // Unresolved microstructure belongs in the BRDF, not aliasing/shimmer.
  return value*(1.-smoothstep(.18,.65,fwidth(x)));
}
float finishMetalPlane(vec3 p,vec3 planeNormal){
  vec3 t=vec3(${travel})-planeNormal*dot(vec3(${travel}),planeNormal);
  if(dot(t,t)<.01)t=vec3(${alt})-planeNormal*dot(vec3(${alt}),planeNormal);
  t=normalize(t);vec3 across=normalize(cross(planeNormal,t));
  float q=dot(p,across),along=dot(p,t);
  // .03 mm dominant abrasion, .07 mm secondary structure. No long
  // wavelength modulation or periodic lines; macro-only microheight.
  return .78*finishMetalNoise(q/ .03+17.31)+.22*finishMetalNoise(q/ .07-9.73);
}
float finishMetalField(vec3 p){
  vec3 w=pow(abs(normalize(vMetalLocalNormal)),vec3(8.));w/=max(dot(w,vec3(1.)),.0001);
  return w.x*finishMetalPlane(p,vec3(1,0,0))+w.y*finishMetalPlane(p,vec3(0,1,0))+w.z*finishMetalPlane(p,vec3(0,0,1));
}`);
    shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
float metalMicroField=finishMetalField(vMetalPosition);
roughnessFactor=clamp(roughnessFactor+metalMicroField*${spec.roughnessVariation.toFixed(6)},.065,1.);
${kind==='satin'?`roughnessFactor=mix(roughnessFactor,.20,smoothstep(.12,.65,1.-abs(dot(normalize(vMetalLocalNormal),vec3(${cap})))));`:''}`);
    shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_begin>',THREE.ShaderChunk.normal_fragment_begin.replace(frameBranch,'mat3 tbn = finishMetalFrame( normal );'));
    shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
vec3 metalQ0=dFdx(-vViewPosition),metalQ1=dFdy(-vViewPosition);
vec3 metalR0=cross(metalQ1,normal),metalR1=cross(normal,metalQ0);
float metalDet=dot(metalQ0,metalR0);
float metalHeight=metalMicroField*${spec.heightMm.toFixed(6)};
vec3 metalSlope=sign(metalDet)*(dFdx(metalHeight)*metalR0+dFdy(metalHeight)*metalR1)/max(abs(metalDet),1.e-10);
metalSlope*=min(1.,${spec.maxSlope.toFixed(6)}/max(length(metalSlope),1.e-8));
normal=normalize(normal-metalSlope);
#ifdef USE_ANISOTROPY
  tbn=finishMetalFrame(normal);
#endif`);
  };
  material.customProgramCacheKey=()=>`om10-studio4-metal-v2-${kind}-${travel}-${cap}`;
}

// Optional lighting-only A/B. Fresh arrays keep callers from mutating the
// default rig. Do not adopt the trial without matched real-render captures.
export function atelierReflectionCards(light='atelier'){
  if(light==='studio4')return [
    [[-34,26,42],[9,42],0xfff7ed,2.8],
    [[30,5,28],[3.5,44],0xf1f5ff,3.0],
    [[0,48,24],[32,16],0xffffff,1.05],
    [[-25,8,-38],[8,32],0xe5edff,1.5],
    [[3,10,62],[28,32],0xf4f5f6,.72],
    [[15,-4,40],[9,45],0x606971,.24],
    [[-3,0,-45],[30,36],0xe5e9ed,.48],
  ];
  const trial=light==='atelier2';
  const cards=[
    [[0,48,38],[30,15],0xfff9f2,.8],
    [trial?[-38,24,45]:[-32,28,48],trial?[10,45]:[20,45],0xfff7ed,4.5],
    [[32,2,25],[3.5,48],0xf1f5ff,6.0],
    [[-24,10,-35],[5,30],0xe5edff,2.5],
    [[5,45,10],[35,22],0xffffff,1.6],
    [[12,0,40],[10,48],0x080909,.03],
    [[-3,0,-45],[35,40],0xe5e9ed,.35],
  ];
  // Restrained near-camera neutral reflection for dark metallic hands, not
  // an emissive hand material or a global exposure/fill-light increase.
  if(trial)cards.push([[-6,6,58],[12,20],0xf4f5f6,.65]);
  // Alternative product-light study: replace the front black flag with a
  // low-radiance broad neutral softbox, leaving bright edge cards unchanged.
  if(light==='atelier3'||light==='softbox')cards[5]=[[0,8,65],[30,22],0xf4f5f6,.65];
  return cards;
}

export function studioEnvironmentBackground({neutral=false,atelier=false,light='atelier'}={}){
  return atelier?(light==='studio4'?0x353a3d:light==='softbox'?0x555c61:light==='atelier3'?0x353a3d:0x272a2d):neutral?0x636363:0x353b43;
}

export function createStudioEnvironment(renderer,{neutral=false,atelier=false,light='atelier'}={}){
  const studio=new THREE.Scene();studio.background=new THREE.Color(studioEnvironmentBackground({neutral,atelier,light}));
  const geometry=new THREE.PlaneGeometry(1,1),cards=[];
  const card=(position,size,color,power)=>{
    const material=new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide});material.color.multiplyScalar(power);
    const mesh=new THREE.Mesh(geometry,material);mesh.position.set(...position);mesh.scale.set(...size,1);mesh.lookAt(0,0,0);studio.add(mesh);cards.push(material);
  };
  if(atelier){
    for(const specification of atelierReflectionCards(light))card(...specification);
  }else if(neutral){
    card([-25,32,35],[22,58],0xffffff,2.4);
    card([30,9,26],[7,52],0xffffff,2.0);
    card([0,50,-5],[48,38],0xffffff,1.5);
    card([-3,4,-45],[44,38],0xffffff,.8);
  }else{
    card([-25,32,35],[22,58],0xeaf1ff,3.6);
    card([30,9,26],[7,52],0xffffff,3.0);
    card([22,10,48],[38,50],0xe9edf2,.8);
    card([-30,-9,-24],[12,36],0xe4c79e,1.8);
    card([0,50,-5],[48,38],0xffffff,2.0);
    card([-3,4,-45],[44,38],0xe9edf6,.8);
    card([30,-8,16],[10,50],0x17202a,.25);
  }
  const generator=new THREE.PMREMGenerator(renderer),target=generator.fromScene(studio,.025,.1,150);
  geometry.dispose();cards.forEach(material=>material.dispose());generator.dispose();return target;
}

export function createAssemblyMaterials(renderer,{atelier=false,light='atelier',finish='baseline',clearTransmission=false}={}){
  const target=renderer?createStudioEnvironment(renderer,{atelier,light}):null,materials=new Map();let disposed=false;
  function unitAxis(axis,fallback){
    const length=Array.isArray(axis)&&axis.length===3&&axis.every(Number.isFinite)?Math.hypot(...axis):0;
    return Number.isFinite(length)&&length>.001?axis.map(value=>value/length):fallback;
  }
  function get(kind,zone,axis,capAxis,opticalThickness,source=false){
    const base=finishes[kind]||finishes.steel;
    const specification={...base,...(atelier?(ATELIER_FINISH_OVERRIDES[kind]||{}):{})};
    if(atelier&&finish==='studio4')Object.assign(specification,(source?STUDIO4_MOVEMENT_FINISHES:STUDIO4_EXTERIOR_FINISHES)[kind]||{});
    // Premium SVG04 keeps the exterior HOUR/MINUTE/SECONDS meshes. Their
    // classified blued material, not the disabled quality-hand overlay, is
    // the correct optional readability-trial target. Keep the lobe unchanged.
    if((finish==='atelier2'||finish==='atelier3'||finish==='studio4')&&kind==='blued')specification.color=0x346fa6;
    const texture=['linear','circular','cross'].includes(zone)?zone:specification.texture;
    const microfinish=atelier&&finish==='studio4'&&Object.hasOwn(STUDIO4_METAL_MICROFINISH,kind);
    const safeAxis=unitAxis(axis,microfinish&&kind==='case'?[0,0,1]:[1,0,0]),faceAxis=unitAxis(capAxis,[0,1,0]);
    const thickness=kind==='crystal'?(opticalThickness??specification.thickness):specification.thickness;
    const cacheKey=`${atelier&&finish==='studio4'&&source?'movement':'standard'}/${kind}/${texture}/${safeAxis.join(',')}/${faceAxis.join(',')}/${thickness??'surface'}`;
    if(materials.has(cacheKey))return materials.get(cacheKey);
    const {texture:unused,strength,...parameters}=specification;
    const material=new THREE.MeshPhysicalMaterial({...parameters,...(kind==='crystal'?{thickness}:{}),envMapIntensity:1.05});
    material.name=`OM10 / ${kind}`;material.userData.finish=kind;
    material.userData.grainAxis=[...safeAxis];material.userData.finishFaceAxis=[...faceAxis];material.userData.finishZone=texture||'plain';
    if(microfinish)addStudioMetalSurface(material,safeAxis,kind,faceAxis);
    else if(texture)addSurface(material,texture,strength,safeAxis,kind,faceAxis);
    if(kind==='crystal')addRefractionEdgeFallback(material,{clearTransmission:atelier&&clearTransmission});
    materials.set(cacheKey,material);return material;
  }
  return {
    environment:target?.texture||null,
    // finishKinds optionally assigns authored zones in a multi-material mesh.
    apply(mesh){
      const data=mesh.userData||{},kind=classifyAssemblyMaterial(mesh);
      const materialFor=index=>get(Object.hasOwn(finishes,data.finishKinds?.[index])?data.finishKinds[index]:kind,data.finishZone,data.grainAxis,data.finishFaceAxis,ASSEMBLY_CRYSTAL_THICKNESS_MM[data.assemblyId],data.sourceIndex!==undefined);
      return Array.isArray(mesh.material)?mesh.material.map((_,index)=>materialFor(index)):materialFor(0);
    },
    clone:cloneAssemblyMaterial,
    dispose(){if(disposed)return;disposed=true;materials.forEach(material=>material.dispose());target?.dispose();},
  };
}

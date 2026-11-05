import * as THREE from './vendor/three.module.js';
import {cloneAssemblyMaterial} from './assembly-materials.js';
export const CARRIER_FINISH = Object.freeze({revision:'carrier-circular-physical-r01',heightMm:.00035,maxSlope:.012,correlationMm:[.03,.07],anisotropy:.18,frame:'analytic radial slope; circumferential tool travel',axis:'source local Y',membership:'DIAL-CARRIER / Dial carrier · stepped support seat / CASE'});
export function effectiveVisible(mesh){for(let p=mesh;p;p=p.parent)if(p.visible===false)return false;return true;}
function visibilityChain(mesh){const out=[];for(let p=mesh;p;p=p.parent)out.push({name:p.name||'',visible:p.visible!==false});return out;}
export function isCarrierRing(mesh){return ['Dial carrier · stepped support seat',THREE.PropertyBinding.sanitizeNodeName('Dial carrier · stepped support seat')].includes(mesh?.name)&&mesh.userData?.assemblyId==='DIAL-CARRIER'&&mesh.userData?.support==='CASE';}
export function bindCarrierFinish(material){
 const prior=material.onBeforeCompile, priorKey=material.customProgramCacheKey();
 const anchor=/#ifdef USE_TANGENT\n[\s\S]*?\n\t#endif/;
 if(!anchor.test(THREE.ShaderChunk.normal_fragment_begin))throw Error('Carrier tangent frame anchor changed');
 material.anisotropy=CARRIER_FINISH.anisotropy;material.anisotropyRotation=0;
 material.userData.carrierMicrofinish={...CARRIER_FINISH};
 material.onBeforeCompile=shader=>{
  material.userData.carrierCompileCount=(material.userData.carrierCompileCount||0)+1;
  prior.call(material,shader);
  shader.vertexShader=shader.vertexShader.replace('#include <common>',`#include <common>
varying vec3 vCarrierPosition;varying vec3 vCarrierViewX;varying vec3 vCarrierViewZ;`).replace('#include <begin_vertex>',`#include <begin_vertex>
vCarrierPosition=position;vCarrierViewX=mat3(modelViewMatrix)*vec3(1.,0.,0.);vCarrierViewZ=mat3(modelViewMatrix)*vec3(0.,0.,1.);`);
  shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
varying vec3 vCarrierPosition;varying vec3 vCarrierViewX;varying vec3 vCarrierViewZ;
mat3 carrierFrame(vec3 n){
 vec2 radial=normalize(vCarrierPosition.xz);
 vec3 t=vCarrierViewX*radial.x+vCarrierViewZ*radial.y;
 t-=n*dot(t,n);
 // On cylindrical walls radial projection degenerates; use circumferential fallback.
 if(dot(t,t)<1.e-6)t=-vCarrierViewX*radial.y+vCarrierViewZ*radial.x;
 t=normalize(t);return mat3(t,normalize(cross(n,t)),n);
}
float carrierHash(float p){p=fract(p*.1031);p*=p+33.33;p*=p+p;return fract(p)*2.-1.;}
float carrierNoise(float p){float i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(carrierHash(i),carrierHash(i+1.),f)*(1.-smoothstep(.18,.65,fwidth(p)));}
float carrierHeight(){float r=length(vCarrierPosition.xz);return .00035*(.78*carrierNoise(r/.03+17.31)+.22*carrierNoise(r/.07-9.73));}
`);
  shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_begin>',THREE.ShaderChunk.normal_fragment_begin.replace(anchor,'mat3 tbn = carrierFrame( normal );'));
  shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
vec3 cq0=dFdx(-vViewPosition),cq1=dFdy(-vViewPosition);
vec3 cr0=cross(cq1,normal),cr1=cross(normal,cq0);
float cd=dot(cq0,cr0),ch=carrierHeight();
vec3 cs=sign(cd)*(dFdx(ch)*cr0+dFdy(ch)*cr1)/max(abs(cd),1.e-10);
cs*=min(1.,.012/max(length(cs),1.e-8));normal=normalize(normal-cs);
#ifdef USE_ANISOTROPY
 tbn=carrierFrame(normal);
#endif
`);
 };
 material.customProgramCacheKey=()=>priorKey+'|'+CARRIER_FINISH.revision;
 material.needsUpdate=true;return material;
}
export function carrierFinishRequested({premiumRequested=false,comparison='restored',mode=null}={}){return premiumRequested&&comparison==='restored'&&(mode===null||mode==='circular');}
export function createCarrierFinish({supported=true,implementation='native-glsl'}={}){
 let enabled=false,requested=false,disposed=false;const owned=new Map(),members=new Map(),baselines=new Map();
 return {
 setEnabled(value){if(disposed)throw Error('Carrier study disposed');requested=value===true;enabled=requested&&supported;},
 apply(mesh,base,{active=true}={}){
  if(disposed||!isCarrierRing(mesh))return base;
  baselines.set(mesh,base);
  members.set(mesh,{name:mesh.name,assemblyId:mesh.userData.assemblyId,support:mesh.userData.support,positionCount:mesh.geometry.attributes.position.count,indexCount:mesh.geometry.index?.count??0});
  if(!enabled||!active||!effectiveVisible(mesh))return base;
  if(Array.isArray(base)||!base?.isMeshPhysicalMaterial)throw Error('Carrier study requires one physical material');
  if(!owned.has(base))owned.set(base,bindCarrierFinish(cloneAssemblyMaterial(base)));
  return owned.get(base);
 },
 get snapshot(){return {...CARRIER_FINISH,supported,requested,reason:requested&&!supported?'Carrier circular physical finish has no installed node adapter; optional node backend retains baseline satin':null,enabled,disposed,ownedMaterials:owned.size,members:[...members].map(([mesh,record])=>{const baseline=baselines.get(mesh),candidate=owned.get(baseline),visible=effectiveVisible(mesh);return {...record,hierarchyVisible:visible,hierarchy:visibilityChain(mesh),baselineMaterialUUID:baseline?.uuid,assignedMaterialUUID:mesh.material?.uuid,candidateMaterialUUID:candidate?.uuid??null,effectiveCandidate:!!candidate&&mesh.material===candidate&&visible,compileCount:candidate?.userData.carrierCompileCount??0,nodeFinish:candidate?.userData.carrierNodeFinish??null,scalarRoughness:mesh.material?.roughness,albedo:mesh.material?.color?.toArray(),anisotropy:mesh.material?.anisotropy??0};}),implementation:supported?implementation:'baseline-unsupported',backendScope:implementation==='native-glsl'?'Native GLSL; accepted fixed views':'Installed TSL graph; actual node render parity pending; no hardware WebGPU claim'};},
 dispose(){if(disposed)return;disposed=true;enabled=false;for(const [mesh,base] of baselines)if([...owned.values()].includes(mesh.material))mesh.material=base;baselines.clear();for(const material of owned.values())material.dispose();owned.clear();members.clear();}
 };
}

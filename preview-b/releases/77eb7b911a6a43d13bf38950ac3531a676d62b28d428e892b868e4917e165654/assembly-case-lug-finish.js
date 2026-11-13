import {BufferAttribute,ShaderChunk} from './vendor/three.module.js';
import {LUG_FINISH_MEMBERSHIP as membership} from './assembly-case-lug-data.js';
export const LUG_FINISH_REVISION='lug-longitudinal-physical-r01';
export function lugFinishBackendPolicy({enabled=true,plain=false,nativeRenderer=true,nodeLugFinishSupported=false}={}){
 const supported=!!nativeRenderer||!!nodeLugFinishSupported;
 return {requested:!!enabled,supported,enabled:!!enabled&&!plain&&supported,implementation:nativeRenderer?'native-glsl':nodeLugFinishSupported?'node-tsl-r01':'baseline-unsupported',renderedParity:nativeRenderer?'accepted fixed native views':'pending matched node/native captures; no hardware WebGPU claim',reason:!supported?'Optional node renderer has no installed TSL lug finish adapter; baseline smooth steel is retained explicitly.':plain?'Plain CASE diagnostic comparison':!enabled?'Explicit lugFinish=off diagnostic comparison':null};
}
/** Two continuous physical projections in local mm. No mesh UV/tangent writes:
 * front/back use (x,-z), sidewalls (y,-z). Both travel along local -Z.
 * Squared normal weights blend charts without a periodic wrap or vertex seam.
 * These are projected, not claimed globally isometric surface coordinates.
 */
export function createLugFinish(geometry,baseMaterial,{enabled=false}={}){
 const frameBranch=/#ifdef USE_TANGENT\n[\s\S]*?\n\t#endif/;
 if(!frameBranch.test(ShaderChunk.normal_fragment_begin))throw Error('r187 lug tangent anchor changed');
 const original=geometry.index,groups=geometry.groups.map(g=>({...g}));
 if(!original||groups[0]?.start!==0||groups[0]?.count!==364722||groups[0]?.materialIndex!==0)throw Error('Lug finish requires verified R5 groups');
 const selected=new Uint8Array(364722/3);
 for(const[start,count]of membership.ranges){if(start%3||count%3||start<0||start+count>364722)throw Error('Invalid lug membership');selected.fill(1,start/3,(start+count)/3);}
 const index=original.array.slice();let cursor=0;
 for(const wanted of [0,1])for(let i=0;i<selected.length;i++)if(selected[i]===wanted){index[cursor++]=original.array[i*3];index[cursor++]=original.array[i*3+1];index[cursor++]=original.array[i*3+2];}
 if(cursor!==364722||selected.reduce((a,b)=>a+b,0)!==membership.triangles)throw Error('Lug coverage mismatch');
 geometry.setIndex(new BufferAttribute(index,1));geometry.clearGroups();
 const unchanged=364722-membership.triangles*3;geometry.addGroup(0,unchanged,0);geometry.addGroup(unchanged,membership.triangles*3,5);for(const g of groups.slice(1))geometry.addGroup(g.start,g.count,g.materialIndex);
 const baseline=baseMaterial.clone(),candidate=baseMaterial.clone();candidate.name='Longitudinal satin lugs · CAD34/35/43/47';candidate.anisotropy=.18;candidate.anisotropyRotation=0;
 candidate.userData.lugFinish={revision:LUG_FINISH_REVISION,physicalHeightPeakToPeakMM:.0006,spacingMM:[.047,.083,.137],travelLocal:[0,0,-1],projections:'front x/-z, side y/-z; millimetres',tangent:'analytic across-grain slope direction',existingAttributesUnchanged:true};
 candidate.onBeforeCompile=shader=>{
  shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vLugPosition;\nvarying vec3 vLugNormal;\nvarying vec3 vLugTravel;\nvarying vec3 vLugFallback;').replace('#include <begin_vertex>','#include <begin_vertex>\nvLugPosition=position;vLugNormal=normal;vLugTravel=mat3(modelViewMatrix)*vec3(0,0,-1);vLugFallback=mat3(modelViewMatrix)*vec3(1,0,0);');
  shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
varying vec3 vLugPosition;varying vec3 vLugNormal;varying vec3 vLugTravel;varying vec3 vLugFallback;
float lugHash(float x){x=fract(x*.1031);x*=x+33.33;x*=x+x;return fract(x)*2.-1.;}
float lugNoise(float x){float c=floor(x),f=fract(x);f=f*f*(3.-2.*f);return mix(lugHash(c),lugHash(c+1.),f)*(1.-smoothstep(.18,.65,fwidth(x)));}
float lugProfile(float q){return .65*lugNoise(q/.047+17.31)+.25*lugNoise(q/.083-9.73)+.10*lugNoise(q/.137+3.17);}
float lugField(){vec2 w=vLugNormal.xy*vLugNormal.xy;w/=max(w.x+w.y,1.e-8);return w.y*lugProfile(vLugPosition.x)+w.x*lugProfile(vLugPosition.y);}
mat3 lugFrame(vec3 n){vec3 along=vLugTravel-n*dot(vLugTravel,n);if(dot(along,along)<.01)along=vLugFallback-n*dot(vLugFallback,n);along=normalize(along);vec3 across=normalize(cross(along,n));return mat3(across,normalize(cross(n,across)),n);}
`);
  shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nfloat lugMicroField=lugField();roughnessFactor=clamp(roughnessFactor+lugMicroField*.008,.065,1.);');
  shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_begin>',ShaderChunk.normal_fragment_begin.replace(frameBranch,'mat3 tbn = lugFrame( normal );'));
  shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
vec3 lugQ0=dFdx(-vViewPosition),lugQ1=dFdy(-vViewPosition);vec3 lugR0=cross(lugQ1,normal),lugR1=cross(normal,lugQ0);float lugDet=dot(lugQ0,lugR0);float lugHeight=lugMicroField*.0003;
vec3 lugSlope=sign(lugDet)*(dFdx(lugHeight)*lugR0+dFdy(lugHeight)*lugR1)/max(abs(lugDet),1.e-10);lugSlope*=min(1.,.025/max(length(lugSlope),1.e-8));normal=normalize(normal-lugSlope);
#ifdef USE_ANISOTROPY
 tbn=lugFrame(normal);
#endif`);
 };
 candidate.customProgramCacheKey=()=>LUG_FINISH_REVISION;
 let active=!!enabled,disposed=false;
 return {baseline,candidate,get material(){return active?candidate:baseline;},setEnabled(value){if(disposed)throw Error('Lug finish is disposed');active=!!value;},get audit(){return {revision:LUG_FINISH_REVISION,enabled:active,cadFaces:membership.cadFaces,triangles:membership.triangles,sourceCaseSHA256:membership.caseGLBSHA256,sharedVerticesWithProtected:membership.sharedVerticesWithProtected,...candidate.userData.lugFinish,scalarRoughness:candidate.roughness,color:candidate.color.toArray(),anisotropy:active?.18:0,drawGroups:geometry.groups.length,geometryChanges:'group0 index-order permutation only; all attributes and ordered triangle corners preserved'};},dispose(){if(disposed)return;disposed=true;active=false;baseline.dispose();candidate.dispose();}};
}

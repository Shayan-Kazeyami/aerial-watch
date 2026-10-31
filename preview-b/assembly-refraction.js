import {ShaderChunk} from './vendor/three.module.js';

// Screen-space transmission has no colour outside its rendered viewport.
// Clamp-to-edge repeats its last texel into long streaks at macro/grazing
// cameras. Fade unavailable samples to the original visible background UV.
// This bounded offscreen approximation keeps the interior optical ray,
// thickness and Fresnel response; it is not scene ray tracing. Environment
// fallback was rejected because bright cards created an artificial edge stripe.
export const ASSEMBLY_REFRACTION_COVERAGE_GLSL=`
float assemblyRefractionCoverage(vec2 uv,vec2 size,float clipW,vec2 entryUV){
  if(clipW<=.00001)return 0.;
  vec2 edge=min(uv,vec2(1.)-uv)*size;
  float feather=clamp(length((uv-entryUV)*size),4.,64.);
  return smoothstep(1.,feather,min(edge.x,edge.y));
}`;

export function refractionCoverage(uv,size,clipW=1,entryUV=uv){
  if(!uv.every(Number.isFinite)||!size.every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(clipW)||clipW<=.00001)return 0;
  const edge=Math.min(uv[0]*size[0],(1-uv[0])*size[0],uv[1]*size[1],(1-uv[1])*size[1]);
  const feather=Math.max(4,Math.min(64,Math.hypot((uv[0]-entryUV[0])*size[0],(uv[1]-entryUV[1])*size[1])));
  const t=Math.max(0,Math.min(1,(edge-1)/(feather-1)));return t*t*(3-2*t);
}

const sampleFunction=`
${ASSEMBLY_REFRACTION_COVERAGE_GLSL}
vec4 getAssemblyTransmissionSample(vec2 uv,float roughness,float ior,vec2 entryUV,float clipW){
  float coverage=assemblyRefractionCoverage(uv,transmissionSamplerSize,clipW,entryUV);
  // Never request an out-of-viewport sample, even when its blend weight is 0.
  vec2 safeUV=clamp(uv,vec2(1.)/transmissionSamplerSize,vec2(1.)-vec2(1.)/transmissionSamplerSize);
  vec2 safeEntryUV=clamp(entryUV,vec2(1.)/transmissionSamplerSize,vec2(1.)-vec2(1.)/transmissionSamplerSize);
  vec4 transmitted=getTransmissionSample(safeUV,roughness,ior);
  if(coverage<1.)transmitted=mix(getTransmissionSample(safeEntryUV,roughness,ior),transmitted,coverage);
  return transmitted;
}
`;

export function addRefractionEdgeFallback(material){
  material.onBeforeCompile=shader=>{
    let chunk=ShaderChunk.transmission_pars_fragment;
    chunk=chunk.replace('\tvec3 volumeAttenuation(',sampleFunction+'\n\tvec3 volumeAttenuation(')
      .replace('\t\tvec4 transmittedLight;','\t\tvec4 assemblyEntryClip=projMatrix*viewMatrix*vec4(position,1.);\n\t\tvec2 assemblyEntryUV=assemblyEntryClip.xy/assemblyEntryClip.w*.5+.5;\n\t\tvec4 transmittedLight;')
      .replace('getTransmissionSample( refractionCoords, roughness, iors[ i ] )','getAssemblyTransmissionSample( refractionCoords, roughness, iors[ i ], assemblyEntryUV, ndcPos.w )')
      .replace('getTransmissionSample( refractionCoords, roughness, ior )','getAssemblyTransmissionSample( refractionCoords, roughness, ior, assemblyEntryUV, ndcPos.w )');
    shader.fragmentShader=shader.fragmentShader.replace('#include <transmission_pars_fragment>',chunk);
  };
  material.customProgramCacheKey=()=> 'om10-sapphire-edge-fallback-v2';
}

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

export function addRefractionEdgeFallback(material,{clearTransmission=false}={}){
  material.onBeforeCompile=shader=>{
    let chunk=ShaderChunk.transmission_pars_fragment;
    const required=['\tvec3 volumeAttenuation(','\t\tvec4 transmittedLight;','getTransmissionSample( refractionCoords, roughness, iors[ i ] )','getTransmissionSample( refractionCoords, roughness, ior )'];
    if(required.some(token=>!chunk.includes(token)))throw new Error('Unsupported transmission shader layout; review the refraction patch before upgrading Three.js.');
    let sampling=sampleFunction;
    if(clearTransmission){
      // Opt-in polished-crystal trial: remove only the reflection BRDF's
      // minimum roughness from background filtering, not from Fresnel or
      // reflection. Keep derivative roughness and the stock bicubic filter.
      // This uniform is captured at compile time; this trial targets the
      // authored, untextured crystal rather than animated roughness/maps.
      const floor='material.roughness = max( roughnessFactor, 0.0525 );';
      if(!ShaderChunk.lights_physical_fragment.includes(floor))throw new Error('Unsupported physical roughness floor; review the clear transmission trial before upgrading Three.js.');
      shader.uniforms.assemblyAuthoredRoughness={value:material.roughness};
      sampling='uniform float assemblyAuthoredRoughness;\n'+sampling.replace(
        '  float coverage=assemblyRefractionCoverage',
        '  roughness=clamp(assemblyAuthoredRoughness+max(0.,roughness-max(assemblyAuthoredRoughness,.0525)),0.,1.);\n  float coverage=assemblyRefractionCoverage');
    }
    chunk=chunk.replace('\tvec3 volumeAttenuation(',sampling+'\n\tvec3 volumeAttenuation(')
      .replace('\t\tvec4 transmittedLight;','\t\tvec4 assemblyEntryClip=projMatrix*viewMatrix*vec4(position,1.);\n\t\tvec2 assemblyEntryUV=assemblyEntryClip.xy/assemblyEntryClip.w*.5+.5;\n\t\tvec4 transmittedLight;')
      .replace('getTransmissionSample( refractionCoords, roughness, iors[ i ] )','getAssemblyTransmissionSample( refractionCoords, roughness, iors[ i ], assemblyEntryUV, ndcPos.w )')
      .replace('getTransmissionSample( refractionCoords, roughness, ior )','getAssemblyTransmissionSample( refractionCoords, roughness, ior, assemblyEntryUV, ndcPos.w )');
    shader.fragmentShader=shader.fragmentShader.replace('#include <transmission_pars_fragment>',chunk);
  };
  material.customProgramCacheKey=()=> clearTransmission?'om10-sapphire-edge-fallback-v2-clear-transmission-v1':'om10-sapphire-edge-fallback-v2';
}

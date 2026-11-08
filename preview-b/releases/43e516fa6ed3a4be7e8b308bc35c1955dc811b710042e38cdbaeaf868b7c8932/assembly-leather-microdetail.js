import * as THREE from './vendor/three.module.js';
// Texture references stay out of JSON-serialized Material.userData. The owner
// remains createPhotoLeatherDetails; node/selection copies borrow, never own.
const bindings=new WeakMap();
export const getLeatherMicrodetailBinding=material=>bindings.get(material)||null;
export function copyLeatherMicrodetailBinding(source,clone){
 const binding=bindings.get(source);if(binding)bindings.set(clone,binding);
 return clone;
}

// Macro keeps the authored R14 scale/strength. Fine calf uses a separate map at
// eight times that frequency; no color overlay, displacement, or sharpened mip.
export const LEATHER_MICRODETAIL=Object.freeze({revision:'leather-dual-scale-r2-sign',repeat:8,normalStrength:.65,roughnessStrength:.4,roughnessMean:.7816598508872238,fadeStartTexels:8,fadeEndTexels:64});
export function installLeatherMicrodetail(material,{normalMap,roughnessMap,settings=LEATHER_MICRODETAIL}={}){
 if(!material?.normalMap||material.normalMapType!==THREE.TangentSpaceNormalMap||!normalMap?.isTexture||!roughnessMap?.isTexture)return null;
 // These maps are the lifecycle owner's existing private lining clones. Never
 // clone again, dispose here, or change repeat: the lining still uses its UVs.
 for(const texture of [normalMap,roughnessMap]){
  texture.colorSpace=THREE.NoColorSpace;texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
  texture.minFilter=THREE.LinearMipmapLinearFilter;texture.magFilter=THREE.LinearFilter;
  if(!texture.isCompressedTexture)texture.generateMipmaps=true;
  texture.needsUpdate=true;
 }
 bindings.set(material,Object.freeze({normalMap,roughnessMap,settings:Object.freeze({...settings})}));
 const previous=material.onBeforeCompile,oldKey=material.customProgramCacheKey();
 const uniforms={leatherMicroNormal:{value:normalMap},leatherMicroRoughness:{value:roughnessMap},leatherMicroRepeat:{value:settings.repeat},leatherMicroNormalStrength:{value:settings.normalStrength},leatherMicroRoughnessStrength:{value:settings.roughnessStrength},leatherMicroRoughnessMean:{value:settings.roughnessMean},leatherMicroSize:{value:new THREE.Vector2(normalMap.image?.width||2048,normalMap.image?.height||2048)},leatherMicroFade:{value:new THREE.Vector2(settings.fadeStartTexels,settings.fadeEndTexels)}};
 const declarations=`
uniform sampler2D leatherMicroNormal;
uniform sampler2D leatherMicroRoughness;
uniform float leatherMicroRepeat, leatherMicroNormalStrength, leatherMicroRoughnessStrength, leatherMicroRoughnessMean;
uniform vec2 leatherMicroSize, leatherMicroFade;
#ifdef USE_NORMALMAP_TANGENTSPACE
float leatherMicroWeight(vec2 detailUv) {
 vec2 dx=dFdx(detailUv)*leatherMicroSize, dy=dFdy(detailUv)*leatherMicroSize;
 float footprint=max(length(dx),length(dy));
 return 1.0-smoothstep(leatherMicroFade.x,leatherMicroFade.y,footprint);
}
// Reoriented normal mapping: detail is composed in the macro normal frame,
// not linearly mixed with world/view normals. Flat detail preserves macro.
vec3 leatherRNM(vec3 baseN, vec3 detailN) {
 vec3 t=normalize(baseN)+vec3(0.0,0.0,1.0);
 vec3 u=normalize(detailN)*vec3(-1.0,-1.0,1.0);
 return normalize(t*dot(t,u)/max(t.z,0.0001)-u);
}
#endif
`;
 const normalChunk=THREE.ShaderChunk.normal_fragment_maps.replace('mapN.xy *= normalScale;',`mapN.xy *= normalScale;
 vec2 leatherDetailUv=vNormalMapUv*leatherMicroRepeat;
 vec3 leatherDetailN=texture2D(leatherMicroNormal,leatherDetailUv).xyz*2.0-1.0;
 // GLTF derivative-tangent handedness belongs to BOTH tangent maps. Keep
 // only the sign: macro strength must not attenuate the independent fine map.
 vec2 leatherMicroHandedness=vec2(normalScale.x<0.0?-1.0:1.0,normalScale.y<0.0?-1.0:1.0);
 leatherDetailN.xy*=leatherMicroHandedness*leatherMicroNormalStrength*leatherMicroWeight(leatherDetailUv);
 mapN=leatherRNM(mapN,leatherDetailN);`);
 const roughChunk=THREE.ShaderChunk.roughnessmap_fragment+`
#ifdef USE_NORMALMAP_TANGENTSPACE
 vec2 leatherRoughUv=vNormalMapUv*leatherMicroRepeat;
 float leatherFineRoughness=texture2D(leatherMicroRoughness,leatherRoughUv).g;
 roughnessFactor=clamp(roughnessFactor+(leatherFineRoughness-leatherMicroRoughnessMean)*leatherMicroRoughnessStrength*leatherMicroWeight(leatherRoughUv),0.04,1.0);
#endif
`;
 material.onBeforeCompile=function(shader,renderer){
  previous.call(this,shader,renderer);
  if(!shader.fragmentShader.includes('#include <normal_fragment_maps>')||!shader.fragmentShader.includes('#include <roughnessmap_fragment>'))throw Error('Leather microdetail: unsupported normal/roughness shader layout');
  Object.assign(shader.uniforms,uniforms);
  shader.fragmentShader=declarations+shader.fragmentShader.replace('#include <normal_fragment_maps>',normalChunk).replace('#include <roughnessmap_fragment>',roughChunk);
 };
 material.customProgramCacheKey=()=>oldKey+'/'+settings.revision+'/'+JSON.stringify(settings);
 material.userData={...material.userData,leatherMicrodetail:{...settings,normalTexture:normalMap.name,roughnessTexture:roughnessMap.name,extraTextureAllocations:0}};
 material.needsUpdate=true;
 return Object.freeze({...settings,extraTextureAllocations:0});
}

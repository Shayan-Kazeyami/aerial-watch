import {Box3} from './vendor/three.module.js';
import {cloneAssemblyMaterial} from './assembly-materials.js';

export const CROWN_CAP_FINISH=Object.freeze({roughness:.32,positionTolerance:1e-5,normalThreshold:.999999});

// Inputs are local-space X and normalized normal X components. A geometric
// face gate is required: cap-edge vertices are shared by adjacent bevel faces.
export function crownCapMask({x,normalX,faceNormalX,maxX}){
  return [x,normalX,faceNormalX,maxX].every(Number.isFinite)&&
    Math.abs(x-maxX)<=CROWN_CAP_FINISH.positionTolerance&&
    normalX>=CROWN_CAP_FINISH.normalThreshold&&
    Math.abs(faceNormalX)>=CROWN_CAP_FINISH.normalThreshold;
}

/** Private material proposal, not a normal repair. Never assigns mesh.material.
 * Caller owns assignment/restoration and must detach the clone before dispose.
 * dispose() releases only the clone, never shared textures or source material.
 */
export function createCrownCapFinish(mesh,baseMaterial){
  if(mesh?.userData?.assemblyId!=='CROWN'||!mesh.geometry?.attributes.position||!mesh.geometry.attributes.normal)
    throw new TypeError('Crown cap finish requires the actual CROWN geometry with normals.');
  if(Array.isArray(baseMaterial)||!baseMaterial?.isMeshPhysicalMaterial)
    throw new TypeError('Crown cap finish requires one MeshPhysicalMaterial, not an array.');
  const bounds=new Box3().setFromBufferAttribute(mesh.geometry.attributes.position),maxX=bounds.max.x;
  if(!Number.isFinite(maxX)||bounds.isEmpty())throw new TypeError('Crown cap finish requires finite nonempty geometry.');
  const material=cloneAssemblyMaterial(baseMaterial),compile=material.onBeforeCompile,key=material.customProgramCacheKey;
  material.name=`${baseMaterial.name} / optional satin crown cap`;
  material.onBeforeCompile=function(shader,renderer){
    compile.call(this,shader,renderer);
    for(const [source,token]of [[shader.vertexShader,'#include <common>'],[shader.vertexShader,'#include <begin_vertex>'],[shader.fragmentShader,'#include <common>'],[shader.fragmentShader,'#include <metalnessmap_fragment>']]){
      if(!source?.includes(token))throw new Error(`Unsupported crown cap shader layout: ${token}`);
    }
    shader.uniforms.uAerialCrownCapMaxX={value:maxX};
    const varyings='\nvarying vec3 vAerialCrownCapLocalPosition;\nvarying vec3 vAerialCrownCapLocalNormal;\n';
    shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>'+varyings)
      .replace('#include <begin_vertex>','#include <begin_vertex>\nvAerialCrownCapLocalPosition=position;\nvAerialCrownCapLocalNormal=normal;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>'+varyings+'uniform float uAerialCrownCapMaxX;\n')
      .replace('#include <metalnessmap_fragment>',`
// Evaluate after the inherited roughness/grain callback, before metalness.
vec3 aerialCrownCapFace=cross(dFdx(vAerialCrownCapLocalPosition),dFdy(vAerialCrownCapLocalPosition));
float aerialCrownCapFaceLength=length(aerialCrownCapFace);
float aerialCrownCapMask=step(abs(vAerialCrownCapLocalPosition.x-uAerialCrownCapMaxX),${CROWN_CAP_FINISH.positionTolerance.toFixed(8)})
  *step(${CROWN_CAP_FINISH.normalThreshold},normalize(vAerialCrownCapLocalNormal).x)
  *step(${CROWN_CAP_FINISH.normalThreshold},abs(aerialCrownCapFace.x)/max(aerialCrownCapFaceLength,1.e-20));
roughnessFactor=mix(roughnessFactor,${CROWN_CAP_FINISH.roughness},aerialCrownCapMask);
#include <metalnessmap_fragment>`);
  };
  material.customProgramCacheKey=function(){return `${key.call(baseMaterial)}|aerial-crown-cap-v1`;};
  let disposed=false;
  return {material,audit:{maxX,roughness:CROWN_CAP_FINISH.roughness,scope:'CROWN outer +X planar cap only; shader-only material proposal'},
    dispose(){if(disposed)return;disposed=true;material.dispose();}};
}

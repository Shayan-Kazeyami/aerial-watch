import {test} from 'node:test';
import assert from 'node:assert/strict';
import {MeshPhysicalMaterial,ShaderChunk} from '../vendor/three.module.js';
import {addRefractionEdgeFallback} from '../assembly-refraction.js';

function compile(options){
  const material=new MeshPhysicalMaterial({roughness:.008,ior:1.76,thickness:.35,transmission:1});
  addRefractionEdgeFallback(material,options);
  const shader={uniforms:{},fragmentShader:'#include <transmission_pars_fragment>\n#include <transmission_fragment>'};
  material.onBeforeCompile(shader);
  return {material,shader};
}
test('clear transmission is opt-in and uses a separate shader cache key',()=>{
  const standard=compile(),disabled=compile({clearTransmission:false}),clear=compile({clearTransmission:true});
  assert.equal(standard.shader.fragmentShader,disabled.shader.fragmentShader);
  assert.equal(standard.material.customProgramCacheKey(),'om10-sapphire-edge-fallback-v2');
  assert.notEqual(clear.material.customProgramCacheKey(),standard.material.customProgramCacheKey());
  assert.deepEqual(standard.shader.uniforms,{});
  assert.equal(clear.shader.uniforms.assemblyAuthoredRoughness.value,.008);
});
test('clear trial changes only wrapper sampling roughness, preserving the optical shader',()=>{
  const standard=compile().shader.fragmentShader,clear=compile({clearTransmission:true}).shader.fragmentShader;
  const adjustment='  roughness=clamp(assemblyAuthoredRoughness+max(0.,roughness-max(assemblyAuthoredRoughness,.0525)),0.,1.);\n';
  assert(clear.includes(adjustment));
  assert.equal(clear.replace('uniform float assemblyAuthoredRoughness;\n','').replace(adjustment,''),standard);
  assert(clear.includes('EnvironmentBRDF( n, v, specularColor, specularF90, roughness )'));
  assert(clear.includes('return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );'));
  assert(clear.includes('getAssemblyTransmissionSample( refractionCoords, roughness, iors[ i ], assemblyEntryUV, ndcPos.w )'));
  assert(clear.includes('getAssemblyTransmissionSample( refractionCoords, roughness, ior, assemblyEntryUV, ndcPos.w )'));
  assert(clear.includes('#include <transmission_fragment>'));
});
test('sampling formula retains geometric roughness and bounds output',()=>{
  const source=compile({clearTransmission:true}).shader.fragmentShader;
  const expression=source.match(/  roughness=(clamp\(assemblyAuthoredRoughness[^;]+);/)[1];
  const sample=new Function('assemblyAuthoredRoughness','roughness','max','clamp',`return ${expression}`);
  const evaluate=(authored,physical)=>sample(authored,physical,Math.max,(v,a,b)=>Math.min(b,Math.max(a,v)));
  assert.equal(evaluate(.008,.0525),.008);
  assert(Math.abs(evaluate(.008,.1525)-.108)<1e-12);
  assert.equal(evaluate(.2,.3),.3);
  assert.equal(evaluate(.008,.008),.008);
  assert.equal(evaluate(1,1),1);
  assert.equal(evaluate(2,2),1);
  assert.equal(evaluate(-1,0),0);
});
test('clear trial rejects an unknown physical floor without affecting standard mode',()=>{
  const saved=ShaderChunk.lights_physical_fragment;
  try{
    ShaderChunk.lights_physical_fragment=saved.replace('0.0525','0.06');
    assert.throws(()=>compile({clearTransmission:true}),/Unsupported physical roughness floor/);
    assert.doesNotThrow(()=>compile());
  }finally{ShaderChunk.lights_physical_fragment=saved;}
});

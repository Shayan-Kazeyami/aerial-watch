import {SSAOPass} from './vendor/postprocessing/SSAOPass.js';
import {GTAOPass} from './vendor/postprocessing/GTAOPass.js';

function noiseIdentity(texture){
  const data=texture?.image?.data;let hash=2166136261;
  if(data){const bytes=new Uint8Array(data.buffer,data.byteOffset,data.byteLength);for(const byte of bytes)hash=Math.imul(hash^byte,16777619);}
  return {uuid:texture?.uuid??null,width:texture?.image?.width??null,height:texture?.image?.height??null,fnv1a32:data?(hash>>>0).toString(16).padStart(8,'0'):null};
}

// Construct only the requested native pipeline: no inactive A/B render targets.
export function createNativeAO({scene,camera,mode='baseline',width=1,height=1}){
  if(!['baseline','gtao'].includes(mode))throw new RangeError('Unknown native AO mode.');
  const isGTAO=mode==='gtao';
  const ao=isGTAO?new GTAOPass(scene,camera,width,height,undefined,
    {radius:1.2,thickness:1,samples:24,screenSpaceRadius:false},
    {samples:16,rings:2,radiusExponent:1,radius:8,lumaPhi:10,depthPhi:2,normalPhi:3})
    :new SSAOPass(scene,camera,width,height,24);
  if(isGTAO)Object.defineProperty(ao,'kernelRadius',{configurable:true,enumerable:true,
    get(){return ao.gtaoMaterial.uniforms.radius.value;},set(value){ao.gtaoMaterial.uniforms.radius.value=value;}});
  else ao.kernelRadius=1.2;
  const nativeDispose=ao.dispose.bind(ao);let disposed=false;
  ao.dispose=()=>{if(disposed)return;disposed=true;nativeDispose();
    // Official r187 passes omit these owned resources from their disposal methods.
    if(isGTAO){ao.gtaoMaterial.dispose();ao.blendMaterial.dispose();}
    else{ao.ssaoMaterial.dispose();ao.noiseTexture.dispose();}
  };
  function snapshot(){
    const common={revision:'native-ao-r1',backend:'native-webgl2',mode,algorithm:isGTAO?'r187 GTAOPass + PoissonDenoiseShader':'r187 SSAOPass',enabled:ao.enabled,
      width:ao.width,height:ao.height,fullResolution:true,radius:ao.kernelRadius,radiusUnits:'world/view-space',disposed};
    if(!isGTAO)return {...common,samples:ao.ssaoMaterial.defines.KERNEL_SIZE,minDistance:ao.minDistance,maxDistance:ao.maxDistance,
      kernel:ao.kernel.map(v=>v.toArray()),noise:noiseIdentity(ao.noiseTexture)};
    const g=ao.gtaoMaterial,p=ao.pdMaterial;
    return {...common,samples:g.defines.SAMPLES,thickness:g.uniforms.thickness.value,screenSpaceRadius:g.defines.SCREEN_SPACE_RADIUS,
      blendIntensity:ao.blendIntensity,legacyDistanceAssignments:{minDistance:ao.minDistance??null,maxDistance:ao.maxDistance??null,usedByAlgorithm:false},
      denoise:{samples:p.defines.SAMPLES,rings:ao.pdRings,radiusExponent:ao.pdRadiusExponent,radius:p.uniforms.radius.value,lumaPhi:p.uniforms.lumaPhi.value,depthPhi:p.uniforms.depthPhi.value,normalPhi:p.uniforms.normalPhi.value},
      noise:noiseIdentity(ao.gtaoNoiseTexture),denoiseNoise:noiseIdentity(ao.pdNoiseTexture)};
  }
  return {ao,snapshot,compositeMaterial:isGTAO?ao.blendMaterial:ao.copyMaterial};
}

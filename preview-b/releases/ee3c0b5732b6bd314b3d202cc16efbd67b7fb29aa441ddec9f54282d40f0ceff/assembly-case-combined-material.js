import {assetURL} from './assembly-asset-routing.js';
import {leatherAnisotropy} from './assembly-photo-leather.js';
import {TextureLoader,NoColorSpace,RepeatWrapping,ClampToEdgeWrapping,LinearFilter,LinearMipmapLinearFilter,MeshPhysicalMaterial,Vector2,TangentSpaceNormalMap} from './vendor/three.module.js';
import {CASE_MATERIAL_DESCRIPTOR} from './assembly-case-combined-material-data.js';
const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
export async function prepareCaseCombinedMaterials(geometry,callerSignal,{mapsEnabled=true,timeoutMs=120000}={}){
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('timeoutMs must be positive');
 callerSignal?.throwIfAborted();const controller=new AbortController(),signal=controller.signal;
 const abort=()=>controller.abort(callerSignal.reason);callerSignal?.addEventListener('abort',abort,{once:true});
 const timer=setTimeout(()=>{const e=new Error('Selected CASE materials took too long to load');e.name='TimeoutError';controller.abort(e);},timeoutMs);
 try{return await prepare(geometry,signal,{mapsEnabled});}finally{clearTimeout(timer);callerSignal?.removeEventListener('abort',abort);}
}
async function prepare(geometry,signal,{mapsEnabled}){
 const base=new URL('./case-assets/',import.meta.url);
 async function fetchBytes(file,digest){const r=await fetch(new URL(assetURL('case-assets/'+file),new URL('../',base)),{signal});if(!r.ok)throw new Error(`Finish ${file} unavailable`);const b=await r.arrayBuffer();if(digest&&await sha(b)!==digest)throw new Error(`Finish ${file} hash mismatch`);return b;}
 const {proof,normalProof}=CASE_MATERIAL_DESCRIPTOR,orientationProof=CASE_MATERIAL_DESCRIPTOR.orientationProvenance;
 const textures=[],materials=[];let disposed=false;
 const dispose=()=>{if(disposed)return;disposed=true;materials.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());};
 const loadTexture=url=>new Promise((resolve,reject)=>{
  let settled=false,texture;const finish=(error,value)=>{if(settled)return;settled=true;signal?.removeEventListener('abort',abort);error?reject(error):resolve(value);};
  const abort=()=>finish(signal.reason||new DOMException('Aborted','AbortError'));
  signal?.throwIfAborted();signal?.addEventListener('abort',abort,{once:true});
  try{texture=new TextureLoader().load(url,t=>{if(settled)return;finish(null,t);},undefined,error=>finish(error));textures.push(texture);}catch(error){finish(error);}
 });
 try{
  for(const [file,digest,periodic,name,rotation] of [['planar-satin.png',proof.textureSHA256,false,'Satin planar steel',0],['revolved-satin.png',proof.revolvedTextureSHA256,true,'Machined steel body',Math.PI/2]]){
   const bytes=await fetchBytes(file,digest),url=URL.createObjectURL(new Blob([bytes],{type:'image/png'}));let texture;
   try{texture=await loadTexture(url);}finally{URL.revokeObjectURL(url);}signal?.throwIfAborted();
   texture.colorSpace=NoColorSpace;texture.wrapS=periodic?RepeatWrapping:ClampToEdgeWrapping;texture.wrapT=ClampToEdgeWrapping;texture.minFilter=LinearMipmapLinearFilter;texture.magFilter=LinearFilter;texture.generateMipmaps=true;texture.userData={dataSHA256:digest};texture.name=name+' height/roughness data';
   const normalRecord=normalProof.records[periodic?1:0];if(normalRecord.sourceHeightSHA256!==digest)throw new Error('Normal-map height identity mismatch');
   const normalBytes=await fetchBytes(normalRecord.normalPNG,normalRecord.normalSHA256),normalURL=URL.createObjectURL(new Blob([normalBytes],{type:'image/png'}));let normalTexture;
   try{normalTexture=await loadTexture(normalURL);}finally{URL.revokeObjectURL(normalURL);}signal?.throwIfAborted();normalTexture.colorSpace=NoColorSpace;normalTexture.flipY=true;normalTexture.wrapS=texture.wrapS;normalTexture.wrapT=texture.wrapT;normalTexture.minFilter=LinearMipmapLinearFilter;normalTexture.magFilter=LinearFilter;normalTexture.generateMipmaps=true;normalTexture.name=name+' physical tangent normal G32';normalTexture.userData={dataSHA256:normalRecord.normalSHA256,encodingGain:normalProof.gain,physicalHeightScaleMM:.0006};
   if(orientationProof.records[periodic?1:0].correctedRotationRadians!==rotation)throw new Error('Anisotropy orientation proof mismatch');
   const material=new MeshPhysicalMaterial({name,metalness:1,roughness:.29,bumpMap:null,bumpScale:.0006,normalMap:mapsEnabled?normalTexture:null,normalMapType:TangentSpaceNormalMap,normalScale:new Vector2(...normalRecord.normalScale),roughnessMap:mapsEnabled?texture:null,anisotropy:.18,anisotropyRotation:CASE_MATERIAL_DESCRIPTOR.rotationRadians[periodic?1:0],clearcoat:0});material.color.setRGB(.56,.57,.58);materials.push(material);
  }
  let filtering={revision:proof.revision,quality:null,capability:null,effectiveTextureAnisotropy:null,physicalMaterialAnisotropy:.18};
  return {materials,proof,normalProof,orientationProof,get comparison(){return {revision:'case-r5-slope-aligned-map-effect-r1',orientationRevision:orientationProof.revision,anisotropyRotations:{planar:0,body:Math.PI/2},normalRevision:normalProof.revision,orientation:CASE_MATERIAL_DESCRIPTOR.orientationProvenance,rotationRadians:CASE_MATERIAL_DESCRIPTOR.rotationRadians,encodingGain:normalProof.gain,normalScale:[1/normalProof.gain,1/normalProof.gain],physicalHeightScaleMM:.0006,bumpMapDisabled:true,requestedMapsEnabled:mapsEnabled,scalarRoughness:.29,bumpScale:.0006,bumpScaleUnits:'Three r180 scalar; NOT calibrated millimetres',physicalMaterialAnisotropy:.18};},get textureFiltering(){return {...filtering,textures:textures.map(t=>({name:t.name,effective:t.anisotropy}))};},setTextureQuality(quality,maxSupported){if(disposed)return;if(!Number.isFinite(maxSupported)||maxSupported<1)throw new Error('Measured renderer anisotropy capability required');const effective=leatherAnisotropy(quality,maxSupported);for(const texture of textures)if(texture.anisotropy!==effective){texture.anisotropy=effective;texture.needsUpdate=true;}filtering={...filtering,quality,capability:maxSupported,effectiveTextureAnisotropy:effective};},dispose};
 }catch(e){dispose();throw e;}
}

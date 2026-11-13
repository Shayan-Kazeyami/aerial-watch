import * as THREE from './vendor/three.module.js';

export function actualBackend(renderer){
  if(renderer.backend?.isWebGPUBackend && renderer.backend.device)return 'WebGPU';
  if(renderer.isWebGLRenderer || renderer.backend?.isWebGLBackend)return 'WebGL2';
  return 'unknown';
}
// The shipping-compatible WebGL path remains default until visual parity passes.
// WebGPU is a real, explicit study, never a name for the automatic GL fallback.
export async function createAssemblyRenderer({canvas,antialias=true,requested='webgl2',unsupportedReason=null,navigatorObject=globalThis.navigator,secure=globalThis.isSecureContext,loadGPU=()=>import('./vendor/three.webgpu.js'),makeGL=options=>new THREE.WebGLRenderer(options)}={}){
  const identity={requested,actual:null,threeRevision:THREE.REVISION,revision:'renderer-r187-integrated-c22-r1',fallbackReason:null,adapter:null,adapterMetadataScope:'Preflight adapter probe only; actual backend established after renderer.init from backend+device',limitations:[]};
  const options={canvas,antialias,alpha:false,powerPreference:'high-performance'};
  let renderer,GPU;
  if(requested==='webgpu'||requested==='webgpu-gl'){
    try{
      if(unsupportedReason)throw new Error(unsupportedReason);
      if(requested==='webgpu'&&!secure)throw new Error('WebGPU requires a secure context');
      if(requested==='webgpu'&&!navigatorObject?.gpu)throw new Error('navigator.gpu unavailable');
      const adapter=requested==='webgpu'?await navigatorObject.gpu.requestAdapter({powerPreference:'high-performance',featureLevel:'compatibility',xrCompatible:false}):{};
      if(!adapter)throw new Error('No WebGPU adapter available');
      identity.adapter=adapter.info?{vendor:adapter.info.vendor,architecture:adapter.info.architecture,device:adapter.info.device,description:adapter.info.description}:null;
      GPU=await loadGPU();renderer=new GPU.WebGPURenderer({...options,forceWebGL:requested==='webgpu-gl'});await renderer.init();
      if(requested==='webgpu'&&actualBackend(renderer)!=='WebGPU')throw new Error('Three initialized a non-WebGPU backend');
      renderer.capabilities={maxTextureSize:renderer.backend.device?.limits.maxTextureDimension2D||renderer.backend.gl?.getParameter(renderer.backend.gl.MAX_TEXTURE_SIZE)||4096,maxSamples:4,getMaxAnisotropy:()=>renderer.getMaxAnisotropy()};
      renderer.aerialPMREMGenerator=GPU.PMREMGenerator;
      const {installNodeFinishLibrary}=await import('./assembly-node-finishes.js');installNodeFinishLibrary(renderer,identity);
      identity.limitations=['Study: baseline procedural grain, R5 lug field/analytic anisotropy, DIAL-CARRIER circular physical finish and crown cap ported to TSL; clear-glass edge/sampling patch ported; Studio4 analytic microfinish still requires a port.','Node SSAO/bloom/SMAA require matched visual validation; SSAO differs from the legacy kernel.','No hardware performance or visual parity claim.'];
    }catch(error){
      identity.fallbackReason=String(error.message||error);
      // A failed GPU initialization can bind the canvas context irreversibly.
      await disposeAssemblyRenderer(renderer,identity);renderer=null;
      if(canvas?.getContext && canvas.parentNode){const fresh=canvas.cloneNode(false);canvas.replaceWith(fresh);options.canvas=fresh;}
    }
  }
  if(!renderer)renderer=makeGL(options);
  identity.actual=actualBackend(renderer);
  if(identity.actual==='unknown')throw new Error('Renderer backend identity could not be established');
  return {renderer,identity,GPU:renderer.isWebGPURenderer?GPU:null};
}
export function isGPU(renderer){return actualBackend(renderer)==='WebGPU';}

export function guardGPUMaterials(scene,diagnostics){
  const names=new Set(diagnostics.guardedMaterials||[]);
  scene.traverse(object=>{for(const material of (Array.isArray(object.material)?object.material:[object.material])){
    if(!material)continue;
    if(material.isShaderMaterial||material.isRawShaderMaterial)throw new Error(`Unsupported WebGPU shader material: ${material.name||material.type}`);
    if(material.onBeforeCompile!==THREE.Material.prototype.onBeforeCompile&&!material.userData.aerialSurface&&!material.userData.aerialCrownCap&&!material.userData.aerialRefraction&&!material.userData.leatherMicrodetail&&!(diagnostics.nodeFinishes?.carrierMicrofinish?.installed&&material.userData.carrierMicrofinish?.revision==='carrier-circular-physical-r01')&&!(diagnostics.nodeFinishes?.lugFinish?.installed&&material.userData.lugFinish?.revision==='lug-longitudinal-physical-r01')){names.add(material.name||material.type);}
  }});
  diagnostics.guardedMaterials=[...names];
}

export async function disposeAssemblyRenderer(renderer,identity){
 try{await renderer?.dispose();}catch(error){(identity.cleanupErrors??=[]).push(String(error.message||error));}
}

import {assetURL,assetBase} from './assembly-asset-routing.js';
import {supportsAvif} from './avif-detect.js';
import {loadWithLiningFallback} from './lining-fallback.js';
import {LINING_QA} from './assembly-lining-qa-selection.js';
import {AUTHORED_LEATHER_IDENTITY} from './assembly-leather-authoring-identity.js';
import {verifyLoadedLeatherGeometry} from './assembly-leather-identity.js';
import {loadGLTFAsset} from './assembly-loading.js';
import {withChunkedTexture} from './assembly-chunked-texture.js';

export const R14_LEATHER_URL='leather-assets/r14/leather.gltf';
export const R14_NORMAL_IDENTITY=Object.freeze({bytes:16562348,sha256:'bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585'});
const LOW_NORMAL_IDENTITY=Object.freeze({bytes:4389472,sha256:'5d8aa10702589424c1157d9a58a7f75aca265569d7c8fac09525a00af19455bc'});
const importLoader=()=>import('./vendor/loaders/KTX2Loader.js').then(module=>module.KTX2Loader);
// Fail closed: GLTFLoader may suppress image errors and return a null map.
export function verifyRequiredLeatherMaps(gltf){
 const required=new Map([['leather / restrained charcoal crease R14',['map','normalMap','roughnessMap']],['lining / warm fine calf R11',['map','normalMap','roughnessMap']],['thread / constant round 0.13 mm / strap-adaptive-thread-fiber-r15',['map','normalMap']]]),seen=new Set();
 if(!gltf?.scene?.traverse)throw new Error('Leather scene is unavailable');
 gltf.scene.traverse(o=>{if(!o.isMesh)return;for(const m of Array.isArray(o.material)?o.material:[o.material]){if(!m||!required.has(m.name))continue;for(const key of required.get(m.name))if(!m[key]?.isTexture)throw new Error(`Leather required map missing: ${m.name} / ${key}`);seen.add(m.name);}});
 for(const name of required.keys())if(!seen.has(name))throw new Error(`Leather required material missing: ${name}`);
 return {status:'verified',materials:seen.size};
}

// Explicit candidate, not a silent quality fallback. One dedicated manager
// confines the normal's temporary Blob URL to this single glTF parse.
export async function loadR14KtxLeather({renderer,makeManager,makeLoader,signal,timeoutMs=120000,disposeUnused=()=>{},baseURL=globalThis.location?.href,onPhase=()=>{},initialNormal='full'},
 {importKtxLoader=importLoader,loadAsset=loadGLTFAsset,withTexture=withChunkedTexture,verifyGeometry=verifyLoadedLeatherGeometry,verifyTextures=verifyRequiredLeatherMaps,requireVerifiedNormal=true,probeAvif=supportsAvif}={}){
 if(!['full','progressive-2k'].includes(initialNormal))throw new TypeError('Unknown initial normal');
 const selectedNormal=initialNormal==='full'?R14_NORMAL_IDENTITY:LOW_NORMAL_IDENTITY;
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('Positive timeout required.');
 signal?.throwIfAborted();
 const start=performance.now(),deadline=start+timeoutMs,controller=new AbortController();
 const phases=[];
 const mark=phase=>{const sample=Object.freeze({phase,elapsedMs:performance.now()-start});phases.push(sample);try{onPhase(sample);}catch{/* Diagnostics must never change asset readiness. */}};
 const abort=()=>controller.abort(signal.reason);signal?.addEventListener('abort',abort,{once:true});
 let timer,ktx,disposed=false,ended=false,initStarted=false,initSettled=false,codecFallback=null,codecUsed=LINING_QA.codec;
 const pendingPosts=new Set();
 // r180 init increments a module counter and may create its worker URL late.
 // Never dispose an uninitialized instance, or dispose twice; defer cleanup of
 // pending init until it settles so its eventual URL is also revoked.
 const dispose=()=>{if(ktx&&initStarted&&initSettled&&!disposed){disposed=true;ktx.dispose();}};
 const stopped=()=>ended||controller.signal.aborted;
 const stoppedError=()=>controller.signal.reason||Object.assign(new Error('Leather texture scope has ended.'),{name:'AbortError'});
 const guardLoader=()=>{
  const parse=ktx.parse,postMessage=ktx.workerPool.postMessage;
  ktx.parse=function(buffer,onLoad,onError){
   if(stopped()){onError?.(stoppedError());return;}
   return parse.call(this,buffer,texture=>{
    if(stopped()){texture?.dispose();onError?.(stoppedError());return;}
    return onLoad?.(texture);
   },onError);
  };
  ktx.workerPool.postMessage=function(...args){
   if(stopped())return Promise.reject(stoppedError());
   mark('worker-transcode-queued');
   // WorkerPool.dispose terminates workers but does not reject its promises.
   // Settle our owned parse chain on cancellation/end instead of orphaning it.
   return new Promise((resolve,reject)=>{
    let settled=false;
    const finish=(callback,value)=>{if(settled)return;settled=true;mark(callback===resolve?'worker-transcode-complete':'worker-transcode-error');pendingPosts.delete(stop);controller.signal.removeEventListener('abort',stop);callback(value);};
    const stop=()=>finish(reject,stoppedError());
    pendingPosts.add(stop);controller.signal.addEventListener('abort',stop,{once:true});
    try{Promise.resolve(postMessage.apply(this,args)).then(value=>stopped()?stop():finish(resolve,value),error=>finish(reject,error));}
    catch(error){finish(reject,error);}
   });
  };
 };
 const checkpoint=()=>{controller.signal.throwIfAborted();if(performance.now()>=deadline){const error=Object.assign(new Error('Leather texture load timed out.'),{name:'TimeoutError'});controller.abort(error);throw error;}};
 const interrupted=new Promise((_,reject)=>{
  controller.signal.addEventListener('abort',()=>reject(controller.signal.reason),{once:true});
  timer=setTimeout(()=>controller.abort(Object.assign(new Error('Leather texture load timed out.'),{name:'TimeoutError'})),timeoutMs);
 });
 const run=async()=>{
  mark('loader-import-start');const KtxLoader=await importKtxLoader();checkpoint();mark('loader-import-end');
  const manager=makeManager(),loader=makeLoader(manager);
  ktx=new KtxLoader(manager).setTranscoderPath(new URL(assetURL('./vendor/libs/basis/'),import.meta.url).href).setWorkerLimit(2);
  guardLoader();
  if(renderer.isWebGPURenderer)await renderer.init();
  checkpoint();ktx.detectSupport(renderer);
  checkpoint();
  mark('transcoder-init-start');const initialization=ktx.init();initStarted=true;
  // Consume rejection immediately and cancel the sibling texture transfer.
  // The parse overlaps normal preparation without duplicating asset requests.
  const initialized=Promise.resolve(initialization).then(
   ()=>{initSettled=true;mark('transcoder-init-end');if(ended)dispose();},
   error=>{initSettled=true;mark('transcoder-init-error');controller.abort(error);if(ended)dispose();}
  );
  checkpoint();
  // Private experiment: parse glTF and request unrelated dependencies while
  // the verified normal is assembled. Only that normal's KTX load waits.
  let readyNormal,failNormal,parsed=null,adopted=false,disposedParsed=false,normalServed=false,normalRequests=0;
  const normalReady=new Promise((resolve,reject)=>{readyNormal=resolve;failNormal=reject;});normalReady.catch(()=>{});
  controller.signal.addEventListener('abort',()=>failNormal(stoppedError()),{once:true});if(controller.signal.aborted)failNormal(stoppedError());
  const originalLoad=ktx.load,normalSuffix='/leather-assets/r14/outer-normal-4k.ktx2',expectedOrigin=new URL(baseURL).origin;
  ktx.load=function(url,onLoad,onProgress,onError){
   let target,match=false;try{target=new URL(url,baseURL);match=target.origin===expectedOrigin&&target.pathname.endsWith(normalSuffix);}catch{}
   const gate=match?Promise.all([initialized,normalReady]):initialized;
   Promise.resolve(gate).then(value=>{checkpoint();if(match&&target.href!==value[1])throw new Error('Normal texture URL does not match verified manifest');if(match){normalServed=true;normalRequests++;}if(typeof originalLoad!=='function')throw new Error('KTX loader has no load method');return originalLoad.call(this,url,onLoad,onProgress,onError);}).catch(error=>onError?.(error));
  };
  loader.setKTX2Loader(ktx);mark('gltf-dependencies-early-start');
  const avifProbe=LINING_QA.codec.includes('avif')?Promise.resolve().then(()=>probeAvif({signal:controller.signal})):Promise.resolve(true);
  const load=async url=>{checkpoint();const before=normalRequests;const value=await loadAsset(url,{loader,signal:controller.signal,timeoutMs:Math.max(1,deadline-performance.now()),disposeUnused});if(requireVerifiedNormal&&normalRequests===before){disposeUnused(value.gltf);throw new Error('Verified leather normal was not requested by this glTF');}return value;};
  const parsedPromise=Promise.resolve().then(async()=>{
   if(LINING_QA.url===R14_LEATHER_URL)return load(R14_LEATHER_URL);
   const supported=await avifProbe;checkpoint();
   const outcome=await loadWithLiningFallback({loadVariant:()=>load(LINING_QA.url),loadBaseline:()=>load(R14_LEATHER_URL),signal:controller.signal,skipVariant:!supported,dispose:item=>disposeUnused(item.gltf)});
   codecFallback=outcome.fallbackReason||null;codecUsed=outcome.used==='baseline'?'baseline':LINING_QA.codec;return outcome.result;
  }).then(value=>{
   parsed=value;if(stopped()&&!disposedParsed){disposedParsed=true;disposeUnused(value.gltf);throw stoppedError();}return value;
  },error=>{if(!controller.signal.aborted)controller.abort(error);throw error;});
  parsedPromise.catch(()=>{});
  mark('normal-prepare-start');
  let result,retainedLow=null;
  try{
   result=await withTexture({manager,baseURL:assetBase('leather-assets',baseURL),manifestURL:initialNormal==='full'?'leather-assets/r14/outer-normal-4k.chunks.json':'leather-assets/r14/outer-normal-2k.manifest.json',
    signal:controller.signal,deadline,maxBytes:selectedNormal.bytes,expectedBytes:selectedNormal.bytes,expectedSha256:selectedNormal.sha256,
    onVerifiedBytes:initialNormal==='progressive-2k'?bytes=>{retainedLow=bytes;}:null,
    disposeLateResult:late=>{if(late===parsed)disposedParsed=true;disposeUnused(late.gltf);},onPhase:sample=>mark('normal:'+sample.phase)},
    async({canonicalTextureURL})=>{mark('normal-prepare-end');readyNormal(canonicalTextureURL);const [out]=await Promise.all([parsedPromise,initialized]);checkpoint();if(requireVerifiedNormal&&!normalServed)throw new Error('Verified leather normal was not requested');mark('gltf-dependencies-parse-transcode-end');return out;});
   if(initialNormal==='progressive-2k'&&!retainedLow)throw Error('Verified 2K normal bytes were not retained');
   adopted=true;
  }catch(error){failNormal(error);if(!controller.signal.aborted)controller.abort(error);if(parsed&&!adopted&&!disposedParsed){disposedParsed=true;disposeUnused(parsed.gltf);}throw error;}

  let geometryProof;
  try{checkpoint();verifyTextures(result.gltf);mark('geometry-identity-start');geometryProof=await verifyGeometry(result.gltf,AUTHORED_LEATHER_IDENTITY);checkpoint();mark('geometry-identity-end');}catch(error){disposeUnused(result.gltf);throw error;}
  return {...result,progressiveNormalBytes:retainedLow,metrics:{...result.metrics,assetDelivery:{requested:'craft14',used:'ktx2',originalURL:R14_LEATHER_URL,fallbackReason:codecFallback,liningCodecQA:{...LINING_QA,used:codecUsed},pipelineMs:performance.now()-start},
   authoredLeather:geometryProof,loadingPhases:phases.slice(),
   chunkedNormal:{...selectedNormal,initialNormal,byteExactReassembly:true},dependencyBytesNotIncludedInBodyBytes:true}};
 };
 try{return await Promise.race([run(),interrupted]);}
 finally{ended=true;if(!controller.signal.aborted)controller.abort(Object.assign(new Error('Leather texture scope has ended.'),{name:'AbortError'}));for(const stop of pendingPosts)stop();clearTimeout(timer);signal?.removeEventListener('abort',abort);dispose();}
}

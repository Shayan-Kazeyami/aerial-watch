import {assetURL,assetBase} from './assembly-asset-routing.js';
import {AUTHORED_LEATHER_IDENTITY} from './assembly-leather-authoring-identity.js';
import {verifyLoadedLeatherGeometry} from './assembly-leather-identity.js';
import {loadGLTFAsset} from './assembly-loading.js';
import {withChunkedTexture} from './assembly-chunked-texture.js';

export const R14_LEATHER_URL='leather-assets/r14/leather.gltf';
export const R14_NORMAL_IDENTITY=Object.freeze({bytes:16562348,sha256:'bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585'});
const importLoader=()=>import('./vendor/loaders/KTX2Loader.js').then(module=>module.KTX2Loader);

// Explicit candidate, not a silent quality fallback. One dedicated manager
// confines the normal's temporary Blob URL to this single glTF parse.
export async function loadR14KtxLeather({renderer,makeManager,makeLoader,signal,timeoutMs=120000,disposeUnused=()=>{},baseURL=globalThis.location?.href,onPhase=()=>{}},
 {importKtxLoader=importLoader,loadAsset=loadGLTFAsset,withTexture=withChunkedTexture,verifyGeometry=verifyLoadedLeatherGeometry}={}){
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('Positive timeout required.');
 signal?.throwIfAborted();
 const start=performance.now(),deadline=start+timeoutMs,controller=new AbortController();
 const phases=[];
 const mark=phase=>{const sample=Object.freeze({phase,elapsedMs:performance.now()-start});phases.push(sample);try{onPhase(sample);}catch{/* Diagnostics must never change asset readiness. */}};
 const abort=()=>controller.abort(signal.reason);signal?.addEventListener('abort',abort,{once:true});
 let timer,ktx,disposed=false,ended=false,initStarted=false,initSettled=false;
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
  // No second geometry/image download, eager GLTF parse or extra texture buffer.
  const initialized=Promise.resolve(initialization).then(
   ()=>{initSettled=true;mark('transcoder-init-end');if(ended)dispose();},
   error=>{initSettled=true;mark('transcoder-init-error');controller.abort(error);if(ended)dispose();}
  );
  checkpoint();mark('normal-prepare-start');
  const result=await withTexture({manager,baseURL:assetBase('leather-assets',baseURL),manifestURL:'leather-assets/r14/outer-normal-4k.chunks.json',
   signal:controller.signal,deadline,maxBytes:R14_NORMAL_IDENTITY.bytes,expectedBytes:R14_NORMAL_IDENTITY.bytes,expectedSha256:R14_NORMAL_IDENTITY.sha256,
   disposeLateResult:late=>disposeUnused(late.gltf),onPhase:sample=>mark('normal:'+sample.phase)},
   async({signal,remainingMs})=>{
    mark('normal-prepare-end');await initialized;checkpoint();loader.setKTX2Loader(ktx);
    mark('gltf-dependencies-parse-transcode-start');
    const result=await loadAsset(R14_LEATHER_URL,{loader,signal,timeoutMs:remainingMs(),disposeUnused});
    mark('gltf-dependencies-parse-transcode-end');return result;
   });
  let geometryProof;
  try{checkpoint();mark('geometry-identity-start');geometryProof=await verifyGeometry(result.gltf,AUTHORED_LEATHER_IDENTITY);checkpoint();mark('geometry-identity-end');}catch(error){disposeUnused(result.gltf);throw error;}
  return {...result,metrics:{...result.metrics,assetDelivery:{requested:'craft14',used:'ktx2',originalURL:R14_LEATHER_URL,fallbackReason:null,pipelineMs:performance.now()-start},
   authoredLeather:geometryProof,loadingPhases:phases.slice(),
   chunkedNormal:{...R14_NORMAL_IDENTITY,byteExactReassembly:true},dependencyBytesNotIncludedInBodyBytes:true}};
 };
 try{return await Promise.race([run(),interrupted]);}
 finally{ended=true;if(!controller.signal.aborted)controller.abort(Object.assign(new Error('Leather texture scope has ended.'),{name:'AbortError'}));for(const stop of pendingPosts)stop();clearTimeout(timer);signal?.removeEventListener('abort',abort);dispose();}
}

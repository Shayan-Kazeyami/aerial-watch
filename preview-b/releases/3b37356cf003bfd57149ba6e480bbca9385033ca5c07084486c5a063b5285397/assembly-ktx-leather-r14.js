import {assetURL,assetBase} from './assembly-asset-routing.js';
import {loadGLTFAsset} from './assembly-loading.js';
import {withChunkedTexture} from './assembly-chunked-texture.js';

export const R14_LEATHER_URL='leather-assets/r14/leather.gltf';
export const R14_NORMAL_IDENTITY=Object.freeze({bytes:16562348,sha256:'bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585'});
const importLoader=()=>import('./vendor/loaders/KTX2Loader.js').then(module=>module.KTX2Loader);

// Explicit candidate, not a silent quality fallback. One dedicated manager
// confines the normal's temporary Blob URL to this single glTF parse.
export async function loadR14KtxLeather({renderer,makeManager,makeLoader,signal,timeoutMs=120000,disposeUnused=()=>{},baseURL=globalThis.location?.href},
 {importKtxLoader=importLoader,loadAsset=loadGLTFAsset,withTexture=withChunkedTexture}={}){
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('Positive timeout required.');
 signal?.throwIfAborted();
 const start=performance.now(),deadline=start+timeoutMs,controller=new AbortController();
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
   // WorkerPool.dispose terminates workers but does not reject its promises.
   // Settle our owned parse chain on cancellation/end instead of orphaning it.
   return new Promise((resolve,reject)=>{
    let settled=false;
    const finish=(callback,value)=>{if(settled)return;settled=true;pendingPosts.delete(stop);controller.signal.removeEventListener('abort',stop);callback(value);};
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
  const KtxLoader=await importKtxLoader();checkpoint();
  const manager=makeManager(),loader=makeLoader(manager);
  ktx=new KtxLoader(manager).setTranscoderPath(new URL(assetURL('./vendor/libs/basis/'),import.meta.url).href).setWorkerLimit(2);
  guardLoader();
  if(renderer.isWebGPURenderer)await ktx.detectSupportAsync(renderer);else ktx.detectSupport(renderer);
  checkpoint();
  const initialization=ktx.init();initStarted=true;
  await Promise.resolve(initialization).then(
   ()=>{initSettled=true;if(ended)dispose();},
   error=>{initSettled=true;if(ended)dispose();throw error;}
  );
  checkpoint();loader.setKTX2Loader(ktx);
  const result=await withTexture({manager,baseURL:assetBase('leather-assets',baseURL),manifestURL:'leather-assets/r14/outer-normal-4k.chunks.json',
   signal:controller.signal,deadline,maxBytes:R14_NORMAL_IDENTITY.bytes,expectedBytes:R14_NORMAL_IDENTITY.bytes,expectedSha256:R14_NORMAL_IDENTITY.sha256,
   disposeLateResult:late=>disposeUnused(late.gltf)},
   ({signal,remainingMs})=>loadAsset(R14_LEATHER_URL,{loader,signal,timeoutMs:remainingMs(),disposeUnused}));
  try{checkpoint();}catch(error){disposeUnused(result.gltf);throw error;}
  return {...result,metrics:{...result.metrics,assetDelivery:{requested:'craft14',used:'ktx2',originalURL:R14_LEATHER_URL,fallbackReason:null,pipelineMs:performance.now()-start},
   chunkedNormal:{...R14_NORMAL_IDENTITY,byteExactReassembly:true},dependencyBytesNotIncludedInBodyBytes:true}};
 };
 try{return await Promise.race([run(),interrupted]);}
 finally{ended=true;for(const stop of pendingPosts)stop();clearTimeout(timer);signal?.removeEventListener('abort',abort);dispose();}
}

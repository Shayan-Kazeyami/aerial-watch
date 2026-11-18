import {loadGLTFAsset} from './assembly-loading.js';
import {decompressGzipAsset} from './assembly-optimized-loading.js';
const importDecoder=()=>import('../f3ab38493b7bc5c4af84728add913e54938d0db276143a7b765a7803f361bb44/vendor/meshopt/meshopt_decoder.mjs').then(m=>m.MeshoptDecoder);
const sha=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),x=>x.toString(16).padStart(2,'0')).join('');
// No lower-detail or unverified fallback. Transport and decoded GLB identities differ.
export async function loadHybridCaseDelivery(options,data,{loadAsset=loadGLTFAsset,decompress=decompressGzipAsset,decoderFactory=importDecoder}={}){
 const d=data.delivery,{loader,signal:callerSignal,timeoutMs=120000}=options;
 if(!d||d.encoding!=='meshopt-gzip'||d.glbSHA256!==data.glbSHA256)throw Error('Invalid hybrid delivery manifest.');
 if(!loader?.parseAsync||!loader?.setMeshoptDecoder)throw TypeError('Hybrid delivery requires meshopt-capable GLTFLoader.');
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw RangeError('timeoutMs must be positive.');
 callerSignal?.throwIfAborted();const c=new AbortController(),signal=c.signal,expires=performance.now()+timeoutMs;
 const abort=()=>c.abort(callerSignal.reason),expire=()=>{const e=new Error('Hybrid CASE delivery deadline expired.');e.name='TimeoutError';c.abort(e);};callerSignal?.addEventListener('abort',abort,{once:true});
 const timer=setTimeout(expire,timeoutMs),check=()=>{if(!signal.aborted&&performance.now()>=expires)expire();signal.throwIfAborted();};
 const strictLoader={parseAsync:async(buffer,path)=>{
  check();if(buffer.byteLength!==d.gzipBytes||await sha(buffer)!==d.gzipSHA256)throw Error('Hybrid compressed asset identity mismatch.');check();
  const decoded=await decompress(buffer,{signal,expectedBytes:d.glbBytes});check();
  if(decoded.byteLength!==d.glbBytes||await sha(decoded)!==d.glbSHA256)throw Error('Hybrid decoded GLB identity mismatch.');check();
  const decoder=await decoderFactory();await decoder?.ready;check();
  if(!decoder?.supported||typeof decoder.decodeGltfBufferAsync!=='function')throw Error('Hybrid meshopt decoder unavailable.');
  loader.setMeshoptDecoder(decoder);check();return loader.parseAsync(decoded,path);
 }};
 try{
  const result=await loadAsset(d.url,{...options,signal,loader:strictLoader,expectedSHA256:d.gzipSHA256});
  try{check();}catch(e){options.disposeUnused?.(result.gltf||result);throw e;}
  return {...result,metrics:{...result.metrics,verifiedGLBSHA256:d.glbSHA256,assetDelivery:{...d,rawReferenceSHA256:data.rawReferenceSHA256,lossless:true,fallback:false}}};
 }finally{clearTimeout(timer);callerSignal?.removeEventListener('abort',abort);}
}

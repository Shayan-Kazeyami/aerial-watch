import {loadGLTFAsset} from './assembly-loading.js';
import {decompressGzipAsset} from './assembly-optimized-loading.js';
import {CASE_COMBINED_DELIVERY} from './assembly-case-combined-delivery-data.js';
const importDecoder=()=>import('./vendor/meshopt/meshopt_decoder.mjs').then(m=>m.MeshoptDecoder);
const sha=async buffer=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)),v=>v.toString(16).padStart(2,'0')).join('');
// Selected fine geometry is mandatory: no raw-asset, coarse-geometry or source fallback.
// The ordinary loader owns transfer/decode deadline and late parsed-scene disposal.
export async function loadCombinedCaseAsset(options={},configuration={}){
 const {loadAsset=loadGLTFAsset,decoderFactory=importDecoder,decompress=decompressGzipAsset}=configuration;
 const {loader,signal:callerSignal,timeoutMs=120000}=options;if(!loader?.parseAsync||!loader?.setMeshoptDecoder)throw new TypeError('Combined CASE requires a meshopt-capable GLTF loader.');
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('timeoutMs must be positive.');
 callerSignal?.throwIfAborted();
 const controller=new AbortController(),signal=controller.signal;
 const abort=()=>controller.abort(callerSignal.reason);callerSignal?.addEventListener('abort',abort,{once:true});
 const expires=performance.now()+timeoutMs;
 const expire=()=>{const error=new Error('Selected combined CASE took too long to load.');error.name='TimeoutError';controller.abort(error);};
 const timer=setTimeout(expire,timeoutMs);
 const checkpoint=()=>{if(!signal.aborted&&performance.now()>=expires)expire();signal.throwIfAborted();};
 const strictLoader={parseAsync:async(buffer,path)=>{
  checkpoint();
  if(buffer.byteLength!==CASE_COMBINED_DELIVERY.gzipBytes||await sha(buffer)!==CASE_COMBINED_DELIVERY.gzipSHA256)throw new Error('Selected combined CASE compressed asset identity mismatch.');
  const decoded=await decompress(buffer,{signal,expectedBytes:CASE_COMBINED_DELIVERY.decodedBytes});checkpoint();
  if(decoded.byteLength!==CASE_COMBINED_DELIVERY.decodedBytes||await sha(decoded)!==CASE_COMBINED_DELIVERY.decodedSHA256)throw new Error('Selected combined CASE decoded asset identity mismatch.');
  const decoder=await decoderFactory();await decoder?.ready;checkpoint();
  if(!decoder?.supported||typeof decoder.decodeGltfBufferAsync!=='function')throw new Error('Selected combined CASE meshopt decoder unavailable.');
  loader.setMeshoptDecoder(decoder);return loader.parseAsync(decoded,path);
 }};
 try{
  const result=await loadAsset(CASE_COMBINED_DELIVERY.url,{...options,signal,loader:strictLoader});
  try{checkpoint();}catch(error){options.disposeUnused?.(result.gltf||result);throw error;}
  return {...result,metrics:{...result.metrics,assetDelivery:{requested:'fine-combined',used:'exact-meshopt-gzip',fallback:false,...CASE_COMBINED_DELIVERY}}};
 }finally{clearTimeout(timer);callerSignal?.removeEventListener('abort',abort);}
}

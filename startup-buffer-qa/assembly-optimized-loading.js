import {createByteCollector} from './assembly-byte-collector.js';
import {loadGLTFAsset} from './assembly-loading.js';

// Opt-in only. Originals remain the compatibility and failure fallback.
export const LOSSLESS_ASSETS=Object.freeze({
  'rebuild/assembly.glb':'optimized-assets/rebuild__assembly.meshopt.glb.gz',
  'premium-face/face-svg04.glb':'optimized-assets/premium-face__face-svg04.meshopt.glb',
  'quality-study/leather-craft-r11.glb':'optimized-assets/quality-study__leather-craft-r11.meshopt.glb',
});
const GZIP_DECODED_BYTES=14359552;
const createGzipDecompressor=()=>{
  if(typeof DecompressionStream!=='function')throw new Error('Gzip decompression is unavailable.');
  return new DecompressionStream('gzip');
};

// Explicit .gz file content, not an HTTP Content-Encoding claim. Bound expansion
// to the audited GLB size and cancel/release the stream on error or interruption.
export async function decompressGzipAsset(buffer,{signal,expectedBytes=GZIP_DECODED_BYTES,createDecompressor=createGzipDecompressor,onBuffering=()=>{}}={}) {
  signal?.throwIfAborted();
  if(!Number.isSafeInteger(expectedBytes)||expectedBytes<=0)throw new RangeError('Invalid audited decoded size.');
  // Feed the owned input view directly; Blob construction snapshots another full
  // compressed buffer before producing its stream. Callers retain input ownership.
  const input=ArrayBuffer.isView(buffer)?new Uint8Array(buffer.buffer,buffer.byteOffset,buffer.byteLength):new Uint8Array(buffer);
  const stream=new ReadableStream({start(controller){controller.enqueue(input);controller.close();}}).pipeThrough(createDecompressor());
  const reader=stream.getReader(),sink=createByteCollector(expectedBytes);let length=0,complete=false;
  const cancel=()=>{reader.cancel(signal?.reason).catch(()=>{});};
  signal?.addEventListener('abort',cancel,{once:true});
  try {
    for(;;){signal?.throwIfAborted();const {done,value}=await reader.read();signal?.throwIfAborted();if(done){complete=true;break;}length+=value.byteLength;if(length>expectedBytes)throw new Error('Gzip asset exceeds its audited decoded size.');sink.append(value);}
    if(length!==expectedBytes)throw new Error('Gzip asset does not match its audited decoded size.');
    const result=sink.finish();onBuffering(result.metrics);return result.buffer;
  }finally{signal?.removeEventListener('abort',cancel);if(!complete)cancel();reader.releaseLock();}
}
const importDecoder=()=>import('./vendor/meshopt/meshopt_decoder.mjs').then(module=>module.MeshoptDecoder);

/** Transfer optimization only; does not change rendering settings or quality.
 * Pass {optIn:true} explicitly (e.g. query assets=meshopt). Decoder/load injection
 * exists for deterministic failure tests, not an external code-loading surface.
 */
export async function loadOptimizedGLTFAsset(originalURL,options={},configuration={}) {
  const {optIn=false,decoderFactory=importDecoder,loadAsset=loadGLTFAsset,createDecompressor=createGzipDecompressor}=configuration;
  const pipelineStarted=performance.now();
  const key=String(originalURL).split(/[?#]/,1)[0].replace(/^\.\//,'');
  const optimizedURL=optIn?LOSSLESS_ASSETS[key]:null;
  const annotate=(result,used,fallbackReason=null)=>({...result,metrics:{...result.metrics,
    assetDelivery:{requested:optIn?'meshopt':'raw',used,originalURL,optimizedURL,fallbackReason,pipelineMs:performance.now()-pipelineStarted}}});
  if(!optimizedURL)return annotate(await loadAsset(originalURL,options),'raw');
  const {signal,timeoutMs=120000,disposeUnused=()=>{}}=options;
  if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('timeoutMs must be positive.');
  signal?.throwIfAborted();
  const controller=new AbortController(),started=performance.now();let timer,onAbort;
  const timeout=()=>{const error=new Error('The watch asset took too long to load. Check your connection and reload the viewer.');error.name='TimeoutError';return error;};
  const interrupted=new Promise((_,reject)=>{
    onAbort=()=>{controller.abort(signal.reason);reject(signal.reason);};
    signal?.addEventListener('abort',onAbort,{once:true});
    timer=setTimeout(()=>{const error=timeout();controller.abort(error);reject(error);},timeoutMs);
  });
  const checkpoint=()=>{controller.signal.throwIfAborted();const remaining=timeoutMs-(performance.now()-started);if(remaining<=0){const error=timeout();controller.abort(error);throw error;}return remaining;};
  const attempt=async url=>{
    let decompressionMs=0,decompressedBytes=0;
    const gzip=url===optimizedURL&&url.endsWith('.gz');
    const loader=gzip?{parseAsync:async(buffer,baseURL)=>{
      const begin=performance.now();
      const decoded=await decompressGzipAsset(buffer,{signal:controller.signal,createDecompressor});
      checkpoint();decompressionMs=performance.now()-begin;decompressedBytes=decoded.byteLength;
      return options.loader.parseAsync(decoded,baseURL);
    }}:options.loader;
    const result=await loadAsset(url,{...options,loader,signal:controller.signal,timeoutMs:checkpoint()});
    try{checkpoint();}catch(error){disposeUnused(result.gltf);throw error;}
    return gzip?{...result,metrics:{...result.metrics,transportFormat:'explicit-gzip',decompressionMs,decompressedBytes,parseMsIncludesDecompression:true}}:result;
  };
  const run=async()=>{
    let stage='decoder-import';
    try {
      const decoder=await decoderFactory();checkpoint();stage='decoder-unsupported';
      if(!decoder?.supported)throw new Error('Meshopt WebAssembly decoder is unavailable.');
      stage='decoder-ready';await decoder.ready;checkpoint();
      stage='decoder-configuration';
      if(typeof options.loader?.setMeshoptDecoder!=='function')throw new Error('GLTFLoader does not support meshopt.');
      options.loader.setMeshoptDecoder(decoder);
      if(optimizedURL.endsWith('.gz')){stage='gzip-support';const probe=createDecompressor();await probe.writable.abort();checkpoint();}
      stage='compressed-load';
      return annotate(await attempt(optimizedURL),'meshopt');
    } catch(error) {
      // Cancellation/deadline is terminal, never a reason to download another asset.
      if(error?.name==='AbortError'||error?.name==='TimeoutError'){controller.abort(error);throw error;}
      checkpoint();
      return annotate(await attempt(originalURL),'raw',{stage,name:error?.name||'Error',message:String(error?.message||error)});
    }
  };
  try{return await Promise.race([run(),interrupted]);}
  finally{clearTimeout(timer);signal?.removeEventListener('abort',onAbort);}
}

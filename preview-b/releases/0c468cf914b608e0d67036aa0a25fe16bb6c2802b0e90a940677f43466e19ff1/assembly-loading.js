import {assetURL} from './assembly-asset-routing.js';
// One bounded retry for transient transfer-start failures only. Parsing and
// decoding are never retried, and both attempts share the original deadline.
async function fetchAsset(url,{fetcher=fetch,signal,retryDelayMs=250}={}) {
 for(let attempt=0;;attempt++){
  signal?.throwIfAborted();
  let response;
  try{response=await fetcher(url,{signal});}
  catch(error){if(attempt||error?.name!=='TypeError'||signal?.aborted)throw error;}
  if(response && (attempt||![408,429,500,502,503,504].includes(response.status)))return response;
  if(response?.body)await response.body.cancel().catch(()=>{});
  signal?.throwIfAborted();
  await new Promise((resolve,reject)=>{
   const cleanup=()=>signal?.removeEventListener('abort',abort);
   const abort=()=>{clearTimeout(timer);cleanup();reject(signal.reason);};
   const timer=setTimeout(()=>{cleanup();resolve();},retryDelayMs);
   signal?.addEventListener('abort',abort,{once:true});
   if(signal?.aborted)abort();
  });
 }
}

// Bound stalled transfers and parsing while preserving caller cancellation.
async function withLoadDeadline(load,{signal,timeoutMs=120000}={}) {
  if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('timeoutMs must be positive.');
  signal?.throwIfAborted();
  const controller=new AbortController();
  let timer,onAbort;
  const interrupted=new Promise((_,reject)=>{
    onAbort=()=>{controller.abort(signal.reason);reject(signal.reason);};
    signal?.addEventListener('abort',onAbort,{once:true});
    timer=setTimeout(()=>{
      const error=new Error('The watch asset took too long to load. Check your connection and reload the viewer.');
      error.name='TimeoutError';controller.abort(error);reject(error);
    },timeoutMs);
  });
  try{return await Promise.race([load(controller.signal),interrupted]);}
  finally{clearTimeout(timer);signal?.removeEventListener('abort',onAbort);}
}

export function loadGLTFAsset(url,options={}) {
  url=assetURL(url);
  return withLoadDeadline(signal=>loadGLTFAssetUnbounded(url,{...options,signal}),options);
}

export function loadJSONAsset(url,{fetcher=fetch,...options}={}) {
  url=assetURL(url);
  return withLoadDeadline(async signal=>{
    const response=await fetchAsset(url,{fetcher,signal,retryDelayMs:options.retryDelayMs});
    if(!response.ok)throw new Error(`Movement metadata could not load (${response.status}).`);
    const value=await response.json();
    signal.throwIfAborted();
    return value;
  },options);
}

async function loadGLTFAssetUnbounded(url,{loader,fetcher=fetch,onProgress=()=>{},now=()=>performance.now(),baseURL=location.href,signal,retryDelayMs,disposeUnused=()=>{},expectedSHA256=null}={}) {
  signal?.throwIfAborted();
  const start=now(),response=await fetchAsset(url,{fetcher,signal,retryDelayMs});
  if(!response.ok)throw new Error(`Asset ${url} could not load (${response.status}).`);
  const total=Number(response.headers?.get('content-length'))||0;let buffer,loaded=0;
  if(response.body?.getReader) {
    const reader=response.body.getReader(),chunks=[];let completed=false;
    const cancel=()=>{reader.cancel(signal?.reason).catch(()=>{});};
    signal?.addEventListener('abort',cancel,{once:true});
    try{for(;;){signal?.throwIfAborted();const {done,value}=await reader.read();if(done){completed=true;break;}chunks.push(value);loaded+=value.byteLength;onProgress({loaded,total,lengthComputable:total>0});}}
    finally{signal?.removeEventListener('abort',cancel);if(!completed)cancel();reader.releaseLock();}
    const bytes=new Uint8Array(loaded);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}buffer=bytes.buffer;
  } else {buffer=await response.arrayBuffer();loaded=buffer.byteLength;onProgress({loaded,total,lengthComputable:total>0});}
  signal?.throwIfAborted();
  if(expectedSHA256!==null){
    if(!/^[a-f0-9]{64}$/.test(expectedSHA256))throw new Error('Invalid expected support SHA-256.');
    const digest=await globalThis.crypto.subtle.digest('SHA-256',buffer);signal?.throwIfAborted();
    const actual=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
    if(actual!==expectedSHA256)throw new Error('Support asset SHA-256 mismatch.');
  }
  const transferred=now(),gltf=await loader.parseAsync(buffer,new URL('.',new URL(url,baseURL)).href),parsed=now();
  if(signal?.aborted){disposeUnused(gltf);signal.throwIfAborted();}
  return {gltf,metrics:{url,bodyBytes:loaded,verifiedSHA256:expectedSHA256,transferMs:transferred-start,parseMs:parsed-transferred,totalMs:parsed-start}};
}

// Optional failures cannot prevent a verified original assembly from opening.
export async function loadProgressiveAssembly({loadBaseline,loadMetadata,loadProposal,onBaseline,onProposal,onWarning=()=>{},onPhase=()=>{},signal,disposeUnused=()=>{}}) {
  onPhase('baseline-loading');
  const proposal=Promise.resolve().then(loadProposal).then(value=>({value}),error=>({error}));
  let baseline,metadata,loadedBaseline,abandoned=false;
  const original=Promise.resolve().then(loadBaseline).then(value=>{loadedBaseline=value;if(abandoned)disposeUnused(value);return value;});
  try{[baseline,metadata]=await Promise.all([original,loadMetadata()]);signal?.throwIfAborted();await onBaseline(baseline,metadata);}
  catch(error){abandoned=true;if(loadedBaseline)disposeUnused(loadedBaseline);proposal.then(result=>{if(result.value)disposeUnused(result.value);});throw error;}
  onPhase('baseline-ready');
  const optional=await proposal;
  if(signal?.aborted){if(optional.value)disposeUnused(optional.value);signal.throwIfAborted();}
  if(optional.error){onWarning(optional.error);onPhase('proposal-unavailable');return {baseline:true,proposal:false};}
  try{await onProposal(optional.value);onPhase('proposal-ready');return {baseline:true,proposal:true};}
  catch(error){disposeUnused(optional.value);onWarning(error);onPhase('proposal-unavailable');return {baseline:true,proposal:false};}
}

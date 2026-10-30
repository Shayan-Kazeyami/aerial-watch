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
  return withLoadDeadline(signal=>loadGLTFAssetUnbounded(url,{...options,signal}),options);
}

export function loadJSONAsset(url,{fetcher=fetch,...options}={}) {
  return withLoadDeadline(async signal=>{
    const response=await fetcher(url,{signal});
    if(!response.ok)throw new Error(`Movement metadata could not load (${response.status}).`);
    const value=await response.json();
    signal.throwIfAborted();
    return value;
  },options);
}

async function loadGLTFAssetUnbounded(url,{loader,fetcher=fetch,onProgress=()=>{},now=()=>performance.now(),baseURL=location.href,signal,disposeUnused=()=>{}}={}) {
  signal?.throwIfAborted();
  const start=now(),response=await fetcher(url,{signal});
  if(!response.ok)throw new Error(`Asset ${url} could not load (${response.status}).`);
  const total=Number(response.headers?.get('content-length'))||0;let buffer,loaded=0;
  if(response.body?.getReader) {
    const reader=response.body.getReader(),chunks=[];
    try{for(;;){signal?.throwIfAborted();const {done,value}=await reader.read();if(done)break;chunks.push(value);loaded+=value.byteLength;onProgress({loaded,total,lengthComputable:total>0});}}
    finally{reader.releaseLock();}
    const bytes=new Uint8Array(loaded);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}buffer=bytes.buffer;
  } else {buffer=await response.arrayBuffer();loaded=buffer.byteLength;onProgress({loaded,total,lengthComputable:total>0});}
  signal?.throwIfAborted();
  const transferred=now(),gltf=await loader.parseAsync(buffer,new URL('.',new URL(url,baseURL)).href),parsed=now();
  if(signal?.aborted){disposeUnused(gltf);signal.throwIfAborted();}
  return {gltf,metrics:{url,bodyBytes:loaded,transferMs:transferred-start,parseMs:parsed-transferred,totalMs:parsed-start}};
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

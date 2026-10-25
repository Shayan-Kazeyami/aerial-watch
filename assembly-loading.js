export async function loadGLTFAsset(url,{loader,fetcher=fetch,onProgress=()=>{},now=()=>performance.now(),baseURL=location.href,signal,disposeUnused=()=>{}}={}) {
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

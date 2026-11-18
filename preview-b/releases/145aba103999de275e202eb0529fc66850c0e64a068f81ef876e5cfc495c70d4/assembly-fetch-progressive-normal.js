import {verifyLowNormal} from './assembly-progressive-normal.js';
// Audited KTX header from the exact existing R14 4K normal. No new remote assets.
const HEADER_BASE64='q0tUWCAyMLsNChoKAAAAAAEAAAAAEAAAABAAAAAAAAAAAAAAAQAAAA0AAAACAAAAiAEAACwAAAC0AQAAlAAAAAAAAAAAAAAAAAAAAAAAAAB4+kIAAAAAADS+uQAAAAAAAAAAAQAAAABiCREAAAAAABbxMQAAAAAAAABAAAAAAAA5LwQAAAAAACnaDAAAAAAAAAAQAAAAAAD4BwEAAAAAAEEnAwAAAAAAAAAEAAAAAAAERAAAAAAAAPTDAAAAAAAAAAABAAAAAADmEgAAAAAAAB4xAAAAAAAAAEAAAAAAAABRBwAAAAAAAJULAAAAAAAAABAAAAAAAADYAwAAAAAAAHkDAAAAAAAAAAQAAAAAAADcAgAAAAAAAPwAAAAAAAAAAAEAAAAAAACTAgAAAAAAAEkAAAAAAAAAQAAAAAAAAAB6AgAAAAAAABkAAAAAAAAAEAAAAAAAAABhAgAAAAAAABkAAAAAAAAAEAAAAAAAAABIAgAAAAAAABkAAAAAAAAAEAAAAAAAAAAsAAAAAAAAAAIAKACmAAEAAwMAABAAAAAAAAAAAAB/AAAAAAAAAAAA/////xIAAABLVFhvcmllbnRhdGlvbgByZAAAACcAAABLVFh3cml0ZXIAdG9rdHggdjQuNC4yIC8gbGlia3R4IHY0LjQuMgAASwAAAEtUWHdyaXRlclNjUGFyYW1zAC0tZW5jb2RlIHVhc3RjIC0tdWFzdGNfcXVhbGl0eSAzIC0temNtcCAxOCAtLW5vcm1hbF9tb2RlAAA=';
const FULL_BYTES=16562348,FULL_SHA='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585';
const PART0_BYTES=8388608,TAIL_START=4389496,TAIL_BYTES=3999112,PART1_BYTES=8173740;
const PART0_SHA='32f662b3984b3efaf87889db2c8d0ba0779593de08390085d3d414ea0eea5a0b';
const TAIL_SHA='84ffbf04c9e13f590d4d38a0ff60e96b2d91150a3560185f2db3adea093ce793';
const PART1_SHA='e80c0155d8346517e1c6c0b46def43e06a97e21b1ed64f18d17b4fc64c816c49';
const digest=async(bytes,cryptoImpl)=>Array.from(new Uint8Array(await cryptoImpl.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
async function readExact(response,size,signal){
 if(!response.body?.getReader)throw Error('Normal chunk body unavailable');
 const reader=response.body.getReader(),out=new Uint8Array(size);let offset=0,done=false;
 const cancel=()=>reader.cancel(signal.reason).catch(()=>{});signal.addEventListener('abort',cancel,{once:true});
 try{while(true){signal.throwIfAborted();const r=await reader.read();signal.throwIfAborted();if(r.done){done=true;break;}if(offset+r.value.byteLength>size)throw Error('Normal chunk exceeds expected length');out.set(r.value,offset);offset+=r.value.byteLength;}if(offset!==size)throw Error('Normal chunk length mismatch');return out;}
 finally{signal.removeEventListener('abort',cancel);if(!done)cancel();reader.releaseLock();}
}
export async function fetchProgressiveNormal({low,baseURL,signal,timeoutMs=120000,fetchImpl=fetch,cryptoImpl=globalThis.crypto,onMetrics=()=>{}}){
 const base=new URL(baseURL),current=new URL(globalThis.location?.href||base);if(!['https:','http:'].includes(base.protocol)||base.origin!==current.origin)throw Error('Invalid origin');
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw RangeError('Invalid timeout');signal?.throwIfAborted();
 const controller=new AbortController();const abort=()=>controller.abort(signal.reason);signal?.addEventListener('abort',abort,{once:true});const timer=setTimeout(()=>controller.abort(Object.assign(Error('Normal upgrade timeout'),{name:'TimeoutError'})),timeoutMs);
 const interrupted=new Promise((_,reject)=>controller.signal.addEventListener('abort',()=>reject(controller.signal.reason),{once:true}));
 const request=async(name,headers)=>{controller.signal.throwIfAborted();const url=new URL(name,base);if(url.origin!==base.origin)throw Error('Invalid chunk origin');const response=await fetchImpl(url.href,{signal:controller.signal,redirect:'error',credentials:'same-origin',...(headers?{headers}:{})});if(controller.signal.aborted){await response.body?.cancel().catch(()=>{});controller.signal.throwIfAborted();}if(response.redirected||(response.url&&response.url!==url.href)){await response.body?.cancel().catch(()=>{});throw Error('Normal chunk redirect refused');}return response;};
 const readVerified=async(response,size,sha)=>{const bytes=await readExact(response,size,controller.signal);if(await digest(bytes,cryptoImpl)!==sha)throw Error('Normal chunk identity mismatch');controller.signal.throwIfAborted();return bytes;};
 const rejectResponse=async(response,message)=>{await response.body?.cancel().catch(()=>{});throw Error(message);};
 const run=async()=>{
  await verifyLowNormal(low,{cryptoImpl});controller.signal.throwIfAborted();
  // Range reuses already-verified 2K mip payload. If ignored, retain the verified
  // complete first chunk and never fetch it again. Requests remain sequential.
  const response=await request('outer-normal-4k.ktx2.part0',{Range:`bytes=${TAIL_START}-${PART0_BYTES-1}`});
  const ranged=response.status===206;
  if(ranged&&response.headers.get('Content-Range')!==`bytes ${TAIL_START}-${PART0_BYTES-1}/${PART0_BYTES}`)return rejectResponse(response,'Unexpected normal Content-Range');
  if(!ranged&&response.status!==200)return rejectResponse(response,'Normal chunk response unavailable');
  const first=await readVerified(response,ranged?TAIL_BYTES:PART0_BYTES,ranged?TAIL_SHA:PART0_SHA);
  const secondResponse=await request('outer-normal-4k.ktx2.part1');if(secondResponse.status!==200)return rejectResponse(secondResponse,'Unexpected second normal chunk status');
  const second=await readVerified(secondResponse,PART1_BYTES,PART1_SHA),full=new Uint8Array(FULL_BYTES);
  if(ranged){const header=Uint8Array.from(atob(HEADER_BASE64),c=>c.charCodeAt(0));full.set(header);full.set(low.subarray(560),584);full.set(first,TAIL_START);}else full.set(first);
  full.set(second,PART0_BYTES);
  if(await digest(full,cryptoImpl)!==FULL_SHA)throw Error('Full normal identity mismatch');controller.signal.throwIfAborted();
  onMetrics({delivery:ranged?'verified-range':'verified-full-chunk-fallback',upgradeBodyBytes:first.byteLength+second.byteLength,initialBodyBytes:low.byteLength,totalBodyBytes:low.byteLength+first.byteLength+second.byteLength,verifiedSHA256:FULL_SHA});
  return full;
 };
 try{return await Promise.race([run(),interrupted]);}finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);}
}

import {reconstructNormalSegments} from './assembly-progressive-normal.js';
const segments=Object.freeze([
 {name:'normal-4k-header.bin',bytes:584,sha:'490eda323dc09144c9bd6f5838e195896d892e989c9d6829024e03d3d10d8e79'},
 {name:'normal-4k-high.part0',bytes:8388608,sha:'4f1e9fd7c95dec3982a1e4c53c2c00317042333f746aa007c61d717305de242c'},
 {name:'normal-4k-high.part1',bytes:3784244,sha:'fc28d76f3f809fc59be8301aacc634b92dc8a238cd02506c034bb796d66655de'}]);
const digest=async(bytes,cryptoImpl)=>Array.from(new Uint8Array(await cryptoImpl.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
async function readExact(response,size,signal){
 if(!response.ok||!response.body?.getReader)throw Error('Segment response unavailable');
 const reader=response.body.getReader(),out=new Uint8Array(size);let offset=0,done=false;
 const cancel=()=>reader.cancel(signal.reason).catch(()=>{});signal.addEventListener('abort',cancel,{once:true});
 try{while(true){signal.throwIfAborted();const r=await reader.read();if(r.done){done=true;break;}if(offset+r.value.byteLength>size)throw Error('Segment exceeds expected length');out.set(r.value,offset);offset+=r.value.byteLength;}if(offset!==size)throw Error('Segment length mismatch');return out;}
 finally{signal.removeEventListener('abort',cancel);if(!done)cancel();reader.releaseLock();}
}
export async function fetchProgressiveNormal({low,baseURL,signal,timeoutMs=120000,fetchImpl=fetch,cryptoImpl=globalThis.crypto}){
 const base=new URL(baseURL),current=new URL(globalThis.location?.href||base);if(!['https:','http:'].includes(base.protocol)||base.origin!==current.origin)throw Error('Invalid origin');
 if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw RangeError('Invalid timeout');signal?.throwIfAborted();
 const controller=new AbortController();const abort=()=>controller.abort(signal.reason);signal?.addEventListener('abort',abort,{once:true});const timer=setTimeout(()=>controller.abort(Object.assign(Error('Normal upgrade timeout'),{name:'TimeoutError'})),timeoutMs);
 const interrupted=new Promise((_,reject)=>controller.signal.addEventListener('abort',()=>reject(controller.signal.reason),{once:true}));
 const run=async()=>{
  // Sequential requests limit peak transient memory and do not contend with initial view.
  const chunks=[];for(const item of segments){controller.signal.throwIfAborted();const url=new URL(item.name,base);if(url.origin!==base.origin)throw Error('Invalid segment origin');const response=await fetchImpl(url.href,{signal:controller.signal,redirect:'error',credentials:'same-origin'});if(controller.signal.aborted){await response.body?.cancel().catch(()=>{});controller.signal.throwIfAborted();}if(response.redirected||(response.url&&response.url!==url.href))throw Error('Segment redirect refused');const bytes=await readExact(response,item.bytes,controller.signal);if(await digest(bytes,cryptoImpl)!==item.sha)throw Error('Segment identity mismatch');controller.signal.throwIfAborted();chunks.push(bytes);}
  const full=await reconstructNormalSegments({low,header:chunks[0],part0:chunks[1],part1:chunks[2],cryptoImpl});controller.signal.throwIfAborted();return full;
 };
 try{return await Promise.race([run(),interrupted]);}finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);}
}

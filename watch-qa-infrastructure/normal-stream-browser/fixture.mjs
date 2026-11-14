import {pendingStreamFixture} from './pending-stream.mjs';
import {fetchProgressiveNormal as baseline} from './baseline.mjs';
import {fetchProgressiveNormal as candidate} from './candidate.mjs';
const assert=(v,m)=>{if(!v)throw Error(m)},sha=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),x=>x.toString(16).padStart(2,'0')).join('');
window.result={passed:false,cases:[],scope:'Native browser Fetch/WebCrypto/Streams, not viewer decoding/adoption or heap proof',tradeoff:'Candidate allocates full16.56MB before first body verification; early failures may allocate more.'};
try {
 const low=new Uint8Array(await(await fetch('./fixtures/normal-2048-existing-mips.ktx2')).arrayBuffer()),lowBefore=await sha(low);
 for(const route of ['range','fallback'])for(const [name,load] of [['baseline',baseline],['candidate',candidate]]){
  let metrics;const calls=[],buffers=[],hashes=[],cryptoImpl={subtle:{digest:async(a,b)=>{let id=buffers.indexOf(b.buffer);if(id<0){id=buffers.length;buffers.push(b.buffer)}hashes.push({id,bytes:b.byteLength,backing:b.buffer.byteLength});return crypto.subtle.digest(a,b)}}};
  const start=performance.now(),out=await load({low,baseURL:new URL('./'+route+'/',location.href).href,cryptoImpl,fetchImpl:(u,o)=>{calls.push({url:u,range:o.headers?.Range});return fetch(u,o)},onMetrics:m=>metrics=m});
  assert(await sha(out)==='bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585','output hash');assert(calls.length===2,'two requests');assert(await sha(low)===lowBefore,'low unchanged');assert(metrics.delivery===(route==='range'?'verified-range':'verified-full-chunk-fallback'),'delivery');
  if(name==='candidate')assert(hashes[1].id===hashes[2].id&&hashes[2].id===hashes[3].id,'single output backing');
  window.result.cases.push({route,name,ms:performance.now()-start,metrics,calls,hashes});
 }
 for(const [name,load]of[['baseline',baseline],['candidate',candidate]]){
  let calls=0,metrics=false;const controller=new AbortController(),f=pendingStreamFixture();
  const job=load({low,baseURL:new URL('./range/',location.href).href,signal:controller.signal,fetchImpl:async()=>{calls++;return new Response(f.stream,{status:206,headers:{'Content-Range':'bytes 4389496-8388607/8388608'}})},onMetrics:()=>metrics=true});
  await f.pendingRead;assert(f.state.acquired===1&&f.state.readCalls===1&&f.state.pending&&f.stream.locked,'loader owns pending reader before abort');const beforeAbort={...f.state};controller.abort(new Error('synthetic QA cancellation'));let rejected=false;try{await job}catch(e){rejected=/synthetic QA cancellation/.test(e.message)}
  await new Promise(r=>setTimeout(r,0));assert(rejected&&f.state.cancelled&&f.state.released===1&&!f.stream.locked&&calls===1&&!metrics,'cancel ownership release and publication');window.result.cases.push({name,route:'controlled-native-stream-abort',rejected,beforeAbort,afterAbort:{...f.state},streamLocked:f.stream.locked,calls,metrics});
 }
 window.result.passed=true;document.querySelector('#status').textContent=JSON.stringify(window.result,null,2);
}catch(e){window.result.failure=e.stack;document.querySelector('#status').textContent=e.stack;}
window.done=true;

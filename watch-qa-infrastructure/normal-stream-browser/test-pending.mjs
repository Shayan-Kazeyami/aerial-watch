import assert from 'node:assert/strict';import fs from 'node:fs';import {webcrypto} from 'node:crypto';import{pendingStreamFixture}from './pending-stream.mjs';
import{fetchProgressiveNormal as baseline}from './baseline.mjs';import{fetchProgressiveNormal as candidate}from './candidate.mjs';
globalThis.location={href:'http://127.0.0.1:8765/'};
const low=new Uint8Array(fs.readFileSync(new URL('./fixtures/normal-2048-existing-mips.ktx2',import.meta.url)));
for(const[name,load]of[['baseline',baseline],['candidate',candidate]]){
 const f=pendingStreamFixture(),c=new AbortController();let metrics=false,calls=0;
 const job=load({low,cryptoImpl:webcrypto,baseURL:location.href,signal:c.signal,fetchImpl:async()=>{calls++;return new Response(f.stream,{status:206,headers:{'Content-Range':'bytes 4389496-8388607/8388608'}})},onMetrics(){metrics=true}});
 await f.pendingRead;assert.equal(f.state.acquired,1);assert.equal(f.state.readCalls,1);assert(f.state.pending&&f.stream.locked);c.abort(new Error('synthetic QA cancellation'));await assert.rejects(job,/synthetic QA cancellation/);assert(f.state.cancelled);assert.equal(f.state.released,1);assert(!f.stream.locked);assert.equal(calls,1);assert(!metrics);console.log(name+' pending native reader abort/release PASS');
}

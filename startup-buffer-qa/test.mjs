import assert from 'node:assert/strict';
import {gzipSync,gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createByteCollector} from './assembly-byte-collector.js';
import {loadGLTFAsset} from './assembly-loading.js';
import {decompressGzipAsset} from './assembly-optimized-loading.js';
const data=Uint8Array.from({length:1024*1024},(_,i)=>(i*13)%251);
for(const hint of [data.length,0,19,data.length*2,2**40,NaN,-1]){
 const sink=createByteCollector(hint);for(let i=0;i<data.length;i+=65536)sink.append(data.subarray(i,i+65536));const result=sink.finish();assert.deepEqual(new Uint8Array(result.buffer),data);
 if(hint===data.length){assert.equal(result.metrics.peakOwnedBytes,data.length+65536);assert.equal(result.metrics.avoidedFinalCopy,true);}
}
let progress=[],parsed=0;
const loader={parseAsync:async b=>{parsed++;assert.deepEqual(new Uint8Array(b),data);return {ok:true};}};
for(const [length,encoding] of [[data.length,null],[0,null],[9,null],[data.length*2,null],[50,'gzip']]){
 const headers={};if(length)headers['content-length']=String(length);if(encoding)headers['content-encoding']=encoding;
 const fetcher=async()=>new Response(new ReadableStream({start(c){for(let i=0;i<data.length;i+=65536)c.enqueue(data.slice(i,i+65536));c.close();}}),{headers});
 const r=await loadGLTFAsset('fixture.glb',{loader,fetcher,baseURL:'https://example.test/',onProgress:p=>progress.push(p.loaded)});assert.equal(r.metrics.bodyBytes,data.length);if(length===data.length&&!encoding)assert(r.metrics.buffering.avoidedFinalCopy);
}
assert.equal(parsed,5);assert(progress.length>0);
const gz=gzipSync(data);let metrics;const decoded=await decompressGzipAsset(gz,{expectedBytes:data.length,onBuffering:m=>metrics=m});assert.deepEqual(new Uint8Array(decoded),data);assert(metrics.avoidedFinalCopy);
await assert.rejects(decompressGzipAsset(gz,{expectedBytes:data.length-1}),/exceeds/);
await assert.rejects(decompressGzipAsset(gz,{expectedBytes:data.length+1}),/does not match/);
await assert.rejects(decompressGzipAsset(Uint8Array.of(1,2,3),{expectedBytes:10}));
const abort=new AbortController();abort.abort();await assert.rejects(decompressGzipAsset(gz,{signal:abort.signal}),{name:'AbortError'});
const fixture=process.argv[2];if(fixture){const compressed=readFileSync(fixture),expected=gunzipSync(compressed);let measured;const out=await decompressGzipAsset(compressed,{expectedBytes:expected.length,onBuffering:m=>measured=m});assert.equal(createHash('sha256').update(new Uint8Array(out)).digest('hex'),createHash('sha256').update(expected).digest('hex'));console.log('REAL_ASSET',JSON.stringify({...measured,baselineOwnedBytePeak:expected.length*2,savedStagingBytes:expected.length*2-measured.peakOwnedBytes}));}
console.log('PASS known/unknown/mismatched/encoded response sizes, bounded allocation, identical bytes, progress, gzip corrupt/overflow/underflow/abort');
let cancelled=false,attempted=false;const controller=new AbortController();
await assert.rejects(loadGLTFAsset('abort.glb',{baseURL:'https://example.test/',signal:controller.signal,loader:{parseAsync:async()=>{attempted=true;}},fetcher:async()=>new Response(new ReadableStream({pull(c){c.enqueue(Uint8Array.of(1));},cancel(){cancelled=true;}}),{headers:{'content-length':'100'}}),onProgress(){controller.abort();}}),{name:'AbortError'});
assert(cancelled&&!attempted);console.log('PASS mid-stream abort cancels reader without parsing');

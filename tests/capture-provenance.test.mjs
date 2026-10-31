import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const source=await readFile(new URL('../assembly-capture-provenance.js',import.meta.url),'utf8');
const {createCaptureProvenance}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const hash=value=>createHash('sha256').update(value).digest('hex');
const bytes=Buffer.from('viewer source');
const files=[{path:'viewer.js',bytes:bytes.length,sha256:hash(bytes)}];
const revision={schemaVersion:1,algorithm:'SHA-256',scope:'Test viewer',files,digest:hash(JSON.stringify(files))};
const base={loadBootRevision:async()=>revision,timeoutMs:25};
const goodFetch=async url=>url.endsWith('.json')?Response.json(revision):new Response(bytes);

test('successful source verification is shared by concurrent export requests',async()=>{
 let calls=0;const provenance=createCaptureProvenance({...base,timeoutMs:1000,fetcher:async url=>{calls++;return goodFetch(url);}});
 const first=provenance.resolve();assert.equal(provenance.resolve(),first);
 assert.equal((await first).status,'verified');assert.equal(calls,2);
});
test('stalled metadata stops blocking exports and verification can be retried',async()=>{
 let stalled=true,requestSignal;
 const provenance=createCaptureProvenance({...base,fetcher:(url,{signal})=>{requestSignal=signal;return stalled?new Promise(()=>{}):goodFetch(url);}});
 const result=await provenance.resolve();assert.equal(result.status,'unavailable');assert.match(result.reason,/timed out/);assert.equal(requestSignal.aborted,true);
 stalled=false;assert.equal((await provenance.resolve()).status,'verified');
});
test('a stalled asset response body times out and aborts its request',async()=>{
 let requestSignal;const provenance=createCaptureProvenance({...base,fetcher:async(url,{signal})=>{
  if(url.endsWith('.json'))return Response.json(revision);
  requestSignal=signal;return {ok:true,arrayBuffer:()=>new Promise(()=>{})};
 }});
 assert.equal((await provenance.resolve()).status,'unavailable');assert.equal(requestSignal.aborted,true);
});
test('viewer departure cancels verification even while boot metadata is stalled',async()=>{
 const controller=new AbortController();const provenance=createCaptureProvenance({...base,timeoutMs:1000,signal:controller.signal,loadBootRevision:()=>new Promise(()=>{}),fetcher:()=>assert.fail('must not fetch')});
 const pending=provenance.resolve();controller.abort(new Error('Viewer closed'));
 const result=await pending;assert.equal(result.status,'unavailable');assert.match(result.reason,/Viewer closed/);
});
test('stalled boot metadata cannot block an export indefinitely',async()=>{
 const provenance=createCaptureProvenance({...base,loadBootRevision:()=>new Promise(()=>{}),fetcher:()=>assert.fail('must not fetch')});
 const result=await provenance.resolve();assert.equal(result.status,'unavailable');assert.match(result.reason,/timed out/);
});
test('late metadata cannot overwrite timeout state or start asset requests',async()=>{
 let finish,calls=0;const provenance=createCaptureProvenance({...base,fetcher:()=>{calls++;return new Promise(resolve=>{finish=resolve;});}});
 await provenance.resolve();finish(Response.json(revision));await new Promise(resolve=>setTimeout(resolve,10));
 assert.equal(provenance.snapshot().status,'unavailable');assert.equal(calls,1);
});

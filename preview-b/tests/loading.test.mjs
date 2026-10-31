import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../assembly-loading.js',import.meta.url),'utf8');
const {loadGLTFAsset,loadJSONAsset,loadProgressiveAssembly}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const options={baseURL:'https://example.test/',fetcher:async()=>new Response(new Uint8Array([1,2,3])),loader:{parseAsync:async()=>({scene:true})}};
test('successful model transfer and parse',async()=>{const result=await loadGLTFAsset('watch.glb',options);assert.equal(result.metrics.bodyBytes,3);assert.deepEqual(result.gltf,{scene:true});});
test('HTTP failures remain actionable',async()=>{await assert.rejects(loadGLTFAsset('watch.glb',{...options,fetcher:async()=>new Response(null,{status:404})}),/404/);});
test('stalled transfer times out and aborts underlying work',async()=>{let requestSignal;await assert.rejects(loadGLTFAsset('watch.glb',{...options,timeoutMs:20,fetcher:(_url,{signal})=>{requestSignal=signal;return new Promise(()=>{});}}),{name:'TimeoutError'});assert.equal(requestSignal.aborted,true);});
test('caller cancellation rejects even if transport ignores abort',async()=>{const controller=new AbortController();const pending=loadGLTFAsset('watch.glb',{...options,signal:controller.signal,fetcher:()=>new Promise(()=>{})});controller.abort();await assert.rejects(pending,{name:'AbortError'});});
test('late parsed resources are disposed after timeout',async()=>{let finish,disposed=0;const pending=loadGLTFAsset('watch.glb',{...options,timeoutMs:20,loader:{parseAsync:()=>new Promise(resolve=>{finish=resolve;})},disposeUnused:()=>disposed++});await assert.rejects(pending,{name:'TimeoutError'});finish({scene:true});await new Promise(resolve=>setImmediate(resolve));assert.equal(disposed,1);});
test('optional proposal failure preserves baseline',async()=>{let baselineShown=false,warned=false;const result=await loadProgressiveAssembly({loadBaseline:async()=>({}),loadMetadata:async()=>({}),loadProposal:async()=>{throw new Error('optional unavailable');},onBaseline:()=>{baselineShown=true;},onProposal:()=>assert.fail(),onWarning:()=>{warned=true;}});assert.deepEqual(result,{baseline:true,proposal:false});assert.ok(baselineShown&&warned);});

test('metadata succeeds and preserves JSON value',async()=>{assert.deepEqual(await loadJSONAsset('parts.json',{fetcher:async()=>Response.json({parts:[1]})}),{parts:[1]});});
test('metadata HTTP and malformed JSON failures propagate',async()=>{await assert.rejects(loadJSONAsset('parts.json',{fetcher:async()=>new Response(null,{status:503})}),/503/);await assert.rejects(loadJSONAsset('parts.json',{fetcher:async()=>new Response('{bad')}),SyntaxError);});
test('metadata stalled response body times out',async()=>{let signal;await assert.rejects(loadJSONAsset('parts.json',{timeoutMs:20,fetcher:async(_url,options)=>{signal=options.signal;return {ok:true,json:()=>new Promise(()=>{})};}}),{name:'TimeoutError'});assert.ok(signal.aborted);});
test('metadata honors pre-existing cancellation without fetching',async()=>{const controller=new AbortController();controller.abort();await assert.rejects(loadJSONAsset('parts.json',{signal:controller.signal,fetcher:()=>assert.fail('must not fetch')}),{name:'AbortError'});});
test('metadata timeout disposes a completed baseline and optional proposal',async()=>{const disposed=[];await assert.rejects(loadProgressiveAssembly({loadBaseline:async()=>({id:'baseline'}),loadMetadata:()=>loadJSONAsset('parts.json',{timeoutMs:20,fetcher:()=>new Promise(()=>{})}),loadProposal:async()=>({id:'proposal'}),onBaseline:()=>assert.fail('must not initialize without metadata'),disposeUnused:value=>disposed.push(value.id)}),{name:'TimeoutError'});await new Promise(resolve=>setImmediate(resolve));assert.deepEqual(disposed.sort(),['baseline','proposal']);});

test('timeout cancels a stalled response stream and releases its reader',async()=>{
  let cancelled=0;
  const body=new ReadableStream({cancel(){cancelled++;}});
  await assert.rejects(loadGLTFAsset('watch.glb',{...options,timeoutMs:20,fetcher:async()=>new Response(body)}),{name:'TimeoutError'});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(cancelled,1);
  assert.equal(body.locked,false);
});
test('progress callback failure cancels the unfinished response stream',async()=>{
  let cancelled=0;
  const body=new ReadableStream({start(controller){controller.enqueue(new Uint8Array([1]));},cancel(){cancelled++;}});
  await assert.rejects(loadGLTFAsset('watch.glb',{...options,fetcher:async()=>new Response(body),onProgress:()=>{throw new Error('progress failed');}}),/progress failed/);
  assert.equal(cancelled,1);
  assert.equal(body.locked,false);
});

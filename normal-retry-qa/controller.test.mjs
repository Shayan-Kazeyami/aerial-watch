import test from 'node:test';
import assert from 'node:assert/strict';
import {createProgressiveUpgrade} from './assembly-progressive-upgrade-controller.js';
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const tick=()=>new Promise(r=>setImmediate(r));
function fixture(options={}){const low=new Uint8Array([1,2,3]),errors=[],textures=[],seen=[];let adopted=0;
 const c=createProgressiveUpgrade({lowBytes:low,fetchFull:async({low,signal})=>{seen.push(low);signal.throwIfAborted();return low;},decodeFull:async()=>{const t={disposed:0,dispose(){this.disposed++;}};textures.push(t);return t;},adopt:()=>{adopted++;},onError:e=>errors.push(e),...options});
 return {c,low,errors,textures,seen,get adopted(){return adopted;}};}
test('initial start once; early retry forbidden; full releases low and cannot retry',async()=>{
 const f=fixture();assert.equal(f.c.retry(),null);assert.equal(f.c.snapshot().retainedLowBytes,3);
 const p=f.c.afterFirstSelectedFrame();assert.equal(f.c.afterFirstSelectedFrame(),null);assert.equal(await p,true);
 assert.deepEqual(f.c.snapshot(),{state:'full',attempts:1,inFlight:false,retainedLowBytes:0});assert.equal(f.c.retry(),null);assert.equal(f.adopted,1);
});
for(const phase of ['fetch','decode','adopt'])test(`${phase} failure retains low; explicit retry succeeds`,async()=>{
 let attempts=0;const failedTexture={disposed:0,dispose(){this.disposed++;}};
 const overrides=phase==='fetch'?{fetchFull:async({low})=>{if(!attempts++)throw Error('fetch failed');return low;}}:phase==='decode'?{decodeFull:async()=>{if(!attempts++)throw Error('decode failed');return {dispose(){}};}}:{decodeFull:async()=>failedTexture,adopt:()=>{if(!attempts++)throw Error('adopt failed');}};
 const f=fixture(overrides);assert.equal(await f.c.afterFirstSelectedFrame(),false);assert.equal(f.errors.length,1);assert.equal(f.c.snapshot().state,'failed');assert.equal(f.c.snapshot().retainedLowBytes,3);
 await tick();assert.equal(f.c.snapshot().attempts,1);assert.equal(f.c.afterFirstSelectedFrame(),null);
 assert.equal(await f.c.retry(),true);assert.equal(f.c.snapshot().attempts,2);assert.equal(f.c.snapshot().retainedLowBytes,0);
 if(phase==='adopt')assert.equal(failedTexture.disposed,1);
});
test('duplicate retry while pending returns identical promise without abort',async()=>{
 let count=0,signal;const gate=deferred();const f=fixture({fetchFull:async args=>{signal=args.signal;if(!count++)throw Error('first');await gate.promise;return args.low;}});
 await f.c.afterFirstSelectedFrame();const p=f.c.retry();await tick();assert.equal(f.c.retry(),p);assert.equal(signal.aborted,false);assert.equal(f.c.snapshot().attempts,2);gate.resolve();assert.equal(await p,true);
});
test('retry during initial pending coalesces and does not cancel',async()=>{
 const gate=deferred();const f=fixture({fetchFull:async({low})=>{await gate.promise;return low;}});const p=f.c.afterFirstSelectedFrame();assert.equal(f.c.retry(),p);gate.resolve();assert.equal(await p,true);assert.equal(f.c.snapshot().attempts,1);
});
test('repeated explicit failures do not auto-retry',async()=>{
 const f=fixture({fetchFull:async()=>{throw Error('offline');}});await f.c.afterFirstSelectedFrame();await f.c.retry();await tick();assert.equal(f.c.snapshot().attempts,2);assert.equal(f.c.snapshot().state,'failed');assert.equal(f.c.snapshot().retainedLowBytes,3);f.c.dispose();assert.equal(f.c.snapshot().retainedLowBytes,0);
});
test('dispose before start releases low, prevents fetch and retry',()=>{const f=fixture();f.c.dispose();f.c.dispose();assert.equal(f.c.afterFirstSelectedFrame(),null);assert.equal(f.c.retry(),null);assert.deepEqual(f.c.snapshot(),{state:'disposed',attempts:0,inFlight:false,retainedLowBytes:0});});
test('dispose during fetch aborts and forbids late decode/adoption',async()=>{
 const gate=deferred();let signal,decoded=0;const f=fixture({fetchFull:async args=>{signal=args.signal;await gate.promise;return args.low;},decodeFull:async()=>{decoded++;return {dispose(){}};}});
 const p=f.c.afterFirstSelectedFrame();await tick();f.c.dispose();assert.equal(signal.aborted,true);assert.equal(await p,false);gate.resolve();await tick();assert.equal(decoded,0);assert.equal(f.c.snapshot().retainedLowBytes,0);assert.equal(f.errors.length,0);
});
test('dispose during decode disposes late texture once, no adoption',async()=>{
 const gate=deferred(),texture={disposed:0,dispose(){this.disposed++;}};const f=fixture({decodeFull:async()=>{await gate.promise;return texture;}});
 const p=f.c.afterFirstSelectedFrame();await tick();f.c.dispose();assert.equal(await p,false);gate.resolve();await tick();assert.equal(texture.disposed,1);assert.equal(f.adopted,0);assert.equal(f.c.retry(),null);
});
test('dispose after full does not dispose caller-owned adopted texture',async()=>{const f=fixture();await f.c.afterFirstSelectedFrame();f.c.dispose();assert.equal(f.textures[0].disposed,0);assert.equal(f.c.snapshot().retainedLowBytes,0);});
test('invalid low buffer rejected',()=>assert.throws(()=>createProgressiveUpgrade({lowBytes:null}),TypeError));
test('retry reuses the same verified low reference, then releases controller reference',async()=>{let count=0;const seen=[];const f=fixture({fetchFull:async({low})=>{seen.push(low);if(!count++)throw Error('network');return low;}});await f.c.afterFirstSelectedFrame();await f.c.retry();assert.equal(seen[0],f.low);assert.equal(seen[1],f.low);assert.equal(f.c.snapshot().retainedLowBytes,0);});
test('disposal during a retry aborts the retry without another error or attempt',async()=>{let count=0,signal;const gate=deferred();const f=fixture({fetchFull:async args=>{if(!count++)throw Error('initial');signal=args.signal;await gate.promise;return args.low;}});await f.c.afterFirstSelectedFrame();const p=f.c.retry();await tick();f.c.dispose();assert.equal(await p,false);assert.equal(signal.aborted,true);gate.resolve();await tick();assert.equal(f.errors.length,1);assert.equal(f.adopted,0);assert.equal(f.c.snapshot().attempts,2);assert.equal(f.c.snapshot().retainedLowBytes,0);});

import assert from 'node:assert/strict';
import {createPreparedAsset as before} from './assembly-prepared-asset-before.js';
import {createPreparedAsset as after} from './assembly-prepared-asset.js';
const turn=()=>new Promise(r=>setTimeout(r,0));
const keep=[];
async function adoptedWeak(factory){const prepared=factory({load:async()=>({payload:new ArrayBuffer(32*1024*1024)})});keep.push(prepared);let asset=await prepared.take();const weak=new WeakRef(asset);asset=null;return weak;}
const old=await adoptedWeak(before),fixed=await adoptedWeak(after);
for(let i=0;i<10;i++){await turn();global.gc();await turn();}
assert(old.deref(),'Baseline should retain resolved asset');assert.equal(fixed.deref(),undefined,'Adopted result should not be retained by preparation helper');
let disposeCount=0;const late=after({load:async()=>{await turn();return{};},dispose:()=>disposeCount++});late.dispose();await assert.rejects(late.take(),{name:'AbortError'});await turn();assert(disposeCount<=1);
const failure=new Error('fixture');await assert.rejects(after({load:async()=>{throw failure;}}).take(),e=>e===failure);
const normal=after({load:async()=>({ok:true})});assert((await normal.take()).ok);await assert.rejects(normal.take(),/already adopted/);normal.dispose();
console.log('PASS: baseline retains32MiB fixture after adoption; candidate releases it with helper still alive. Error identity, double take and cancellation preserved. Not total browser memory.');
let resolveLate,releaseCount=0;const pending=after({load:()=>new Promise(r=>resolveLate=r),dispose:()=>releaseCount++});await turn();pending.dispose();pending.dispose();resolveLate({});await assert.rejects(pending.take(),{name:'AbortError'});assert.equal(releaseCount,1);
let abandonCount=0;const unadopted=after({load:async()=>({}),dispose:()=>abandonCount++});await turn();unadopted.dispose();unadopted.dispose();assert.equal(abandonCount,1);console.log('PASS late and ready-unadopted resources disposed exactly once');

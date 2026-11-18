import assert from 'node:assert/strict';
import {createOfflineVideoExport} from './assembly-offline-video.js';
import {createReadbackVideoFrame} from './assembly-video-frame.js';
let refs=[],frames=0,closed=0,mode='success',endCount=0,renderCount=0,flushResolve;
class Frame{constructor(pixels,meta){refs.push(new WeakRef(pixels));this.timestamp=meta.timestamp;this.duration=meta.duration;frames++;}close(){closed++;}}
class Encoder{static async isConfigSupported(c){return {supported:true,config:c}} constructor(h){this.h=h;this.state='configured';this.encodeQueueSize=0;}configure(){} encode(f){this.encodeQueueSize++;if(mode==='reject')throw Error('encoder rejection');this.h.output({type:'key',timestamp:f.timestamp,duration:f.duration,byteLength:4,copyTo:a=>a.set([1,2,3,4])});}async flush(){if(mode==='pending')await new Promise(r=>flushResolve=r);this.encodeQueueSize=0;}close(){this.state='closed';}}
global.VideoFrame=Frame;global.VideoEncoder=Encoder;
class Element{constructor(){this.children=new Map();this.open=false;this.disabled=false;}querySelector(k){if(!this.children.has(k))this.children.set(k,new Element());return this.children.get(k);}setAttribute(){}removeAttribute(){}addEventListener(){}removeEventListener(){}append(){}remove(){}focus(){}showModal(){this.open=true;}close(){this.open=false;}}
const doc={head:new Element(),body:new Element(),createElement:()=>new Element(),addEventListener(){},removeEventListener(){}};const win={addEventListener(){},removeEventListener(){}};
const canvas={width:3840,height:1638};const gl={FRAMEBUFFER_BINDING:1,RGBA:2,UNSIGNED_BYTE:3,getParameter:()=>null,readPixels:()=>{},isContextLost:()=>false};
const collect=async()=>{await new Promise(r=>setImmediate(r));global.gc();await new Promise(r=>setImmediate(r));};
let exporter=createOfflineVideoExport({canvas,gl,doc,win,begin:()=>({}),renderFrame:()=>{renderCount++;},end:()=>endCount++,onProgress:p=>{if(p.completed===1){assert.ok(refs.at(-1).deref(),'scratch freed during active export');if(mode==='abort')exporter.cancel();if(mode==='dispose')exporter.dispose();}}});
const results=[];
for(const scenario of ['success','success','abort','reject','success']){mode=scenario;refs=[];let error=null;try{await exporter.start({durationMs:100,frameRate:30,size:'compact'});}catch(e){error=e.name+':'+e.message;}await collect();assert.equal(refs.filter(r=>r.deref()).length,0,scenario+' retained pixels');assert.equal(exporter.active,false);assert.equal(exporter.progress,null);if(scenario==='success')assert.equal(error,null);else assert.ok(error);results.push({scenario,error,retainedScratchBytes:0});}
assert.equal(frames,closed);assert.equal(endCount,5);
// Explicit release after a live readback must not dispose the reusable producer.
refs=[];const snapshot=createReadbackVideoFrame({canvas,gl,Frame});snapshot({timestamp:0}).close();snapshot.release();snapshot.release();await collect();assert.equal(refs[0].deref(),undefined);snapshot({timestamp:1}).close();snapshot.release();await collect();assert.equal(refs[1].deref(),undefined);
// Genuinely pending flush: scratch survives async GC until cancellation settles.
mode='pending';refs=[];const active=exporter.start({durationMs:500,frameRate:30,size:'compact'});
while(!flushResolve)await new Promise(r=>setImmediate(r));
await collect();assert.ok(refs.at(-1).deref(),'in-flight scratch prematurely freed');
exporter.dispose();await assert.rejects(active,/cancelled/);flushResolve();await collect();assert.equal(exporter.active,false);assert.equal(refs.filter(r=>r.deref()).length,0);
// 2D fallback backing canvas must be released; source untouched; reusable pixels exact.
let canvases=[],observed=[];
const fallbackDoc={createElement:()=>{const c={width:0,height:0,getContext:()=>({drawImage(){},getImageData:()=>({data:new Uint8ClampedArray([1,2,3,4,5,6,7,8])})})};canvases.push(c);return c;}};
class PixelFrame{constructor(p){observed.push([...p]);}close(){}}
const source={width:2,height:1};const fallback=createReadbackVideoFrame({canvas:source,doc:fallbackDoc,Frame:PixelFrame});
fallback({}).close();fallback.release();fallback.release();assert.deepEqual([canvases[0].width,canvases[0].height],[0,0]);fallback({}).close();fallback.release();assert.deepEqual(observed,[[1,2,3,4,5,6,7,8],[1,2,3,4,5,6,7,8]]);assert.deepEqual(source,{width:2,height:1});assert.equal(frames,closed);
console.log(JSON.stringify({passed:true,results,frames,closed,endCount,pendingFlush:true,fallback2d:true,scope:'actual current exporter/lifecycle with mocked DOM, GL, WebCodecs; actual JS allocation and GC, no GPU or phone claim'},null,2));

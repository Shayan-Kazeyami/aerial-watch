import test from 'node:test';
import assert from 'node:assert/strict';
import {createFrameVideoExporter} from '../assembly-video-export.js';
function setup(options={}){
 const frames=[],encoded=[],instances=[],renders=[],progress=[],end=[];
 let support=true,drop=false;
 class Frame{constructor(canvas,init){this.canvas=canvas;this.init=init;this.closed=false;frames.push(this);}close(){this.closed=true;}}
 class Encoder{static async isConfigSupported(config){return {supported:support,config};}constructor(callbacks){this.callbacks=callbacks;this.state='unconfigured';this.encodeQueueSize=0;instances.push(this);}configure(config){this.config=config;this.state='configured';}encode(frame,{keyFrame}){encoded.push(frame.init);if(!drop)this.callbacks.output({type:keyFrame?'key':'delta',timestamp:frame.init.timestamp,duration:frame.init.duration,byteLength:2,copyTo(dest){dest.set([12,34]);}});}async flush(){}close(){this.state='closed';}}
 const canvas={width:320,height:180};const exporter=createFrameVideoExporter({canvas,Encoder,Frame,begin:()=>({saved:'pose'}),renderFrame:(t,detail)=>renders.push({t,...detail}),end:context=>end.push(context),onProgress:value=>progress.push(value),yieldTask:async()=>{},mux:opts=>{assert.equal(opts.chunks.length,opts.expectedFrames);return new Uint8Array([1,2,3]);},...options});
 return {exporter,canvas,frames,encoded,instances,renders,progress,end,setSupported:v=>support=v,setDrop:v=>drop=v};
}
test('offline export samples every frame at deterministic time and restores state once',async()=>{
 const h=setup();const r=await h.exporter.start({durationMs:1000,frameRate:30});assert.equal(r.frameCount,30);assert.equal(r.durationMs,1000);assert.equal(r.blob.type,'video/webm');assert.equal(r.blob.size,3);
 assert.deepEqual(h.renders.map(x=>x.t),Array.from({length:30},(_,i)=>i/30));assert.equal(h.encoded.at(-1).timestamp+h.encoded.at(-1).duration,1000000);
 assert(h.frames.every(f=>f.closed));assert.equal(h.instances[0].state,'closed');assert.deepEqual(h.end,[{saved:'pose'}]);assert.equal(h.exporter.active,false);
});
test('a slow render does not alter encoded sample times',async()=>{
 const h=setup({renderFrame:()=>{const stop=Date.now()+5;while(Date.now()<stop){}}});await h.exporter.start({durationMs:100,frameRate:30});assert.deepEqual(h.encoded.map(x=>x.timestamp),[0,33333,66667]);
});
test('cancel while rendering restores, closes and permits a new export',async()=>{
 let count=0;const h=setup({renderFrame:()=>{if(++count===2)h.exporter.cancel();}});await assert.rejects(h.exporter.start({durationMs:1000}),{name:'AbortError'});assert.equal(h.frames.length,1);assert.equal(h.end.length,1);assert.equal(h.instances[0].state,'closed');assert.equal(h.exporter.active,false);
 await h.exporter.start({durationMs:100});assert.equal(h.end.length,2);
});
test('duplicates are rejected and disposal permanently closes exporter',async()=>{
 let release;const h=setup({yieldTask:()=>new Promise(resolve=>{release=resolve;})});const task=h.exporter.start({durationMs:100});await new Promise(r=>setTimeout(r,0));await assert.rejects(h.exporter.start(),/already rendering/);h.exporter.dispose();await assert.rejects(task,{name:'AbortError'});release?.();await assert.rejects(h.exporter.start(),/has closed/);assert.equal(h.end.length,1);
});
test('resize aborts instead of mixing dimensions',async()=>{
 const h=setup({yieldTask:async()=>{h.canvas.width=100;}});await assert.rejects(h.exporter.start({durationMs:100}),/changed size/);assert.equal(h.end.length,1);assert(h.frames.every(f=>f.closed));
});
test('frame creation or encode failure still restores',async()=>{
 class BadFrame{constructor(){throw Error('frame allocation failed');}}
 const h=setup({Frame:BadFrame});await assert.rejects(h.exporter.start(),/allocation/);assert.equal(h.end.length,1);assert.equal(h.instances[0].state,'closed');
});
test('encoder output count must match requested samples',async()=>{
 const h=setup();h.setDrop(true);await assert.rejects(h.exporter.start({durationMs:100}),/0 of 3 frames/);assert.equal(h.end.length,1);
});
test('memory is bounded and failure retains no active session',async()=>{
 const h=setup({maxOutputBytes:3});await assert.rejects(h.exporter.start({durationMs:100}),/memory limit/);assert.equal(h.exporter.active,false);assert.equal(h.end.length,1);
});
test('unsupported encoders leave scene untouched',async()=>{
 const h=setup();h.setSupported(false);await assert.rejects(h.exporter.start(),/cannot encode/);assert.equal(h.renders.length,0);assert.equal(h.end.length,0);assert.equal(h.exporter.active,false);
});
test('UI scheduling timeout is bounded',async()=>{
 const h=setup({timeoutMs:10,yieldTask:()=>new Promise(()=>{})});await assert.rejects(h.exporter.start(),/Video render scheduling timed out/);assert.equal(h.end.length,1);assert.equal(h.exporter.active,false);
});
test('invalid dimensions, duration and frame rate fail before scene begins',async()=>{
 for(const opts of [{durationMs:0},{frameRate:0},{durationMs:31000},{frameRate:61}]){const h=setup();await assert.rejects(h.exporter.start(opts));assert.equal(h.end.length,0);}
 const h=setup();h.canvas.width=0;await assert.rejects(h.exporter.start(),/dimensions/);assert.equal(h.end.length,0);
});

test('async scene hooks are rejected before scene work begins',async()=>{
 for(const name of ['begin','renderFrame','end']){const h=setup({[name]:async()=>{}});await assert.rejects(h.exporter.start(),/must be synchronous/);assert.equal(h.renders.length,0);assert.equal(h.end.length,0);}
});
test('late old encoder callbacks cannot affect a replacement export',async()=>{
 let release;const h=setup();await h.exporter.start({durationMs:100});const old=h.instances[0];
 const next=h.exporter.start({durationMs:100});old.callbacks.error(Error('stale failure'));old.callbacks.output({byteLength:999999999});await next;assert.equal(h.end.length,2);
});
test('encoder flush timeout restores scene and releases owned resources',async()=>{
 class Encoder{static async isConfigSupported(config){return {supported:true,config};}constructor(){this.state='configured';this.encodeQueueSize=4;}configure(){}encode(){}flush(){return new Promise(()=>{});}close(){this.state='closed';}}
 const h=setup({Encoder,timeoutMs:10});await assert.rejects(h.exporter.start({durationMs:100}),/Video encoding timed out/);assert.equal(h.end.length,1);assert.equal(h.exporter.active,false);assert(h.frames.every(f=>f.closed));
});

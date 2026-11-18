import assert from 'node:assert/strict';
import test from 'node:test';
import {createFrameVideoExporter,videoExportSizes} from './runtime/assembly-video-export.js';

test('viewport stays byte-for-byte in dimensions; compact never crops/upscales',()=>{
 assert.deepEqual(videoExportSizes(361,253),{view:{width:361,height:253},compact:{width:270,height:188}});
 assert.deepEqual(videoExportSizes(932,430).compact,{width:540,height:248});
 assert.deepEqual(videoExportSizes(430,932).compact,{width:248,height:540});
 assert.equal(videoExportSizes(2,2).compact,null);
 for(const [w,h] of [[7000,7000],[0,400],[300,NaN],[-1,30]]) assert.throws(()=>videoExportSizes(w,h),RangeError);
 for(const [w,h] of [[400,845],[832,540],[390,844],[1080,1920],[1920,1080],[270,360]]){
  const {compact:c}=videoExportSizes(w,h);
  assert(c.width<w&&c.height<h&&Math.max(c.width,c.height)<=540);
  const s=Math.min(.75,540/Math.max(w,h));
  assert(w*s-c.width<2&&h*s-c.height<2);
 }
});

function fixture({stall=false,unsupported=false}={}){
 const canvas={width:361,height:253};const events=[];
 class Encoder {
  static async isConfigSupported(config){events.push(['support',config]);return{supported:!unsupported,config}}
  constructor({output}){this.output=output;this.state='configured';this.encodeQueueSize=0}
  configure(config){events.push(['configure',config]);}
  encode(frame){events.push(['input',frame.width,frame.height]);this.output({type:'key',timestamp:frame.meta.timestamp,duration:frame.meta.duration,byteLength:1,copyTo:b=>b[0]=1})}
  flush(){events.push(['flush']);return stall?new Promise(()=>{}):Promise.resolve()}
  close(){this.state='closed';events.push(['close'])}
 }
 let ended,started;
 const engine=createFrameVideoExporter({canvas,Encoder,Frame:class {},
  createFrame:(source,meta)=>({width:source.width,height:source.height,meta,close(){events.push(['frame.close'])}}),
  begin:x=>{started=x;return{saved:true}},renderFrame:(sec,x)=>events.push(['render',sec,x.index]),end:x=>{ended=x},
  onProgress:x=>events.push(['progress',x]),yieldTask:()=>Promise.resolve(),
  mux:x=>{events.push(['mux',x]);return new Uint8Array([0x1a,0x45,0xdf,0xa3]);}});
 return{engine,canvas,events,get ended(){return ended;},get started(){return started;}};
}
for(const size of ['view','compact'])test(`real settings cross all relevant code paths: ${size}`,async()=>{
 const f=fixture();const r=await f.engine.start({durationMs:100,size});
 const dims=videoExportSizes(361,253)[size];
 assert.equal(r.width,dims.width);assert.equal(r.height,dims.height);
 const c=f.events.find(([m])=>m==='configure')[1];assert.equal(c.width,r.width);assert.equal(c.height,r.height);
 assert(size==='view'?c.bitrate===8000000:c.bitrate<8000000);
 assert.deepEqual(f.events.filter(([m])=>m==='input'),Array(3).fill(['input',361,253]));
 assert.equal(f.events.filter(([m])=>m==='frame.close').length,3);
 assert.equal(f.started.width,r.width);assert.equal(f.started.height,r.height);
 assert.deepEqual(f.ended,{saved:true});
 const mux=f.events.find(([m])=>m==='mux')[1];assert.equal(mux.width,r.width);assert.equal(mux.height,r.height);assert.equal(mux.expectedFrames,3);
 assert.equal(f.engine.active,false);assert.deepEqual(f.canvas,{width:361,height:253});
});
test('unsupported, invalid, cancelled, and retried exports do not leak active state or resize the view',async()=>{
 const bad=fixture({unsupported:true}); await assert.rejects(bad.engine.start({size:'compact'}),/cannot encode/);assert.equal(bad.started,undefined);
 const x=fixture();await assert.rejects(x.engine.start({size:'__proto__'}),/resolution/);assert.equal(x.engine.active,false);
 const f=fixture({stall:true});const run=f.engine.start({size:'compact',durationMs:100});
 while(!f.events.some(([m])=>m==='flush'))await Promise.resolve();
 await assert.rejects(f.engine.start(),/already/);
 assert.equal(f.engine.cancel(),true);await assert.rejects(run,{name:'AbortError'});
 assert.equal(f.engine.active,false);assert.deepEqual(f.ended,{saved:true});assert(!f.events.some(([m])=>m==='mux'));assert.deepEqual(f.canvas,{width:361,height:253});
 const pending=f.engine.start({size:'view',durationMs:100});await Promise.resolve();assert.equal(f.engine.cancel(),true);await assert.rejects(pending,{name:'AbortError'});
});

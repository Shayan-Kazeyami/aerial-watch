import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source=await readFile(new URL('../assembly-recording.js',import.meta.url),'utf8');
const {createCanvasRecorder,inspectWebM}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));

function setup(options={}){
  const instances=[],statuses=[],timers=new Map();let stoppedTracks=0,nextTimer=0;
  class Recorder {
    static isTypeSupported(type){return type==='video/webm;codecs=vp8';}
    constructor(stream,{mimeType}){this.stream=stream;this.mimeType=mimeType;this.state='inactive';this.stops=0;instances.push(this);}
    start(){this.state='recording';}
    stop(){this.stops++;this.state='inactive';}
    data(value='video'){this.ondataavailable?.({data:new Blob([value])});}
    finish(){this.state='inactive';this.onstop?.();}
  }
  const recorder=createCanvasRecorder({
    canvas:{captureStream:()=>({getTracks:()=>[{stop(){stoppedTracks++;}}]})},
    MediaRecorderClass:Recorder,onStatus:(message,detail)=>statuses.push({message,...detail}),
    schedule:fn=>{timers.set(++nextTimer,fn);return nextTimer;},cancel:id=>timers.delete(id),...options,
  });
  return {recorder,instances,statuses,timers,get stoppedTracks(){return stoppedTracks;}};
}
function assertClean(harness,instance){
  assert.equal(harness.recorder.recording,false);
  assert.equal(harness.timers.size,0);
  assert.equal(instance.ondataavailable,null);
  assert.equal(instance.onerror,null);
  assert.equal(instance.onstop,null);
}

test('timed stop includes final data and releases recording resources',async()=>{
  let completed;const h=setup({onComplete:result=>{completed=result;}});
  const pending=h.recorder.start(),instance=h.instances[0];
  instance.data('first');[...h.timers.values()][0]();
  assert.equal(instance.stops,1);assert.equal(h.recorder.stop(),false);
  instance.data('last');instance.finish();
  const result=await pending;
  assert.equal(await result.blob.text(),'firstlast');assert.equal(result.mimeType,'video/webm;codecs=vp8');
  assert.equal(completed,result);assert.equal(h.statuses.at(-1).state,'complete');
  assert.equal(h.stoppedTracks,1);assertClean(h,instance);
});

test('completion callback failure reports an error and allows another recording',async()=>{
  const error=new Error('Could not export clip');let calls=0;
  const h=setup({onComplete:()=>{if(++calls===1)throw error;}});
  const pending=h.recorder.start(),first=h.instances[0];first.data();first.finish();
  await assert.rejects(pending,error);
  assert.equal(h.statuses.at(-1).state,'error');assert.equal(h.statuses.at(-1).error,error);
  assertClean(h,first);
  const retry=h.recorder.start(),second=h.instances[1];second.data();second.finish();await retry;
  assert.equal(h.statuses.at(-1).state,'complete');assert.equal(h.stoppedTracks,2);
});

test('browser recording errors reject once and discard late completion',async()=>{
  let completed=0;const h=setup({onComplete:()=>completed++});
  const pending=h.recorder.start(),instance=h.instances[0],lateStop=instance.onstop;
  const error=new Error('Encoder failed');instance.onerror({error});lateStop();
  await assert.rejects(pending,error);
  assert.equal(completed,0);assert.equal(instance.stops,1);assert.equal(h.stoppedTracks,1);
  assert.equal(h.statuses.at(-1).state,'error');assertClean(h,instance);
});

test('empty browser output rejects and releases the stream',async()=>{
  const h=setup(),pending=h.recorder.start(),instance=h.instances[0];instance.finish();
  await assert.rejects(pending,/empty clip/);
  assert.equal(h.statuses.at(-1).state,'error');assert.equal(h.stoppedTracks,1);assertClean(h,instance);
});

test('closing a pending recording cancels it once and suppresses late output',async()=>{
  let completed=0;const h=setup({onComplete:()=>completed++});
  const pending=h.recorder.start(),instance=h.instances[0],lateStop=instance.onstop;
  h.recorder.dispose();h.recorder.dispose();lateStop();
  await assert.rejects(pending,{name:'AbortError'});
  assert.equal(completed,0);assert.equal(instance.stops,1);assert.equal(h.stoppedTracks,1);
  assert.equal(h.statuses.at(-1).state,'disposed');assertClean(h,instance);
  assert.throws(()=>h.recorder.start(),/disposed/);
});

test('missing browser stop event times out, releases resources and permits retry',async()=>{
  const h=setup({finalizeTimeoutMs:5000});
  const pending=h.recorder.start(),first=h.instances[0];
  first.data();h.recorder.stop();
  // A broken encoder may become inactive without delivering its final event.
  const watchdog=[...h.timers.values()].at(-1);
  assert.ok(h.timers.size>=2,'stop must install a finalization watchdog');
  const rejected=assert.rejects(pending,/finish.*timed out/i);
  watchdog();await rejected;
  assertClean(h,first);assert.equal(h.stoppedTracks,1);
  const retry=h.recorder.start(),second=h.instances[1];second.data();second.finish();
  await retry;assertClean(h,second);
});

test('late completion and watchdog cannot affect a new recording after timeout',async()=>{
  let completions=0;const h=setup({onComplete:()=>completions++});
  const pending=h.recorder.start(),first=h.instances[0],lateStop=first.onstop;
  first.data();h.recorder.stop();const watchdog=[...h.timers.values()].at(-1);
  const rejected=assert.rejects(pending,/timed out/);watchdog();await rejected;
  const retry=h.recorder.start(),second=h.instances[1];
  lateStop();watchdog();
  assert.equal(h.recorder.recording,true);assert.equal(completions,0);
  second.data();second.finish();await retry;
  assert.equal(completions,1);assertClean(h,second);
});

test('closing during finalization clears the watchdog and cancels once',async()=>{
  const h=setup(),pending=h.recorder.start(),instance=h.instances[0];
  instance.data();h.recorder.stop();const watchdog=[...h.timers.values()].at(-1);
  const rejected=assert.rejects(pending,{name:'AbortError'});
  h.recorder.dispose();watchdog();await rejected;
  assert.equal(h.statuses.filter(s=>s.state==='disposed').length,1);
  assert.equal(h.stoppedTracks,1);assertClean(h,instance);
});

test('invalid finalization timeouts fail before capturing a stream',()=>{
  for(const finalizeTimeoutMs of [0,-1,NaN,Infinity]){
    const h=setup({finalizeTimeoutMs});
    assert.throws(()=>h.recorder.start(),/positive.*timeout/);
    assert.equal(h.instances.length,0);assert.equal(h.recorder.recording,false);
  }
});

// Minimal structural fixtures, deliberately not decodable video. Inspection
// measures container packets/timestamps; it must never claim decoder success.
function webm(times,{scale=1000000,unknownSegment=false,laced=false,blockGroup=false}={}){
  const element=(id,data)=>Buffer.concat([Buffer.from(id,'hex'),Buffer.from([0x20|(data.length>>16),(data.length>>8)&255,data.length&255]),data]);
  const uint=(id,n)=>element(id,Buffer.from([(n>>24)&255,(n>>16)&255,(n>>8)&255,n&255]));
  const tracks=element('1654ae6b',element('ae',Buffer.concat([uint('d7',1),uint('83',1)])));
  const info=element('1549a966',uint('2ad7b1',scale));
  const blocks=times.map(time=>{
    const data=Buffer.from([0x81,(time>>8)&255,time&255,laced?0x82:0x80,0x01]);
    return blockGroup?element('a0',element('a1',data)):element('a3',data);
  });
  const cluster=element('1f43b675',Buffer.concat([uint('e7',0),...blocks]));
  const contents=Buffer.concat([info,tracks,cluster]);
  const segment=unknownSegment?Buffer.concat([Buffer.from('18538067ff','hex'),contents]):element('18538067',contents);
  return new Blob([element('1a45dfa3',Buffer.alloc(0)),segment]);
}

test('WebM inspection measures packet timestamps, not requested or decoded FPS',async()=>{
  for(const options of [{},{unknownSegment:true},{blockGroup:true}]){
    assert.deepEqual(await inspectWebM(webm([0,4010],options)),{
      verified:true,encodedPacketCount:2,timestampSpanMs:4010,
    });
  }
  assert.equal((await inspectWebM(webm([-100,100],{scale:2000000}))).timestampSpanMs,400);
  assert.equal((await inspectWebM(webm([]))).encodedPacketCount,0);
});

test('unsupported, malformed, truncated and excessive WebM inputs are unverified',async()=>{
  const bytes=new Uint8Array(await webm([0,100]).arrayBuffer());
  for(const blob of [new Blob(['not a video']),new Blob([bytes.subarray(0,bytes.length-1)]),webm([0],{laced:true})]){
    assert.deepEqual(await inspectWebM(blob),{verified:false,encodedPacketCount:null,timestampSpanMs:null});
  }
  assert.equal((await inspectWebM({size:128*1024*1024+1,arrayBuffer(){throw Error('Must not allocate');}})).verified,false);
});

test('observed two-packet eight-second capture is rejected instead of downloaded',async()=>{
  let time=0,completed=0;const h=setup({now:()=>time,onComplete:()=>completed++});
  const pending=h.recorder.start(),instance=h.instances[0];
  instance.data(await webm([0,4010]).arrayBuffer());time=8000;h.recorder.stop();instance.finish();
  await assert.rejects(pending,error=>error.message.includes('too little motion')&&error.videoTiming.encodedPacketCount===2);
  assert.equal(completed,0);assertClean(h,instance);
});

test('healthy container exposes requested settings separately from measured timing',async()=>{
  let time=100;const h=setup({now:()=>time});
  const pending=h.recorder.start(),instance=h.instances[0];
  instance.data(await webm([0,2000,4000,6000,7900]).arrayBuffer());time=8100;h.recorder.stop();instance.finish();
  const result=await pending;
  assert.equal(result.requestedDurationMs,8000);assert.equal(result.requestedFrameRate,30);
  assert.equal(result.elapsedMs,8000);assert.equal(result.durationMs,undefined);assert.equal(result.frameRate,undefined);
  assert.equal(result.videoTiming.timestampSpanMs,7900);assert.equal(result.videoTiming.encodedPacketCount,5);
  assertClean(h,instance);
});

test('short timestamp coverage rejects even when there are many packets',async()=>{
  let time=0;const h=setup({now:()=>time});const pending=h.recorder.start(),instance=h.instances[0];
  instance.data(await webm([0,100,200,300,400,500]).arrayBuffer());time=8000;instance.finish();
  await assert.rejects(pending,/too little motion/);assertClean(h,instance);
});

test('an intentional early stop is compared with elapsed capture, not the eight-second target',async()=>{
  let time=0;const h=setup({now:()=>time});const pending=h.recorder.start(),instance=h.instances[0];
  instance.data(await webm([0,1000,2900]).arrayBuffer());time=3000;h.recorder.stop();
  time=10000;instance.finish();const result=await pending;
  assert.equal(result.elapsedMs,3000);assert.equal(result.videoTiming.timestampSpanMs,2900);assertClean(h,instance);
});

test('uninspected output explicitly reports unknown timing rather than nominal FPS',async()=>{
  const h=setup(),pending=h.recorder.start(),instance=h.instances[0];instance.data();instance.finish();
  const result=await pending;assert.equal(result.videoTiming.verified,false);
  assert.equal(result.videoTiming.timestampSpanMs,null);assert.match(h.statuses.at(-1).message,/could not be verified/);
});

test('disposal during asynchronous inspection rejects and suppresses late download',async()=>{
  let finish,completed=0;const h=setup({inspect:()=>new Promise(resolve=>{finish=resolve;}),onComplete:()=>completed++});
  const pending=h.recorder.start(),instance=h.instances[0];instance.data();instance.finish();
  assert.equal(h.recorder.recording,true);assert.equal(h.stoppedTracks,1);
  assert.throws(()=>h.recorder.start(),/already recording/);
  const rejected=assert.rejects(pending,{name:'AbortError'});h.recorder.dispose();
  finish({verified:false});await rejected;await Promise.resolve();
  assert.equal(completed,0);assert.equal(h.stoppedTracks,1);assertClean(h,instance);
});

test('inspection timeout permits retry and ignores a stale inspection result',async()=>{
  let finish,completed=0,calls=0;
  const h=setup({inspect:()=>++calls===1?new Promise(resolve=>{finish=resolve;}):Promise.resolve({verified:false}),onComplete:()=>completed++});
  const pending=h.recorder.start(),first=h.instances[0];first.data();first.finish();
  const rejected=assert.rejects(pending,/Checking.*timed out/);[...h.timers.values()][0]();await rejected;
  const retry=h.recorder.start(),second=h.instances[1];second.data();second.finish();await retry;
  finish({verified:true,encodedPacketCount:100,timestampSpanMs:8000});await Promise.resolve();
  assert.equal(completed,1);assertClean(h,second);
});


test('known video container with no packets is rejected even after an early stop',async()=>{
  const h=setup(),pending=h.recorder.start(),instance=h.instances[0];
  instance.data(await webm([]).arrayBuffer());instance.finish();
  await assert.rejects(pending,/too little motion/);assertClean(h,instance);
});

test('completion callback disposal cannot announce a cancelled clip as ready',async()=>{
  const h=setup({onComplete:()=>h.recorder.dispose()});
  const pending=h.recorder.start(),instance=h.instances[0];instance.data();instance.finish();
  await assert.rejects(pending,{name:'AbortError'});assert.equal(h.statuses.at(-1).state,'disposed');assertClean(h,instance);
});

import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source=await readFile(new URL('../assembly-recording.js',import.meta.url),'utf8');
const {createCanvasRecorder}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));

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

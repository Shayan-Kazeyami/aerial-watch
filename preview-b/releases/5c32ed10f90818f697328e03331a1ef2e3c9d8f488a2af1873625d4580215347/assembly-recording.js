// A conservative, local structural check of MediaRecorder WebM output. This is
// NOT a decoder or a guarantee of smooth playback. Unknown layouts are reported
// as unverified, never interpreted as the requested duration/frame rate.
export async function inspectWebM(blob){
  const unverified={verified:false,encodedPacketCount:null,timestampSpanMs:null};
  // Bound memory/work even if a caller supplies an unexpectedly large blob.
  if(blob.size>128*1024*1024)return unverified;
  try{
    const bytes=new Uint8Array(await blob.arrayBuffer());
    const view=new DataView(bytes.buffer);let scale=1000000,elements=0;
    const tracks=new Map(),packets=[];
    function vint(at,id=false){
      if(at>=bytes.length||bytes[at]===0)throw Error('Invalid EBML integer');
      let length=1,mask=128;while(!(bytes[at]&mask)){length++;mask>>=1;}
      if(length>(id?4:8)||at+length>bytes.length)throw Error('Truncated EBML integer');
      let value=id?bytes[at]:bytes[at]&(mask-1),unknown=!id&&value===mask-1;
      for(let i=1;i<length;i++){value=value*256+bytes[at+i];unknown=unknown&&bytes[at+i]===255;}
      if(!unknown&&!Number.isSafeInteger(value))throw Error('Oversized EBML integer');
      return {value,length,unknown};
    }
    function uint(start,end){
      if(end-start<1||end-start>6)throw Error('Invalid EBML unsigned integer');
      let value=0;for(let i=start;i<end;i++)value=value*256+bytes[i];return value;
    }
    function children(start,end,visit){
      for(let at=start;at<end;){
        if(++elements>1000000)throw Error('Too many EBML elements');
        const id=vint(at,true),size=vint(at+id.length),data=at+id.length+size.length;
        // Unknown-size Segment is standard for streaming recordings. Other
        // unknown containers require a full schema parser: do not guess bounds.
        if(size.unknown&&id.value!==0x18538067)throw Error('Unsupported streaming container');
        const next=size.unknown?end:data+size.value;
        if(next>end||next<data)throw Error('Truncated EBML element');
        visit(id.value,data,next);at=next;
      }
    }
    function packet(start,end,cluster){
      const track=vint(start),header=start+track.length;
      if(track.unknown||header+3>=end)throw Error('Truncated video block');
      if(bytes[header+2]&6)throw Error('Laced blocks not inspected');
      packets.push({track:track.value,time:cluster+view.getInt16(header)});
    }
    let segment=false,header=false;
    children(0,bytes.length,(id,start,end)=>{
      if(id===0x1a45dfa3)header=true;
      if(id!==0x18538067)return;segment=true;
      children(start,end,(id,start,end)=>{
        if(id===0x1549a966)children(start,end,(id,start,end)=>{if(id===0x2ad7b1)scale=uint(start,end);});
        if(id===0x1654ae6b)children(start,end,(id,start,end)=>{
          if(id!==0xae)return;let number,type;
          children(start,end,(id,start,end)=>{if(id===0xd7)number=uint(start,end);if(id===0x83)type=uint(start,end);});
          if(number!==undefined)tracks.set(number,type);
        });
        if(id===0x1f43b675){
          let time=null;const blocks=[];
          children(start,end,(id,start,end)=>{
            if(id===0xe7)time=uint(start,end);
            if(id===0xa3)blocks.push([start,end]);
            if(id===0xa0)children(start,end,(id,start,end)=>{if(id===0xa1)blocks.push([start,end]);});
          });
          if(time===null)throw Error('Missing cluster timestamp');
          for(const [start,end] of blocks)packet(start,end,time);
        }
      });
    });
    const videoTracks=[...tracks].filter(([,type])=>type===1);
    if(!header||!segment||videoTracks.length!==1||scale<=0)return unverified;
    const times=packets.filter(p=>p.track===videoTracks[0][0]).map(p=>p.time);
    if(!times.length)return {...unverified,verified:true,encodedPacketCount:0,timestampSpanMs:0};
    let first=Infinity,last=-Infinity;for(const time of times){first=Math.min(first,time);last=Math.max(last,time);}
    return {verified:true,encodedPacketCount:times.length,timestampSpanMs:(last-first)*scale/1000000};
  }catch{return unverified;}
}

// Records only the displayed canvas. Playback, watch clocks and camera state
// remain owned by the viewer. No audio, network upload or hidden rendering.
export function createCanvasRecorder({canvas,onStatus=()=>{},onComplete=()=>{},
  MediaRecorderClass=globalThis.MediaRecorder,durationMs=8000,frameRate=30,
  videoBitsPerSecond=12000000,finalizeTimeoutMs=5000,schedule=setTimeout,cancel=clearTimeout,
  now=()=>globalThis.performance.now(),inspect=inspectWebM}={}){
  let active=null,disposed=false;
  const status=(message,state,error)=>onStatus(message,{state,error});
  function cleanup(recording,release=true){
    if(recording.timer!==undefined){cancel(recording.timer);recording.timer=undefined;}
    if(recording.finalizeTimer!==undefined){cancel(recording.finalizeTimer);recording.finalizeTimer=undefined;}
    recording.stream?.getTracks().forEach(track=>track.stop());recording.stream=null;
    if(recording.recorder){recording.recorder.ondataavailable=null;recording.recorder.onerror=null;recording.recorder.onstop=null;}
    if(release&&active===recording)active=null;
  }
  function fail(recording,error){
    if(recording.settled)return;recording.settled=true;
    // Detach events before stopping to avoid a second completion callback.
    const recorder=recording.recorder;cleanup(recording);
    try{if(recorder&&recorder.state!=='inactive')recorder.stop();}catch{/* Tracks are already closed. */}
    try{status(error.message,disposed?'disposed':'error',error);}finally{recording.reject(error);}
  }
  function stop(){if(!active)return false;const recording=active;
    if(recording.stopRequested)return false;recording.stopRequested=true;recording.stoppedAt=now();
    try{
      // A browser can stop encoding without dispatching its final data/stop event.
      // Bound that wait so the caller can recover rather than stay disabled.
      recording.finalizeTimer=schedule(()=>fail(recording,new Error('Finishing the motion clip timed out. Please try recording again.')),finalizeTimeoutMs);
      recording.recorder.stop();
    }catch(error){fail(recording,error);}return true;
  }
  return {
    get recording(){return !!active;},
    get disposed(){return disposed;},
    start(){
      if(disposed)throw new Error('The motion recorder has been disposed. Reload the viewer to record again.');
      if(active)throw new Error('A motion clip is already recording. Wait for it to finish.');
      if(typeof canvas?.captureStream!=='function'||typeof MediaRecorderClass!=='function')throw new Error('This browser cannot record the watch canvas. Use a current browser with WebM recording support.');
      const candidates=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'];
      const mimeType=candidates.find(type=>typeof MediaRecorderClass.isTypeSupported!=='function'||MediaRecorderClass.isTypeSupported(type));
      if(!mimeType)throw new Error('WebM video recording is unavailable in this browser. You can still save a still image.');
      if(!Number.isFinite(durationMs)||durationMs<=0||!Number.isFinite(frameRate)||frameRate<=0)throw new Error('A positive recording duration and frame rate are required.');
      if(!Number.isFinite(finalizeTimeoutMs)||finalizeTimeoutMs<=0)throw new Error('A positive recording finalization timeout is required.');
      let resolve,reject;const completion=new Promise((yes,no)=>{resolve=yes;reject=no;});
      const recording={resolve,reject,chunks:[],settled:false,stopRequested:false};active=recording;
      try{
        recording.stream=canvas.captureStream(frameRate);
        recording.recorder=new MediaRecorderClass(recording.stream,{mimeType,videoBitsPerSecond});
        recording.recorder.ondataavailable=event=>{if(event.data?.size)recording.chunks.push(event.data);};
        recording.recorder.onerror=event=>fail(recording,event.error||new Error('The browser could not finish the motion clip.'));
        recording.recorder.onstop=async()=>{
          if(recording.settled||recording.inspecting)return;
          recording.inspecting=true;recording.stopRequested=true;
          const elapsedMs=Math.max(0,(recording.stoppedAt??now())-recording.startedAt);
          const blob=new Blob(recording.chunks,{type:recording.recorder.mimeType||mimeType});
          // Release capture immediately, but retain ownership until inspection
          // finishes so disposal and duplicate starts still work correctly.
          cleanup(recording,false);
          if(!blob.size){fail(recording,new Error('The browser produced an empty clip. Start the watch motion and try recording again.'));return;}
          try{
            status('Checking captured motion…','finalizing');
            if(recording.settled)return;
            recording.finalizeTimer=schedule(()=>fail(recording,new Error('Checking the motion clip timed out. Please try recording again.')),finalizeTimeoutMs);
            const videoTiming=await inspect(blob);
            if(recording.settled)return;
            // A few widely spaced packets are not a useful motion clip even
            // when they cover most of the requested interval. This is only a
            // structural cadence floor, NOT measured decoded FPS or a smoothness
            // guarantee. Compare with elapsed capture time, including early stops.
            const sparse=videoTiming.verified&&(videoTiming.encodedPacketCount===0||(elapsedMs>=2000&&
              (videoTiming.encodedPacketCount/(elapsedMs/1000)<8||videoTiming.timestampSpanMs<elapsedMs*0.75)));
            if(sparse){
              const error=new Error('The browser captured too little motion for a usable clip. Start the watch motion if paused, choose Smoother motion quality, keep this tab visible, and record again.');
              error.videoTiming=videoTiming;error.elapsedMs=elapsedMs;fail(recording,error);return;
            }
            const result={blob,mimeType:blob.type,requestedDurationMs:durationMs,requestedFrameRate:frameRate,
              elapsedMs,videoTiming};
            // Packet timestamps are not decoded duration or achieved FPS.
            onComplete(result);
            if(recording.settled)return;
            status(videoTiming.verified?'Motion clip ready.':'Motion clip ready; playback quality could not be verified.','complete');
            if(recording.settled)return;
            recording.settled=true;cleanup(recording);resolve(result);
          }catch(error){fail(recording,error);}
        };
        recording.startedAt=now();recording.recorder.start();recording.timer=schedule(stop,durationMs);
        status(`Recording ${durationMs/1000}-second motion clip…`,'recording');
      }catch(error){fail(recording,error);}
      return completion;
    },
    stop,
    dispose(){if(disposed)return;disposed=true;if(active){const error=new Error('Motion recording cancelled because the viewer closed.');error.name='AbortError';fail(active,error);}},
  };
}

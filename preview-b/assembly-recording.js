// Records only the displayed canvas. Playback, watch clocks and camera state
// remain owned by the viewer. No audio, network upload or hidden rendering.
export function createCanvasRecorder({canvas,onStatus=()=>{},onComplete=()=>{},
  MediaRecorderClass=globalThis.MediaRecorder,durationMs=8000,frameRate=30,
  videoBitsPerSecond=12000000,finalizeTimeoutMs=5000,schedule=setTimeout,cancel=clearTimeout}={}){
  let active=null,disposed=false;
  const status=(message,state,error)=>onStatus(message,{state,error});
  function cleanup(recording){
    if(recording.timer!==undefined){cancel(recording.timer);recording.timer=undefined;}
    if(recording.finalizeTimer!==undefined){cancel(recording.finalizeTimer);recording.finalizeTimer=undefined;}
    recording.stream?.getTracks().forEach(track=>track.stop());
    if(recording.recorder){recording.recorder.ondataavailable=null;recording.recorder.onerror=null;recording.recorder.onstop=null;}
    if(active===recording)active=null;
  }
  function fail(recording,error){
    if(recording.settled)return;recording.settled=true;
    // Detach events before stopping to avoid a second completion callback.
    const recorder=recording.recorder;cleanup(recording);
    try{if(recorder&&recorder.state!=='inactive')recorder.stop();}catch{/* Tracks are already closed. */}
    status(error.message,disposed?'disposed':'error',error);recording.reject(error);
  }
  function stop(){if(!active)return false;const recording=active;
    if(recording.stopRequested)return false;recording.stopRequested=true;
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
        recording.recorder.onstop=()=>{
          if(recording.settled)return;recording.settled=true;
          const blob=new Blob(recording.chunks,{type:recording.recorder.mimeType||mimeType});cleanup(recording);
          if(!blob.size){const error=new Error('The browser produced an empty clip. Start the watch motion and try recording again.');status(error.message,'error',error);reject(error);return;}
          const result={blob,mimeType:blob.type,durationMs,frameRate};
          try{onComplete(result);status('Motion clip ready.','complete');resolve(result);}catch(error){status(error.message,'error',error);reject(error);}
        };
        recording.recorder.start();recording.timer=schedule(stop,durationMs);
        status(`Recording ${durationMs/1000}-second motion clip…`,'recording');
      }catch(error){fail(recording,error);}
      return completion;
    },
    stop,
    dispose(){if(disposed)return;disposed=true;if(active){const error=new Error('Motion recording cancelled because the viewer closed.');error.name='AbortError';fail(active,error);}},
  };
}

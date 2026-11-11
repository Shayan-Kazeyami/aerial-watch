import {muxWebM} from './assembly-webm-muxer.js';

const abortError=()=>Object.assign(new Error('Video render cancelled. No video was saved.'),{name:'AbortError'});
const positive=(value,name)=>{if(!Number.isFinite(value)||value<=0)throw new TypeError(`${name} must be positive and finite.`);};

// Render one scene sample per output frame, independently of the display's RAF
// cadence. The application owns its scene, pause/restore behavior and cancellation
// controls. Scene hooks (begin, renderFrame and end) must be synchronous: they
// must finish their mutations before returning, and must not start background
// work. This never replaces a failed real-time recording with a sparse clip.
export function createFrameVideoExporter({canvas,begin=()=>{},renderFrame,end=()=>{},onProgress=()=>{},
  Encoder=globalThis.VideoEncoder,Frame=globalThis.VideoFrame,mux=muxWebM,
  yieldTask=()=>new Promise(resolve=>setTimeout(resolve,0)),timeoutMs=60000,
  schedule=setTimeout,unschedule=clearTimeout,maxOutputBytes=128*1024*1024}={}){
 let active=null,disposed=false;
 const check=session=>{if(session.cancelled)throw session.error||abortError();};
 function bounded(session,promise,label){
  return new Promise((resolve,reject)=>{
   let done=false,timer;
   const finish=(fn,value)=>{if(done)return;done=true;unschedule(timer);session.waiters.delete(abort);fn(value);};
   const abort=()=>finish(reject,session.error||abortError());session.waiters.add(abort);
   timer=schedule(()=>finish(reject,new Error(`${label} timed out. No video was saved.`)),timeoutMs);
   Promise.resolve(promise).then(value=>finish(resolve,value),error=>finish(reject,error));
  });
 }
 function cancelSession(session,error){
  if(!session||session!==active||session.cancelled||session.settled)return false;
  session.cancelled=true;session.error=error||abortError();for(const abort of [...session.waiters])abort();return true;
 }
 const synchronous=(callback,args,label)=>{
  const value=callback(...args);
  if(value&&typeof value.then==='function')throw new TypeError(`${label} must be synchronous and must not start background work.`);
  return value;
 };
 return {
  get active(){return !!active;},
  cancel(){return cancelSession(active);},
  dispose(){disposed=true;cancelSession(active);},
  async start({durationMs=8000,frameRate=30,bitrate=8000000}={}){
   if(disposed)throw new Error('The video exporter has closed. Reload the viewer to render video.');
   if(active)throw new Error('A video is already rendering. Wait or cancel it first.');
   if(typeof Encoder!=='function'||typeof Frame!=='function'||typeof Encoder.isConfigSupported!=='function')throw new Error('Frame-by-frame video export is unavailable in this browser. Try a current Chrome or Edge browser, or save a PNG image.');
   if(typeof renderFrame!=='function')throw new TypeError('A renderFrame callback is required.');
   for(const hook of [begin,renderFrame,end])if(hook?.constructor?.name==='AsyncFunction')throw new TypeError('Scene hooks must be synchronous and must not start background work.');
   positive(durationMs,'Duration');positive(frameRate,'Frame rate');positive(bitrate,'Bitrate');positive(timeoutMs,'Timeout');positive(maxOutputBytes,'Output byte limit');
   if(durationMs>30000||frameRate>60)throw new RangeError('Video export is limited to 30 seconds and 60 frames per second.');
   const width=canvas?.width,height=canvas?.height;
   if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>8192||height>8192||width*height>16777216)throw new RangeError('Video canvas dimensions are unsupported.');
   const frameCount=Math.round(durationMs*frameRate/1000);
   if(frameCount<1)throw new RangeError('The video must contain at least one frame.');
   // The encoded duration is an exact whole number of frames.
   const encodedDurationMs=frameCount*1000/frameRate;
   const session={cancelled:false,settled:false,error:null,waiters:new Set()};active=session;
   let encoder,context,began=false,framesEncoded=0,totalBytes=0,config,codec;
   const chunks=[];
   try{
    for(const candidate of [{codec:'vp09.00.10.08',container:'vp9'},{codec:'vp8',container:'vp8'}]){
     check(session);
     try{const proposed={codec:candidate.codec,width,height,bitrate,framerate:frameRate,latencyMode:'quality'};
      const support=await bounded(session,Encoder.isConfigSupported(proposed),'Video encoder setup');
      if(support.supported){config=support.config;codec=candidate.container;break;}
     }catch(error){check(session);if(/timed out/.test(error.message))throw error;}
    }
    if(!config)throw new Error('This browser cannot encode this video size. Try a smaller browser window or save a PNG image.');
    encoder=new Encoder({output:chunk=>{
     if(active!==session||session.cancelled||session.settled)return;
     try{
      totalBytes+=chunk.byteLength;
      if(totalBytes>maxOutputBytes)throw new Error('The video exceeded its memory limit. Try a smaller browser window.');
      const data=new Uint8Array(chunk.byteLength);chunk.copyTo(data);
      chunks.push({type:chunk.type,timestamp:chunk.timestamp,duration:chunk.duration,data});framesEncoded++;
     }catch(error){cancelSession(session,error);}
    },error:error=>cancelSession(session,error)});
    encoder.configure(config);check(session);
    context=synchronous(begin,[{frameCount,frameRate,durationMs:encodedDurationMs,width,height}],'Scene preparation');began=true;check(session);
    onProgress({completed:0,total:frameCount,phase:'rendering'});
    for(let index=0;index<frameCount;index++){
     check(session);
     if(canvas.width!==width||canvas.height!==height)throw new Error('The watch view changed size. Render again when resizing is finished.');
     const timestamp=Math.round(index*1000000/frameRate),next=Math.round((index+1)*1000000/frameRate);
     synchronous(renderFrame,[index/frameRate,{index,frameCount,frameRate,context}],'Watch frame render');check(session);
     let frame;
     try{frame=new Frame(canvas,{timestamp,duration:next-timestamp,alpha:'discard'});encoder.encode(frame,{keyFrame:index===0||index%Math.round(frameRate*2)===0});}
     finally{frame?.close();}
     if(encoder.encodeQueueSize>=4)await bounded(session,encoder.flush(),'Video encoding');
     check(session);onProgress({completed:index+1,total:frameCount,phase:'rendering'});await bounded(session,yieldTask(),'Video render scheduling');
    }
    check(session);onProgress({completed:frameCount,total:frameCount,phase:'encoding'});
    await bounded(session,encoder.flush(),'Video encoding');check(session);
    if(framesEncoded!==frameCount)throw new Error(`The encoder returned ${framesEncoded} of ${frameCount} frames. No video was saved.`);
    const bytes=mux({chunks,width,height,frameRate,durationMs:encodedDurationMs,codec,expectedFrames:frameCount,maxOutputBytes});check(session);
    if(bytes.byteLength>maxOutputBytes)throw new Error('The video exceeded its memory limit. No video was saved.');
    return {blob:new Blob([bytes],{type:'video/webm'}),width,height,frameRate,frameCount,durationMs:encodedDurationMs,codec};
   }finally{
    session.settled=true;
    try{if(encoder&&encoder.state!=='closed')encoder.close();}finally{
     try{if(began)synchronous(end,[context],'Scene restoration');}finally{active=null;chunks.length=0;}
    }
   }
  },
 };
}

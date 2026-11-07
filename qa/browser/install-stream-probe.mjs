// API-observation probe. Defaults preserve stream rate, pixels, recorder options and lifecycle.
// Explicit requestFrames experiment is opt-in and separately labelled; never changes quality.
export async function installStreamProbe(page,{requestFrames=false}={}){
 await page.addInitScript(({requestFrames})=>{
  const log=window.__qaStreamProbe={mode:requestFrames?'EXPERIMENT explicit track.requestFrame every250ms':'OBSERVATION_ONLY',streams:[],recorders:[]};
  const original=HTMLCanvasElement.prototype.captureStream;
  if(original)HTMLCanvasElement.prototype.captureStream=function(...args){
   const stream=Reflect.apply(original,this,args),entry={at:performance.now(),args,canvas:{width:this.width,height:this.height},tracks:[]};log.streams.push(entry);
   for(const track of stream.getVideoTracks()){
    const t={id:track.id,kind:track.kind,settings:track.getSettings(),requestFrameSupported:typeof track.requestFrame==='function',events:[],samples:[],requests:0};entry.tracks.push(t);
    for(const type of ['mute','unmute','ended'])track.addEventListener(type,()=>t.events.push({type,at:performance.now(),readyState:track.readyState,muted:track.muted}));
    const sample=()=>{t.samples.push({at:performance.now(),readyState:track.readyState,muted:track.muted,enabled:track.enabled});if(requestFrames&&track.readyState==='live'&&typeof track.requestFrame==='function'){try{track.requestFrame();t.requests++;}catch(error){t.events.push({type:'requestFrame-error',message:error.message});}}};
    sample();const timer=setInterval(()=>{sample();if(track.readyState==='ended')clearInterval(timer);},250);setTimeout(()=>clearInterval(timer),30000);
   }return stream;
  };
  const Native=globalThis.MediaRecorder;if(Native)globalThis.MediaRecorder=class extends Native{
   constructor(...args){super(...args);const e={at:performance.now(),options:args[1],mimeType:this.mimeType,videoBitsPerSecond:this.videoBitsPerSecond,events:[]};log.recorders.push(e);
    for(const name of ['start','stop','pause','resume','error','dataavailable'])this.addEventListener(name,event=>e.events.push({name,at:performance.now(),state:this.state,dataBytes:event.data?.size,dataType:event.data?.type,error:event.error?.message}));
   }
  };
 },{requestFrames});
}
export const readStreamProbe=page=>page.evaluate(()=>window.__qaStreamProbe||null);

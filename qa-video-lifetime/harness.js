const arm=location.pathname.includes('/candidate/')?'candidate':'original';
const {createOfflineVideoExport}=await import('./'+arm+'/assembly-offline-video.js');
window.qaReleaseCount=0;window.qaAllocations=[];
window.qaAllocate=n=>{qaAllocations.push(n);return new Uint8Array(n)};
const canvas=document.querySelector('canvas'),gl=canvas.getContext('webgl2',{preserveDrawingBuffer:true});
if(!gl)throw new Error('Real WebGL2 unavailable');
let state={time:7},ends=0,renders=0;
function render(t){
 gl.disable(gl.SCISSOR_TEST);gl.clearColor(.1,.1,.1,1);gl.clear(gl.COLOR_BUFFER_BIT);
 gl.enable(gl.SCISSOR_TEST);gl.scissor(0,0,96,32);gl.clearColor(t%1,.1,.8,1);gl.clear(gl.COLOR_BUFFER_BIT);
 gl.scissor(0,32,96,32);gl.clearColor(.8,.3,t%1,1);gl.clear(gl.COLOR_BUFFER_BIT);gl.disable(gl.SCISSOR_TEST);
}
render(0);
const exp=createOfflineVideoExport({canvas,gl,
 begin(){const old={...state};state.time=0;return old},
 renderFrame(t){state.time=t;renders++;render(t)},
 end(old){state={...old};ends++;render(0)}
});
window.qaReady=true;
window.qaCaptureState=()=>({renders,ends});
window.success=async()=>{
 const result=await exp.start({durationMs:1000,frameRate:12,bitrate:500000});
 const bytes=new Uint8Array(await result.blob.arrayBuffer());
 const url=URL.createObjectURL(result.blob),video=document.createElement('video');video.muted=true;video.src=url;document.body.append(video);
 try{
  await new Promise((resolve,reject)=>{video.onloadeddata=resolve;video.onerror=()=>reject(new Error('Produced WebM did not decode'))});
  video.currentTime=.5;await new Promise(resolve=>video.onseeked=resolve);
  const decoded=document.createElement('canvas');decoded.width=96;decoded.height=64;
  const ctx=decoded.getContext('2d');ctx.drawImage(video,0,0);
  const top=Array.from(ctx.getImageData(48,8,1,1).data),bottom=Array.from(ctx.getImageData(48,56,1,1).data);
  if(top[0]<170||bottom[2]<170)throw new Error('Decoded video orientation/color mismatch');
  let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);
  return {frameCount:result.frameCount,width:result.width,height:result.height,durationMs:result.durationMs,codec:result.codec,videoBase64:btoa(binary),top,bottom,state:{...state},ends,renders,allocations:[...qaAllocations],releases:qaReleaseCount,active:exp.active,dialogOpen:!!document.querySelector('dialog[open]')};
 }finally{URL.revokeObjectURL(url);video.remove()}
};
window.startCancel=()=>{
 window.cancelResult=null;
 exp.start({durationMs:30000,frameRate:60,bitrate:500000}).then(()=>cancelResult={unexpectedSuccess:true},e=>cancelResult={name:e.name,message:e.message,state:{...state},ends,allocations:[...qaAllocations],releases:qaReleaseCount,active:exp.active,dialogOpen:!!document.querySelector('dialog[open]')});
};
window.disposeExport=()=>{exp.dispose();return {releases:qaReleaseCount,dialogCount:document.querySelectorAll('dialog').length}};

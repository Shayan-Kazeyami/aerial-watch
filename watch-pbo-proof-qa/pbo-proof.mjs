// Isolated feasibility helper. NOT integrated into Watch or approved for release.
// Caller owns rendering and must not mutate its scene/framebuffer while active.
import {createReadbackVideoFrame} from './original-frame.mjs';
const abort=()=>Object.assign(new Error('Readback aborted'),{name:'AbortError'});
export function createPBOProof({canvas,gl,pause=()=>new Promise(r=>setTimeout(r,0)),maxPolls=100}={}) {
 let active=false;const audit={createdBuffers:0,deletedBuffers:0,createdSyncs:0,deletedSyncs:0,initialStatuses:[],fallbacks:0};
 class PixelFrame {constructor(p){this.pixels=new Uint8Array(p);}close(){}}
 const original=createReadbackVideoFrame({canvas,gl,Frame:PixelFrame});
 const check=signal=>{if(signal?.aborted)throw abort();if(gl.isContextLost())throw Error('Context lost');};
 return {audit,get active(){return active;},async read({signal}={}){
  if(active)throw Error('Readback already active');
  const width=canvas.width,height=canvas.height;
  if(width<1||height<1||width>256||height>256)throw Error('Proof resource limit');
  active=true;let buffer=null,fence=null;
  try {
   check(signal);
   if(!gl.fenceSync||!gl.getBufferSubData){audit.fallbacks++;const f=original({timestamp:0});try{return f.pixels;}finally{f.close();original.release();}}
   if(gl.getParameter(gl.FRAMEBUFFER_BINDING)!==null)throw Error('Completed screen framebuffer required');
   if(gl.getParameter(gl.PACK_ROW_LENGTH)!==0||gl.getParameter(gl.PACK_SKIP_PIXELS)!==0||gl.getParameter(gl.PACK_SKIP_ROWS)!==0||gl.getParameter(gl.PACK_ALIGNMENT)!==4)throw Error('Unsupported pack state');
   buffer=gl.createBuffer();if(!buffer)throw Error('Buffer allocation refused');audit.createdBuffers++;
   const old=gl.getParameter(gl.PIXEL_PACK_BUFFER_BINDING);
   try {gl.bindBuffer(gl.PIXEL_PACK_BUFFER,buffer);gl.bufferData(gl.PIXEL_PACK_BUFFER,width*height*4,gl.STREAM_READ);gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,0);}
   finally {gl.bindBuffer(gl.PIXEL_PACK_BUFFER,old);}
   // Snapshot command issued before yielding: no dependence on canvas retention.
   fence=gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE,0);if(!fence)throw Error('Fence allocation refused');audit.createdSyncs++;gl.flush();
   let status=gl.clientWaitSync(fence,0,0);audit.initialStatuses.push(status);
   await pause();check(signal);
   let polls=0;
   while(status===gl.TIMEOUT_EXPIRED){if(++polls>maxPolls)throw Error('Fence poll limit');status=gl.clientWaitSync(fence,0,0);if(status===gl.TIMEOUT_EXPIRED){await pause();check(signal);}}
   if(status!==gl.ALREADY_SIGNALED&&status!==gl.CONDITION_SATISFIED)throw Error('Fence wait failed');check(signal);
   if(canvas.width!==width||canvas.height!==height)throw Error('Source dimensions changed');
   const data=new Uint8Array(width*height*4),binding=gl.getParameter(gl.PIXEL_PACK_BUFFER_BINDING);
   try{gl.bindBuffer(gl.PIXEL_PACK_BUFFER,buffer);gl.getBufferSubData(gl.PIXEL_PACK_BUFFER,0,data);}finally{gl.bindBuffer(gl.PIXEL_PACK_BUFFER,binding);}
   const row=new Uint8Array(width*4);for(let y=0;y<Math.floor(height/2);y++){const a=y*width*4,b=(height-1-y)*width*4;row.set(data.subarray(a,a+width*4));data.copyWithin(a,b,b+width*4);data.set(row,b);}
   return data;
  }finally{if(fence){gl.deleteSync(fence);audit.deletedSyncs++;}if(buffer){gl.deleteBuffer(buffer);audit.deletedBuffers++;}active=false;}
 }};
}

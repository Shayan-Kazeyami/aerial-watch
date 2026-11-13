// Give WebCodecs owned CPU pixels, not a retained WebGL surface. GPU-backed
// canvas frames can stall encoder flush when a native modal occludes the view.
export function createReadbackVideoFrame({canvas,gl,Frame=globalThis.VideoFrame,doc=globalThis.document}={}){
 let pixels,row,copyCanvas,copyContext,width=0,height=0;
 return metadata=>{
  const w=canvas.width,h=canvas.height;
  if(gl?.isContextLost?.())throw new Error('The graphics context closed during video capture.');
  if(gl?.readPixels){
   if(gl.getParameter(gl.FRAMEBUFFER_BINDING)!==null)throw new Error('Video capture requires the completed screen frame.');
   const stride=w*4;
   if(w!==width||h!==height){pixels=new Uint8Array(stride*h);row=new Uint8Array(stride);width=w;height=h;}
   gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
   // WebGL has a bottom-left origin; WebCodecs RGBA buffers are top-left.
   for(let y=0;y<Math.floor(h/2);y++){const a=y*stride,b=(h-1-y)*stride;row.set(pixels.subarray(a,a+stride));pixels.copyWithin(a,b,b+stride);pixels.set(row,b);}
  }else{
   copyCanvas??=doc.createElement('canvas');copyContext??=copyCanvas.getContext('2d',{alpha:false,willReadFrequently:true});
   if(!copyContext)throw new Error('This browser cannot prepare video pixels.');
   if(copyCanvas.width!==w||copyCanvas.height!==h){copyCanvas.width=w;copyCanvas.height=h;}
   copyContext.drawImage(canvas,0,0);pixels=copyContext.getImageData(0,0,w,h).data;
  }
  return new Frame(pixels,{...metadata,format:'RGBA',codedWidth:w,codedHeight:h});
 };
}

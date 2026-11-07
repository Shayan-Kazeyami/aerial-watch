export function installOpaqueCaptureProbe(){
 const original=HTMLCanvasElement.prototype.toBlob;
 window.__opaqueCaptureProbe={scope:'Single observed native PNG export; readPixels synchronizes and may change reproduction. No quality or scene mutation.',calls:[]};
 const errors=gl=>{const out=[];for(let i=0;i<16;i++){const e=gl.getError();if(e===gl.NO_ERROR)break;out.push(e);}return out;};
 const snapshot=gl=>({attributes:gl.getContextAttributes(),contextLost:gl.isContextLost(),drawingBuffer:[gl.drawingBufferWidth,gl.drawingBufferHeight],framebufferDefault:gl.getParameter(gl.FRAMEBUFFER_BINDING)===null,readFramebufferDefault:gl.getParameter(gl.READ_FRAMEBUFFER_BINDING)===null,drawFramebufferDefault:gl.getParameter(gl.DRAW_FRAMEBUFFER_BINDING)===null,framebufferStatus:gl.checkFramebufferStatus(gl.FRAMEBUFFER),viewport:Array.from(gl.getParameter(gl.VIEWPORT)),scissor:Array.from(gl.getParameter(gl.SCISSOR_BOX)),scissorTest:gl.isEnabled(gl.SCISSOR_TEST),colorWriteMask:Array.from(gl.getParameter(gl.COLOR_WRITEMASK)),packAlignment:gl.getParameter(gl.PACK_ALIGNMENT),packRowLength:gl.getParameter(gl.PACK_ROW_LENGTH),packSkipRows:gl.getParameter(gl.PACK_SKIP_ROWS),packSkipPixels:gl.getParameter(gl.PACK_SKIP_PIXELS),pixelPackBufferBound:gl.getParameter(gl.PIXEL_PACK_BUFFER_BINDING)!==null,limits:{maxTextureSize:gl.getParameter(gl.MAX_TEXTURE_SIZE),maxRenderbufferSize:gl.getParameter(gl.MAX_RENDERBUFFER_SIZE),maxViewportDims:Array.from(gl.getParameter(gl.MAX_VIEWPORT_DIMS)),maxSamples:gl.getParameter(gl.MAX_SAMPLES)}});
 HTMLCanvasElement.prototype.toBlob=function(...args){
  if(this.id!=='assembly-canvas')return original.apply(this,args);
  const record={at:performance.now(),width:this.width,height:this.height};window.__opaqueCaptureProbe.calls.push(record);
  try{
   if(window.__opaqueCaptureProbe.calls.length!==1)throw Error('Only one instrumented canvas readback authorized');
   const gl=this.getContext('webgl2');if(!gl)throw Error('Existing WebGL2 context unavailable');
   record.errorsBefore=errors(gl);record.before=snapshot(gl);const n=this.width*this.height,bytes=n*4;
   if(!Number.isSafeInteger(bytes)||bytes>50000000)throw Error('ReadPixels 50MB limit');
   if(!record.before.framebufferDefault||!record.before.readFramebufferDefault||record.before.pixelPackBufferBound||record.before.packRowLength||record.before.packSkipRows||record.before.packSkipPixels)throw Error('Unexpected readback state; will not rebind/reset it');
   let pixels=new Uint8Array(bytes);const began=performance.now();gl.readPixels(0,0,this.width,this.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);record.readPixelsMs=performance.now()-began;record.errorsAfterRead=errors(gl);record.after=snapshot(gl);
   const mask=new Uint8Array(Math.ceil(n/8));let nonOpaque=0,zeroAlpha=0;const samples=[];
   for(let y=0;y<this.height;y++)for(let x=0;x<this.width;x++){const p=y*this.width+x,source=((this.height-1-y)*this.width+x)*4,a=pixels[source+3];if(a!==255){nonOpaque++;mask[p>>3]|=1<<(p&7);}if(a===0)zeroAlpha++;if((x===2000&&(y===500||y===1500))||(y===500&&(x===300||x===3800)))samples.push({x,y,rgba:Array.from(pixels.subarray(source,source+4))});}
   pixels=null;let binary='';for(let i=0;i<mask.length;i+=16384)binary+=String.fromCharCode(...mask.subarray(i,i+16384));
   record.maskBase64=btoa(binary);record.coverage={pixels:n,nonOpaque,zeroAlpha,samples,maskCoordinates:'PNG top-left; one nonopaque bit per pixel, least significant bit first'};
  }catch(e){record.error=String(e?.message||e);}
  const callback=args[0];args[0]=function(blob){record.callbackAt=performance.now();record.blobBytes=blob?.size??null;return callback.apply(this,arguments);};
  record.beforeNativeToBlob=performance.now();
  try{return original.apply(this,args);}finally{record.nativeReturnedAt=performance.now();}
 };
}

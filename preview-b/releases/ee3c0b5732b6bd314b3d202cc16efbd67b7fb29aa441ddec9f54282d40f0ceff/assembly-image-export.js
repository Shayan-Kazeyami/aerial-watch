/** Bound callback waiting after the native toBlob call returns.
 * Some software backends block inside toBlob while reading pixels. JavaScript
 * cannot interrupt that native call; starting its callback deadline beforehand
 * can reject a valid image immediately after the main thread unblocks.
 */
export function captureCanvasPNG(canvas,{timeoutMs=10000,signal}={}){
  if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('timeoutMs must be positive.');
  return new Promise((resolve,reject)=>{
    let settled=false,timer;
    const finish=(error,blob)=>{if(settled)return;settled=true;clearTimeout(timer);signal?.removeEventListener('abort',abort);error?reject(error):resolve(blob);};
    const abort=()=>{if(settled)return;settled=true;clearTimeout(timer);signal.removeEventListener('abort',abort);reject(signal.reason);};
    signal?.addEventListener('abort',abort,{once:true});
    if(signal?.aborted){abort();return;}
    try{
      canvas.toBlob(blob=>finish(blob?null:new Error('The canvas could not create an image.'),blob),'image/png');
      // A synchronous callback may already have settled the request.
      if(!settled)timer=setTimeout(()=>finish(new Error('Image encoding timed out. Please retry the image export.')),timeoutMs);
    }catch(error){finish(error);}
  });
}

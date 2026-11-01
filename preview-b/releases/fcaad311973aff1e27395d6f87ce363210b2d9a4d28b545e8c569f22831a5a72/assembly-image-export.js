/** Bounded browser PNG encoding: a missing callback must not lock Save image. */
export function captureCanvasPNG(canvas,{timeoutMs=10000}={}){
  if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('timeoutMs must be positive.');
  return new Promise((resolve,reject)=>{
    let settled=false;
    const finish=(error,blob)=>{if(settled)return;settled=true;clearTimeout(timer);error?reject(error):resolve(blob);};
    const timer=setTimeout(()=>finish(new Error('Image encoding timed out. Try a lower image quality and save again.')),timeoutMs);
    try{canvas.toBlob(blob=>finish(blob?null:new Error('The canvas could not create an image.'),blob),'image/png');}
    catch(error){finish(error);}
  });
}

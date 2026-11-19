// The unmodified r180 pass loads two embedded PNGs asynchronously. Await ready
// before presenting the first composed frame. This helper never changes pass
// settings/resolution, and wraps disposal so late image events cannot revive it.
export function prepareSMAAPass(pass,{signal,timeoutMs=10000}={}) {
  const textures=[pass?._areaTexture,pass?._searchTexture];
  if(textures.some(texture=>!texture?.image)||typeof pass?.dispose!=='function')throw new TypeError('Three r180 SMAAPass required.');
  const originalDispose=pass.dispose,cleanups=[];
  let disposed=false,settled=false,timer,rejectReady;
  const abortError=()=>Object.assign(new Error('SMAA preparation canceled.'),{name:'AbortError'});
  function cleanup(){clearTimeout(timer);while(cleanups.length)cleanups.pop()();}
  function fail(error){if(settled)return;settled=true;cleanup();rejectReady(error);}
  function dispose(){
    if(disposed)return;disposed=true;fail(abortError());
    // These property callbacks belong to the original constructor, not us.
    // Removing them after disposal avoids marking freed textures for upload.
    for(const texture of textures)texture.image.onload=null;
    originalDispose.call(pass);
  }
  pass.dispose=dispose;
  const ready=new Promise((resolve,reject)=>{
    rejectReady=reject;
    if(signal?.aborted){fail(abortError());return;}
    const pending=new Set(textures);
    function loaded(texture){
      if(settled||disposed||!pending.has(texture))return;
      if(!(texture.image.naturalWidth>0)){fail(new Error('SMAA lookup image failed to decode.'));return;}
      texture.needsUpdate=true;pending.delete(texture);
      if(!pending.size){settled=true;cleanup();resolve(pass);}
    }
    if(signal){const abort=()=>fail(abortError());signal.addEventListener('abort',abort,{once:true});cleanups.push(()=>signal.removeEventListener('abort',abort));}
    timer=setTimeout(()=>fail(new Error('SMAA lookup images timed out.')),Math.max(1,Number.isFinite(timeoutMs)?timeoutMs:10000));
    for(const texture of textures){
      const image=texture.image,onLoad=()=>loaded(texture),onError=()=>fail(new Error('SMAA lookup image could not load.'));
      image.addEventListener('load',onLoad);image.addEventListener('error',onError);
      cleanups.push(()=>{image.removeEventListener('load',onLoad);image.removeEventListener('error',onError);});
      if(image.complete)loaded(texture);
      if(settled)break;
    }
  });
  // Disposal may happen before a loading caller attaches its await handler.
  // Keep cancellation handled without changing the original rejecting promise.
  ready.catch(()=>{});
  return {ready,dispose,get disposed(){return disposed;}};
}

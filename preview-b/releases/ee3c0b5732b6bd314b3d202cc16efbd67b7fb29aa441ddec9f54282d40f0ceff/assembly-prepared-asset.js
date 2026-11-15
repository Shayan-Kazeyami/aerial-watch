// Start independent preparation early, transfer ownership only when the scene can
// adopt it. Abandoned/late results are disposed exactly once, without unhandled
// promise rejections or changing the original error delivered to the caller.
export function createPreparedAsset({load,dispose=()=>{},signal}={}){
 if(typeof load!=='function')throw new TypeError('Asset loader required');
 const controller=new AbortController();let cancelled=false,taken=false,result=null,failed=false,failure;
 const reason=()=>controller.signal.reason||new DOMException('Prepared asset cancelled','AbortError');
 const abandon=()=>{if(cancelled)return;cancelled=true;controller.abort(signal?.reason||new DOMException('Prepared asset cancelled','AbortError'));if(result){const value=result;result=null;dispose(value);}signal?.removeEventListener('abort',abandon);};
 signal?.addEventListener('abort',abandon,{once:true});if(signal?.aborted)abandon();
 const outcome=Promise.resolve().then(()=>{controller.signal.throwIfAborted();return load(controller.signal);}).then(value=>{
  if(cancelled){dispose(value);return;}result=value;
  // The long-lived promise resolves without the asset. Only the transferable
  // result slot owns it; clearing that slot after take releases temporary GLTF data.
 },error=>{failed=true;failure=error;}).catch(error=>{failed=true;failure=error;});
 return {
  async take(){if(taken)throw new Error('Prepared asset already adopted');await outcome;if(cancelled)throw reason();if(failed)throw failure;if(taken)throw new Error('Prepared asset already adopted');taken=true;const value=result;result=null;signal?.removeEventListener('abort',abandon);return value;},
  dispose(){if(!taken)abandon();else signal?.removeEventListener('abort',abandon);}
 };
}

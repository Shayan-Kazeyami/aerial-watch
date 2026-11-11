// Start independent preparation early, transfer ownership only when the scene can
// adopt it. Abandoned/late results are disposed exactly once, without unhandled
// promise rejections or changing the original error delivered to the caller.
export function createPreparedAsset({load,dispose=()=>{},signal}={}){
 if(typeof load!=='function')throw new TypeError('Asset loader required');
 const controller=new AbortController();let cancelled=false,taken=false,result=null;
 const reason=()=>controller.signal.reason||new DOMException('Prepared asset cancelled','AbortError');
 const abandon=()=>{if(cancelled)return;cancelled=true;controller.abort(signal?.reason||new DOMException('Prepared asset cancelled','AbortError'));if(result){const value=result;result=null;dispose(value);}signal?.removeEventListener('abort',abandon);};
 signal?.addEventListener('abort',abandon,{once:true});if(signal?.aborted)abandon();
 const outcome=Promise.resolve().then(()=>{controller.signal.throwIfAborted();return load(controller.signal);}).then(value=>{
  if(cancelled){dispose(value);return {error:reason()};}result=value;return {value};
 },error=>({error})).catch(error=>({error}));
 return {
  async take(){if(taken)throw new Error('Prepared asset already adopted');const settled=await outcome;if(cancelled)throw reason();if('error' in settled)throw settled.error;if(taken)throw new Error('Prepared asset already adopted');taken=true;result=null;signal?.removeEventListener('abort',abandon);return settled.value;},
  dispose(){if(!taken)abandon();else signal?.removeEventListener('abort',abandon);}
 };
}

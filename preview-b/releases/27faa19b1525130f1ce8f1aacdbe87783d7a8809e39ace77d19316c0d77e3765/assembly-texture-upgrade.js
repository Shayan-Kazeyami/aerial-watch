// Private study: one in-flight upgrade. The installed texture remains owned by
// the caller. Prepared replacements are disposed unless the caller adopts them.
// adopt must be transactional: if it throws, it must restore all old bindings.
export function createTextureUpgrade({load,adopt,dispose,onError=()=>{}}){
 let generation=0,disposed=false,current=null;
 const cancel=()=>{generation++;current?.abort();current=null;};
 return {
  start(){
   if(disposed)throw new Error('Upgrade disposed');
   cancel();const id=generation, controller=new AbortController();current=controller;
   const job=Promise.resolve().then(()=>{if(controller.signal.aborted)throw controller.signal.reason;return load(controller.signal)}).then(texture=>{
    if(disposed||id!==generation||controller.signal.aborted){dispose(texture);return false;}
    try{adopt(texture);return true;}catch(error){dispose(texture);throw error;}
   }).catch(error=>{if(!disposed&&id===generation&&!controller.signal.aborted)onError(error);return false;});
   let onAbort;const interrupted=new Promise(resolve=>{onAbort=()=>resolve(false);controller.signal.addEventListener('abort',onAbort,{once:true});});
   return Promise.race([job,interrupted]).finally(()=>{controller.signal.removeEventListener('abort',onAbort);if(current===controller)current=null;});
  },
  cancel,
  dispose(){if(disposed)return;disposed=true;cancel();}
 };
}

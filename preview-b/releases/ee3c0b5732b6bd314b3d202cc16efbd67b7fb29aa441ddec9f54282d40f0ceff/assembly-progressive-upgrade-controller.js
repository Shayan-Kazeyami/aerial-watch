import {createTextureUpgrade} from './assembly-texture-upgrade.js';
// Explicit failed-only retry; never restarts an active attempt. Keep verified
// low payload only while initial/pending/failed, release on adoption or disposal.
export function createProgressiveUpgrade({lowBytes,fetchFull,decodeFull,adopt,onError=()=>{}}){
 if(!(lowBytes instanceof Uint8Array))throw TypeError('Verified low normal bytes required');
 let low=lowBytes,state='waiting',attempts=0,inFlight=null;
 const worker=createTextureUpgrade({
  load:async signal=>{const bytes=await fetchFull({low,signal});signal.throwIfAborted();return decodeFull(bytes,{signal});},
  adopt,
  dispose:texture=>texture.dispose(),
  onError:error=>{if(state!=='disposed'){state='failed';onError(error);}},
 });
 function start(){
  if(inFlight)return inFlight;
  state='upgrading';attempts++;
  const job=worker.start();
  inFlight=job.then(adopted=>{
   if(state!=='disposed'){
    if(adopted){state='full';low=null;}
    else state='failed';
   }
   return adopted;
  }).finally(()=>{inFlight=null;});
  return inFlight;
 }
 return {
  afterFirstSelectedFrame(){return state==='waiting'?start():null;},
  retry(){if(state==='disposed'||state==='full'||state==='waiting')return null;return inFlight??start();},
  snapshot(){return {state,attempts,inFlight:!!inFlight,retainedLowBytes:low?.byteLength??0};},
  dispose(){if(state==='disposed')return;state='disposed';low=null;worker.dispose();},
 };
}

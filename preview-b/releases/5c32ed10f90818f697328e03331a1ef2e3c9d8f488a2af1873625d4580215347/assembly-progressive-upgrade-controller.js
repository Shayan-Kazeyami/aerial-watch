import {createTextureUpgrade} from './assembly-texture-upgrade.js';
// A policy controller only. fetchFull, decodeFull, and adoption own their own
// resource cleanup and must honor cancellation; late decoded textures are disposed.
export function createProgressiveUpgrade({lowBytes,fetchFull,decodeFull,adopt,onError=()=>{}}){
 if(!(lowBytes instanceof Uint8Array))throw TypeError('Verified low normal bytes required');
 let low=lowBytes,started=false,disposed=false;
 const worker=createTextureUpgrade({load:async signal=>{const bytes=await fetchFull({low,signal});signal.throwIfAborted();return decodeFull(bytes,{signal});},adopt,dispose:t=>t.dispose(),onError});
 return {afterFirstSelectedFrame(){if(disposed||started)return null;started=true;const p=worker.start();p.finally(()=>{low=null});return p;},dispose(){if(disposed)return;disposed=true;low=null;worker.dispose();}};
}

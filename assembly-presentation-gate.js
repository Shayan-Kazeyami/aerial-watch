// Presentation readiness is separate from baseline/runtime readiness.
// Asset deadlines remain owned by assembly-loading.js; this gate owns no timers.
export function createPresentationGate({enabled=false,onChange=()=>{}}={}){
 const states=new Map(['baseline','proposal','premiumFace','leather'].map(key=>[key,'pending']));
 const errors=new Map();let disposed=false,fatal='',revealed=false,revision=0,renderedRevision=-1;
 function snapshot(){
  const pending=[...states].filter(([,value])=>value==='pending').map(([key])=>key);
  const warnings=[...errors].map(([asset,message])=>({asset,message}));
  const canRender=!disposed&&!fatal&&(!enabled||revealed||pending.length===0);
  const interactive=!disposed&&!fatal&&(!enabled||revealed);
  const phase=disposed?'disposed':fatal?'error':!enabled?'legacy':pending.length?'preparing':renderedRevision<revision?'rendering':warnings.length?'degraded':'ready';
  const message=fatal||(!enabled?'':phase==='preparing'?'Preparing the selected dial and leather. Static reference preview.':phase==='rendering'?(revealed?'Updating the selected watch…':'Lighting the selected watch. Static reference preview.'):warnings.length?'Available watch ready with missing design assets: '+warnings.map(w=>w.asset).join(', ')+'. Reload to retry.':'Selected watch ready.');
  return {enabled,phase,interactive,canRender,pending,warnings,message};
 }
 function emit(){if(!disposed&&enabled)onChange(snapshot());}
 return {snapshot,settle(asset,error){if(disposed||fatal||!states.has(asset))return;states.set(asset,error?'failed':'ready');if(error)errors.set(asset,String(error.message||error));else errors.delete(asset);revision++;emit();},rendered(){if(disposed||fatal||!snapshot().canRender)return false;const changed=!revealed||renderedRevision!==revision;revealed=true;renderedRevision=revision;if(changed)emit();return true;},fail(message){if(disposed)return;fatal=String(message);emit();},dispose(){disposed=true;},publish:emit};
}

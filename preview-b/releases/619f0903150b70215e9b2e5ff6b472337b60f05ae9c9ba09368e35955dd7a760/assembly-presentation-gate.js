// Presentation readiness is separate from baseline/runtime readiness.
// Asset deadlines remain owned by assembly-loading.js; this gate owns no timers.
export function createPresentationGate({enabled=false,extraAssets=[],onChange=()=>{}}={}){
 const states=new Map(['baseline','proposal','premiumFace','leather',...extraAssets].map(key=>[key,'pending']));
 const reason=error=>String(error?.message||error).replace(/https?:\/\/[^\s)]+/gi,'[asset URL]').replace(/[\x00-\x1f\x7f<>]/g,' ').replace(/\s+/g,' ').trim().slice(0,180);
 const errors=new Map();let disposed=false,fatal='',revealed=false,revision=0,renderedRevision=-1;
 function snapshot(){
  const pending=[...states].filter(([,value])=>value==='pending').map(([key])=>key);
  const failedAssets=[...states].filter(([,value])=>value==='failed').map(([key])=>key);
  const warnings=[...errors].map(([asset,message])=>({asset,message}));
  // A baseline is not a substitute for the selected design. Never reveal it
  // after a failed initial design load, even when all requests have settled.
  const blocked=failedAssets.length>0;
  const canRender=!disposed&&!fatal&&(!enabled||revealed||(!blocked&&pending.length===0));
  const interactive=!disposed&&!fatal&&(!enabled||revealed);
  const phase=disposed?'disposed':fatal?'error':!enabled?'legacy':blocked&&!revealed?'asset-error':pending.length?'preparing':renderedRevision<revision?'rendering':warnings.length?'degraded':'ready';
  const message=fatal||(!enabled?'':phase==='asset-error'?'The selected watch could not load ('+failedAssets.map(asset=>asset+': '+errors.get(asset)).join('; ')+'). Reload to retry.':phase==='preparing'?'Preparing the selected dial and leather.':phase==='rendering'?(revealed?'Updating the selected watch…':'Lighting the selected watch.'):warnings.length?'The selected watch remains available. Additional assets could not load: '+warnings.map(w=>w.asset).join(', ')+'. Reload to retry.':'Selected watch ready.');
  return {enabled,phase,interactive,canRender,pending,failedAssets,warnings,message};
 }
 function emit(){if(!disposed&&enabled)onChange(snapshot());}
 return {
  snapshot,
  settle(asset,error){
   if(disposed||fatal||!states.has(asset))return;
   // A failed refresh must not downgrade an already installed good asset.
   if(!error||states.get(asset)!=='ready')states.set(asset,error?'failed':'ready');
   if(error)errors.set(asset,reason(error));else errors.delete(asset);
   revision++;emit();
  },
  retry(asset){if(disposed||fatal||!states.has(asset))return;if(states.get(asset)!=='ready')states.set(asset,'pending');errors.delete(asset);revision++;emit();},
  rendered(){if(disposed||fatal||!snapshot().canRender)return false;const changed=!revealed||renderedRevision!==revision;revealed=true;renderedRevision=revision;if(changed)emit();return true;},
  fail(message){if(disposed)return;fatal=String(message);emit();},dispose(){disposed=true;},publish:emit
 };
}

const RELEASE='./preview-b/releases/1b013b90cdd2d448fbe5c88bc90e28786ba3424600fb43d35ddabed0707d9158/atelier-preview.html';
// These are preparation milestones, not measured byte/time percentages. The UI
// intentionally has no numeric percentage and exposes the estimate to AT.
const WEIGHTS={baseline:25,proposal:10,premiumFace:15,leather:30,antialias:6};
export function createLoadingProgress(){
 let highest=0;
 return {
  update(snapshot,{failed=false,ready=false,documentLoaded=false}={}){
   if(failed||['error','asset-error','disposed'].includes(snapshot?.phase))return {state:'error',value:highest};
   if(ready||snapshot?.interactive){highest=100;return {state:'ready',value:100};}
   let target=documentLoaded?6:2;
   if(snapshot?.enabled&&Array.isArray(snapshot.pending)){
    target=6;for(const [name,weight] of Object.entries(WEIGHTS))if(!snapshot.pending.includes(name)&&!snapshot.failedAssets?.includes(name))target+=weight;
   }
   highest=Math.max(highest,Math.min(92,target));return {state:'loading',value:highest};
  },
  reset(){highest=0;}
 };
}
export function startLoadingBar({frame,panel,bar,fill,label,win=window}){
 const progress=createLoadingProgress();let timer=null,finishTimer=null,detach=()=>{},stopped=false,finished=false,finishing=false;
 const cancelFinish=()=>{if(finishTimer!==null)win.clearTimeout(finishTimer);finishTimer=null;finishing=false;};
 const render=(snapshot,flags)=>{
  const state=progress.update(snapshot,flags);panel.dataset.state=state.state;
  if(state.state==='error'){cancelFinish();panel.hidden=true;return;}
  if(finished)return;
  panel.hidden=false;label.textContent=state.state==='ready'?'Watch ready':'Loading watch…';
  fill.style.transform=`scaleX(${state.value/100})`;
  bar.setAttribute('aria-valuenow',String(state.value));bar.setAttribute('aria-valuetext',state.state==='ready'?'Watch ready':'Loading watch, estimated preparation progress');
  if(state.state==='ready'&&!finishing){finishing=true;finishTimer=win.setTimeout(()=>{panel.hidden=true;finished=true;finishTimer=null;finishing=false;},win.matchMedia?.('(prefers-reduced-motion: reduce)').matches?100:700);}
 };
 const clear=()=>{if(timer!==null)win.clearInterval(timer);timer=null;cancelFinish();detach();detach=()=>{};};
 const attach=()=>{
  clear();if(stopped)return;progress.reset();finished=false;render(null,{documentLoaded:true});
  try{
   const child=frame.contentWindow,doc=frame.contentDocument;if(!doc)return;
   let latest=child.assemblyInspect?.().presentation;
   const sample=()=>{if(stopped)return;try{
    const flags={documentLoaded:true,failed:doc.body?.dataset.failed==='true'||doc.body?.dataset.presentation==='asset-error',ready:doc.body?.dataset.ready==='true'};
    render(latest,flags);
    if((flags.ready||latest?.interactive)&&timer!==null){win.clearInterval(timer);timer=null;}
   }catch{cancelFinish();panel.hidden=true;}};
   const onState=event=>{latest=event.detail;sample();};
   doc.addEventListener('atelier:presentation-state',onState);detach=()=>doc.removeEventListener('atelier:presentation-state',onState);
   timer=win.setInterval(sample,250);sample();
   doc.dispatchEvent(new child.CustomEvent('atelier:request-presentation-state'));
  }catch{cancelFinish();panel.hidden=true;}
 };
 const onHide=()=>clear();const onShow=event=>{if(event.persisted)attach();};
 const stop=()=>{stopped=true;clear();frame.removeEventListener('load',attach);win.removeEventListener('pagehide',onHide);win.removeEventListener('pageshow',onShow);};
 frame.addEventListener('load',attach);win.addEventListener('pagehide',onHide);win.addEventListener('pageshow',onShow);render(null);
 const entry=new URL(RELEASE,win.location.href);entry.search=win.location.search;entry.hash=win.location.hash;frame.src=entry.href;
 return stop;
}
if(typeof document!=='undefined')startLoadingBar({frame:document.getElementById('watch-viewer'),panel:document.getElementById('watch-loading'),bar:document.getElementById('watch-progress'),fill:document.getElementById('watch-progress-fill'),label:document.getElementById('watch-loading-label')});

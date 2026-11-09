const RELEASE='./preview-b/releases/dca5c072be394554f4ae293b0324e61a38f5b548cbab721f99f8cf80e13298bc/atelier-preview.html';
const CORE=['baseline','proposal','premiumFace','leather'];
export function loadingState(snapshot,{failed=false,ready=false,antialias=true}={}){
 if(failed||['error','asset-error','disposed'].includes(snapshot?.phase))return {hidden:true,state:'error'};
 if(ready||snapshot?.interactive)return {hidden:true,state:'ready'};
 if(!snapshot?.enabled||!Array.isArray(snapshot.pending))return {hidden:false,state:'connecting',label:'Opening the watch studio',detail:'Preparing the viewer…',value:null};
 const steps=new Set([...CORE,...(antialias?['antialias']:[]),...snapshot.pending,...(snapshot.failedAssets||[])]);
 const total=steps.size+1; // The first successfully composed frame is its own step.
 const complete=steps.size-snapshot.pending.length;
 return {hidden:false,state:'preparing',value:complete,total,label:snapshot.phase==='rendering'?'Lighting the watch':'Preparing the watch',detail:`${complete} of ${total} preparation steps complete`};
}
export function startLoadingBar({frame,panel,bar,label,detail,win=window}){
 let timer=null,detach=()=>{},stopped=false;
 const render=(snapshot,flags)=>{const state=loadingState(snapshot,flags);panel.hidden=state.hidden;panel.dataset.state=state.state;if(state.hidden)return;
 label.textContent=state.label;detail.textContent=state.detail;
 if(state.value===null){bar.removeAttribute('value');bar.removeAttribute('aria-valuetext');}
 else{bar.max=state.total;bar.value=state.value;bar.setAttribute('aria-valuetext',state.detail);}
 };
 const clear=()=>{if(timer!==null)win.clearInterval(timer);timer=null;detach();detach=()=>{};};
 const attach=()=>{
  clear();if(stopped)return;render(null);
  try{
   const child=frame.contentWindow,doc=frame.contentDocument;
   if(!doc)return;
   let latest=child.assemblyInspect?.().presentation;
   const sample=()=>{if(stopped)return;try{
    const body=doc.body;const state=latest;
    const flags={antialias:new URL(child.location.href).searchParams.get('antialias')==='smaa',failed:body?.dataset.failed==='true'||body?.dataset.presentation==='asset-error',ready:body?.dataset.ready==='true'};
    render(state,flags);
    // Keep listening for a retry on this document; no periodic work after ready.
    if((flags.ready||state?.interactive)&&timer!==null){win.clearInterval(timer);timer=null;}
   }catch{panel.hidden=true;}};
   const onState=event=>{latest=event.detail;sample();};
   doc.addEventListener('atelier:presentation-state',onState);
   detach=()=>doc.removeEventListener('atelier:presentation-state',onState);
   timer=win.setInterval(sample,250);sample();
   // Replays current readiness even if the initial events preceded iframe load.
   doc.dispatchEvent(new child.CustomEvent('atelier:request-presentation-state'));
  }catch{panel.hidden=true;}
 };
 const stop=()=>{stopped=true;clear();frame.removeEventListener('load',attach);};
 frame.addEventListener('load',attach);win.addEventListener('pagehide',()=>{clear();},{once:false});
 win.addEventListener('pageshow',event=>{if(event.persisted)attach();});
 render(null);
 const entry=new URL(RELEASE,win.location.href);entry.search=win.location.search;entry.hash=win.location.hash;frame.src=entry.href;
 return stop;
}
if(typeof document!=='undefined')startLoadingBar({frame:document.getElementById('watch-viewer'),panel:document.getElementById('watch-loading'),bar:document.getElementById('watch-progress'),label:document.getElementById('watch-loading-label'),detail:document.getElementById('watch-loading-detail')});

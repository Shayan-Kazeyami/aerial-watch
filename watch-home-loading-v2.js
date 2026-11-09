const RELEASE='./preview-b/releases/457c5eba8f27ffecf7710adc2fb3ef10a2ac326af781f19232fad75328dc2bd4/atelier-preview.html';
export function loadingState(snapshot,{failed=false,ready=false}={}){
 if(failed||['error','asset-error','disposed'].includes(snapshot?.phase))return {hidden:true,state:'error'};
 if(ready||snapshot?.interactive)return {hidden:true,state:'ready'};
 // Indeterminate by design: asset milestones are not byte or time percentages.
 return {hidden:false,state:'loading',label:'Loading watch…',detail:'',value:null};
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
    const flags={failed:body?.dataset.failed==='true'||body?.dataset.presentation==='asset-error',ready:body?.dataset.ready==='true'};
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

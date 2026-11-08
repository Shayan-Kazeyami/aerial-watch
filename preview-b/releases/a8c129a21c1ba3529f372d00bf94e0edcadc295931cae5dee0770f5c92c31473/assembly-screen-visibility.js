// Only suspend after an observer reports the viewer entirely outside the viewport.
// Absence of IntersectionObserver leaves the existing always-visible policy intact.
export function observeViewerVisibility(element,{Observer=globalThis.IntersectionObserver,onChange=()=>{}}={}){
 let visible=true,disposed=false,observer=null;
 if(Observer&&element){observer=new Observer(entries=>{if(disposed)return;let entry;for(let i=entries.length-1;i>=0;i--){if(entries[i].target===element){entry=entries[i];break;}}if(!entry)return;const next=!!entry.isIntersecting;if(next!==visible){visible=next;onChange(visible);}},{threshold:0});observer.observe(element);}
 return {get visible(){return visible;},dispose(){if(disposed)return;disposed=true;observer?.disconnect();}};
}

export function skipViewerFrame({hidden,failed,contextLost,viewportVisible,recording}){return !!(hidden||failed||contextLost||(!viewportVisible&&!recording));}

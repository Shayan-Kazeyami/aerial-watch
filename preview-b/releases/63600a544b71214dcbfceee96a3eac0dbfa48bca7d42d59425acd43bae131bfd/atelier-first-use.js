// One non-blocking touch cue. No scene render loop, focus change or layout resize.
export function createFirstUseGuide({canvas,host,document:doc=canvas.ownerDocument,window:win=doc.defaultView,duration=8000}) {
 const key='aerial.touch-guide.v1';let seen=false,visible=false,timer=null,disposed=false,start=null,lastReady=false;
 try{seen=win.localStorage.getItem(key)==='done';}catch{}
 const cue=doc.createElement('p');cue.className='atelier-first-use';cue.hidden=true;cue.setAttribute('role','status');cue.textContent='Drag to explore · Pinch to zoom';host.append(cue);
 const listeners=[];const listen=(target,name,fn,options)=>{target.addEventListener(name,fn,options);listeners.push(()=>target.removeEventListener(name,fn,options));};
 const clear=()=>{if(timer!==null)win.clearTimeout(timer);timer=null;};
 function hide(){clear();visible=false;cue.hidden=true;}
 function complete(){if(seen)return;seen=true;hide();try{win.localStorage.setItem(key,'done');}catch{}}
 function update(ready){
  lastReady=!!ready;
  if(disposed||seen||!ready||doc.hidden||!win.matchMedia('(pointer: coarse)').matches){hide();return;}
  if(visible)return;visible=true;cue.hidden=false;timer=win.setTimeout(complete,duration);
 }
 listen(canvas,'pointerdown',e=>{if(e.pointerType==='touch'){if(start&&start.id!==e.pointerId)complete();start={id:e.pointerId,x:e.clientX,y:e.clientY};}},{passive:true});
 listen(canvas,'pointermove',e=>{if(start&&e.pointerId===start.id&&Math.hypot(e.clientX-start.x,e.clientY-start.y)>=8)complete();},{passive:true});
 for(const name of ['pointerup','pointercancel'])listen(canvas,name,e=>{if(start?.id===e.pointerId)start=null;},{passive:true});
 listen(doc,'visibilitychange',()=>{if(doc.hidden){start=null;hide();}else update(lastReady);});
 listen(win,'pagehide',()=>{start=null;hide();});listen(win,'pageshow',()=>update(lastReady));
 return {update,snapshot:()=>({seen,visible}),dispose(){if(disposed)return;disposed=true;hide();listeners.forEach(off=>off());cue.remove();}};
}

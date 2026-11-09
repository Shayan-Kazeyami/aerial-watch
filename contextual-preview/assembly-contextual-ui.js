// Object-local actions reuse existing runtime controls; no independent state.
export function contextKind(data={}) {
 const id=String(data.assemblyId||'');
 if(id==='CROWN')return 'crown';
 if(/STRAP|BUCKLE|KEEPER/.test(id))return 'strap';
 if(/CASE|CRYSTAL/.test(id))return 'case';
 return 'component';
}
export function clampCard(x,y,width,height,viewportWidth,viewportHeight){
 return {x:Math.max(8,Math.min(x+18,viewportWidth-width-8)),y:Math.max(8,Math.min(y+18,viewportHeight-height-8))};
}
export function createContextualUI({canvas,pick,describe,available=()=>true,document:doc=canvas.ownerDocument,window:win=doc.defaultView}){
 const card=doc.createElement('section');card.className='watch-object-actions';card.hidden=true;card.setAttribute('aria-label','Object interactions');
 const heading=doc.createElement('strong'),hint=doc.createElement('span'),actions=doc.createElement('div'),close=doc.createElement('button');close.type='button';close.textContent='×';close.setAttribute('aria-label','Dismiss object interactions');close.className='watch-object-close';card.append(heading,hint,actions,close);doc.body.append(card);
 const style=doc.createElement('style');style.textContent=`.watch-object-actions{position:fixed;z-index:80;max-width:min(280px,calc(100vw - 16px));padding:14px 34px 14px 14px;border:1px solid #ffffff30;border-radius:14px;background:#17201ff0;color:#f3f0e7;box-shadow:0 12px 40px #0005;backdrop-filter:blur(14px);font:12px/1.4 system-ui,sans-serif;pointer-events:auto}.watch-object-actions[hidden]{display:none}.watch-object-actions strong,.watch-object-actions span{display:block}.watch-object-actions span{color:#c0c9c2;margin:5px 0 9px}.watch-object-actions div{display:flex;flex-wrap:wrap;gap:6px}.watch-object-actions button{font:inherit;color:inherit;background:#ffffff12;border:1px solid #ffffff24;border-radius:8px;padding:8px 10px;min-height:36px;cursor:pointer}.watch-object-actions button:hover{background:#ffffff28}.watch-object-actions button:focus-visible{outline:2px solid #e1c694;outline-offset:2px}.watch-object-actions .watch-object-close{position:absolute;right:4px;top:3px;padding:4px;min-height:28px;width:28px;border:0;background:none}@media(pointer:coarse){.watch-object-actions button{min-height:44px}}`;
 doc.head.append(style);
 let current=null,point=null,touch=false,down=null,timer=null,pickTimer=null,lastPick=0,pending=null,raf=0,disposed=false;
 const listeners=[];const listen=(target,event,handler,options)=>{target.addEventListener(event,handler,options);listeners.push(()=>target.removeEventListener(event,handler,options));};
 function hide(){clearTimeout(timer);current=null;card.hidden=true;canvas.style.cursor='';}
 function place(){if(!point)return;const rect=card.getBoundingClientRect(),p=clampCard(point.x,point.y,rect.width,rect.height,win.innerWidth,win.innerHeight);card.style.left=p.x+'px';card.style.top=p.y+'px';}
 function show(hit,event){if(!hit||!available()){hide();return;}clearTimeout(timer);point={x:event.clientX,y:event.clientY};if(current!==hit||card.hidden){current=hit;const item=describe(hit);if(!item?.actions?.length){hide();return;}heading.textContent=item.label;hint.textContent=item.hint||'Choose an action for this part.';actions.replaceChildren();for(const action of item.actions){const button=doc.createElement('button');button.type='button';button.textContent=action.label;button.onclick=()=>{if(!available()){hide();return;}action.run();hide();};actions.append(button);}}card.hidden=false;place();}
 function scheduleHide(){clearTimeout(timer);timer=setTimeout(()=>{if(!card.matches(':hover')&&!card.contains(doc.activeElement))hide();},350);}
 function process(){raf=0;if(disposed||!pending||down)return;const event=pending;pending=null;if(!available()){hide();return;}lastPick=win.performance.now();const hit=pick(event);if(hit)show(hit,event);else scheduleHide();}
 listen(canvas,'pointermove',event=>{if(event.pointerType==='touch'||event.buttons||down)return;touch=false;pending={clientX:event.clientX,clientY:event.clientY};clearTimeout(pickTimer);const delay=Math.max(0,80-(win.performance.now()-lastPick));if(delay){pickTimer=setTimeout(()=>{if(!disposed&&!raf)raf=win.requestAnimationFrame(process);},delay);}else if(!raf)raf=win.requestAnimationFrame(process);});
 listen(canvas,'pointerdown',event=>{down={x:event.clientX,y:event.clientY,id:event.pointerId};hide();},true);
 listen(canvas,'pointerup',event=>{const start=down;down=null;if(disposed||!available())return;if(!start||start.id!==event.pointerId||event.pointerType!=='touch'||Math.hypot(start.x-event.clientX,start.y-event.clientY)>5)return;touch=true;show(pick(event),event);},true);
 listen(canvas,'pointercancel',()=>{down=null;hide();},true);
 listen(canvas,'pointerleave',()=>{if(!touch)scheduleHide();});listen(card,'pointerenter',()=>clearTimeout(timer));listen(card,'pointerleave',()=>{if(!touch)scheduleHide();});
 listen(doc,'pointerdown',event=>{if(!card.contains(event.target)&&event.target!==canvas)hide();});
 listen(doc,'keydown',event=>{if(event.key==='Escape'){const focused=card.contains(doc.activeElement);hide();if(focused)canvas.focus({preventScroll:true});}});
 listen(win,'blur',hide);listen(win,'resize',hide);listen(canvas,'wheel',hide,{passive:true});listen(doc,'visibilitychange',()=>{if(doc.hidden)hide();});close.onclick=hide;
 return {hide,dispose(){disposed=true;hide();clearTimeout(pickTimer);if(raf)win.cancelAnimationFrame(raf);listeners.forEach(off=>off());card.remove();style.remove();}};
}

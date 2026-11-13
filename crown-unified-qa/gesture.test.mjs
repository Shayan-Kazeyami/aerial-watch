import test from 'node:test';import assert from 'node:assert/strict';
import {createCrownHotspot} from './assembly-crown-hotspot.js';
class Element extends EventTarget{
 constructor(){super();this.attrs=new Map();this.style={setProperty(){}};this.captured=new Set();this.hidden=false;}
 setAttribute(k,v){this.attrs.set(k,String(v))}removeAttribute(k){this.attrs.delete(k)}append(){}remove(){}querySelectorAll(){return []}
 setPointerCapture(id){this.captured.add(id)}hasPointerCapture(id){return this.captured.has(id)}releasePointerCapture(id){this.captured.delete(id)}focus(){}
}
function setup(){
 const doc=new Element(),win=new Element(),canvas=new Element(),frames=new Map(),timers=new Map();let time=0,id=0,available=true,anchor=true,pulled=false,turns=[],starts=0,ends=0,cancels=0,toggles=0;
 doc.createElement=()=>new Element();doc.body=new Element();doc.head=new Element();doc.defaultView=win;canvas.ownerDocument=doc;doc.hidden=false;
 win.matchMedia=()=>({matches:false});win.requestAnimationFrame=fn=>{frames.set(++id,fn);return id};win.cancelAnimationFrame=id=>frames.delete(id);win.setTimeout=fn=>{timers.set(++id,fn);return id};win.clearTimeout=id=>timers.delete(id);
 const h=createCrownHotspot({canvas,available:()=>available,getAnchor:()=>anchor?({x:100,y:100}):null,getPulled:()=>pulled,now:()=>time,onTurn:d=>turns.push(d),onToggle:()=>{toggles++;pulled=!pulled},onCancel:()=>cancels++,onGestureStart:()=>starts++,onGestureEnd:()=>ends++});
 const event=(y=100,pointerId=1)=>({button:0,pointerId,clientY:y,preventDefault(){},stopPropagation(){}});
 return {h,canvas,doc,win,event,turns,frames,timers,tick(ms=16){time+=ms;const fs=[...frames.values()];frames.clear();fs.forEach(f=>f(time));},hideAnchor(){anchor=false},disable(){available=false},stats:()=>({starts,ends,cancels,toggles})};
}
test('direct and dot share stationary displaced rate, reverse and dead zone',()=>{for(const direct of [false,true]){const f=setup();f.h.beginPointer(f.event(),direct?f.canvas:undefined);f.h.movePointer(f.event(78));for(let i=0;i<10;i++)f.tick(100);assert.equal(f.turns.reduce((a,b)=>a+b,0),120);f.h.movePointer(f.event(122));f.tick(100);assert.equal(f.turns.at(-1),-12);f.h.movePointer(f.event(100));const n=f.turns.length;f.tick(100);assert.equal(f.turns.length,n);f.h.endPointer(f.event());f.tick();assert.equal(f.turns.length,n);assert.equal(f.stats().toggles,0);assert.equal(f.stats().ends,1);}});
test('tap toggles once, duplicate release and unrelated pointer are ignored',()=>{const f=setup();assert.equal(f.h.beginPointer(f.event(),f.canvas),true);assert.equal(f.h.beginPointer(f.event(100,2),f.canvas),false);assert.equal(f.h.endPointer(f.event(100,2)),false);assert.equal(f.h.endPointer(f.event()),true);assert.equal(f.h.endPointer(f.event()),false);assert.equal(f.stats().toggles,1);assert.equal(f.canvas.captured.size,0);});
test('cancel clears RAF, timer, pointer capture and ownership, without toggling',()=>{const f=setup();f.h.beginPointer(f.event(),f.canvas);f.h.movePointer(f.event(78));f.tick();f.h.cancel();f.h.cancel();const n=f.turns.length;f.tick(100);assert.equal(f.turns.length,n);assert.equal(f.frames.size,0);assert.equal(f.timers.size,0);assert.equal(f.canvas.captured.size,0);assert.deepEqual(f.stats(),{starts:1,ends:1,cancels:1,toggles:0});});
for(const reason of ['blur','hidden','unavailable','dispose'])test(reason+' stops held gesture',()=>{const f=setup();f.h.beginPointer(f.event(),f.canvas);f.h.movePointer(f.event(78));f.tick();if(reason==='blur')f.win.dispatchEvent(new Event('blur'));if(reason==='hidden'){f.doc.hidden=true;f.doc.dispatchEvent(new Event('visibilitychange'));}if(reason==='unavailable'){f.disable();f.tick();}if(reason==='dispose')f.h.dispose();const n=f.turns.length;f.tick(100);assert.equal(f.turns.length,n);assert.equal(f.stats().ends,1);assert.equal(f.stats().toggles,0);assert.equal(f.canvas.captured.size,0);});
test('readiness rejects entry and cancelled pointer never toggles',()=>{const f=setup();f.h.beginPointer(f.event(),f.canvas);f.h.endPointer(f.event(),true);assert.equal(f.stats().toggles,0);f.disable();assert.equal(f.h.beginPointer(f.event(),f.canvas),false);});

test('captured direct mesh hold survives unavailable dot anchor but not unavailable scene',()=>{const f=setup();f.h.beginPointer(f.event(),f.canvas);f.h.movePointer(f.event(78));f.hideAnchor();f.h.update();f.tick(100);assert.equal(f.turns.at(-1),12);assert.equal(f.stats().ends,0);f.disable();f.h.update();assert.equal(f.stats().ends,1);});
test('dot hold cancels when its anchor disappears',()=>{const f=setup();f.h.beginPointer(f.event());f.hideAnchor();f.h.update();assert.equal(f.stats().ends,1);});
test('actual integration callbacks restore previously enabled and disabled orbit state exactly',async()=>{
 const {readFile}=await import('node:fs/promises'),source=await readFile(new URL('./assembly-review.js',import.meta.url),'utf8');
 const start=source.match(/onGestureStart\(\)\{([^}]+)\}/)[1],end=source.match(/onGestureEnd\(\)\{([^}]+)\}/)[1];
 for(const enabled of [true,false]){
  const state=new Function('initial',`let controls={enabled:initial},crownControlsEnabled=null,down=[1,2],dirty=false;return {start(){${start}},end(){${end}},snapshot(){return {enabled:controls.enabled,saved:crownControlsEnabled,down,dirty}}}`)(enabled);
  state.start();assert.equal(state.snapshot().enabled,false);assert.equal(state.snapshot().down,null);
  state.end();assert.equal(state.snapshot().enabled,enabled);assert.equal(state.snapshot().saved,null);assert.equal(state.snapshot().dirty,true);
  state.end();assert.equal(state.snapshot().enabled,enabled);
 }
});

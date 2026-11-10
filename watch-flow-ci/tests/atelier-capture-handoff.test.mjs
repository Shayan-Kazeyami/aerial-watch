import {test} from 'node:test';import assert from 'node:assert/strict';import vm from 'node:vm';import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../atelier-preview.js',import.meta.url),'utf8'),block=source.split('// BEGIN full-stage capture handoff.')[1].split('// END full-stage capture handoff.')[0];
function harness(){
 const timers=new Map(),listeners=new Map(),docListeners=new Map(),calls=[],requests=[];let serial=0;
 const els={context:{hidden:false},stage:{getBoundingClientRect:()=>({width:400,height:380})},'assembly-canvas':{width:800,height:760},status:{textContent:''},'record-scene':{textContent:'Record 8s video',getAttribute:()=>null},'capture-scene':{textContent:'Save PNG image',getAttribute:()=>null}};
 const document={body:{dataset:{panelOpen:'false'}},createElement:()=>({style:{},setAttribute(){}}),querySelector:()=>({append:n=>els[n.id]=n}),addEventListener:(k,f)=>docListeners.set(k,f),removeEventListener:k=>docListeners.delete(k),dispatchEvent:e=>{requests.push(e);docListeners.get(e.type)?.(e);}};
 const context=vm.createContext({$:id=>els[id],document,panelMedia:{matches:true},taskStatusBaseline:'old',CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail;}},window:{addEventListener:(k,f)=>listeners.set(k,f),removeEventListener:k=>listeners.delete(k)},setTimeout:(fn,ms)=>{timers.set(++serial,{fn,ms});return serial;},clearTimeout:k=>timers.delete(k),liveTarget:id=>els[id]?.disabled?null:els[id],proxy:id=>{calls.push(id);return true;},updateText:(id,text)=>els[id].textContent=text,closeContext:()=>els.context.hidden=true});vm.runInContext(block,context);
 const poll=async()=>{const [id,t]=[...timers].find(([,t])=>t.ms===50)||[];assert.ok(t,'poll scheduled');timers.delete(id);t.fn();await Promise.resolve();};
 const ack=(requestId=requests.at(-1)?.detail.requestId,dimensions=[400,380,800,760])=>docListeners.get('atelier:capture-frame-rendered')?.({detail:{requestId,dimensions}});
 return {context,els,timers,listeners,docListeners,calls,requests,document,poll,ack,start:id=>vm.runInContext(`captureAtFullStage('${id||'capture-scene'}')`,context)};
}
test('correct geometry can start after one actual render even with no RAF samples',async()=>{const h=harness(),p=h.start('record-scene');await h.poll();await h.poll();assert.equal(h.requests.length,1);assert.equal(h.calls.length,0);h.ack();await p;assert.deepEqual(h.calls,['record-scene']);assert.equal(h.timers.size,0);assert.equal(h.docListeners.size,0);});
test('stable geometry alone cannot authorize capture; wrong request or dimensions rejected',async()=>{const h=harness(),p=h.start();await h.poll();await h.poll();h.ack(999);assert.equal(h.calls.length,0);h.ack(undefined,[400,380,800,394]);assert.equal(h.calls.length,0);for(let i=0;i<3;i++)await h.poll();h.ack();await p;assert.deepEqual(h.calls,['capture-scene']);});
test('compact canvas never requests render or captures until resize completes',async()=>{const h=harness();h.els['assembly-canvas'].height=394;const p=h.start();for(let i=0;i<4;i++)await h.poll();assert.equal(h.requests.length,0);h.els['assembly-canvas'].height=760;for(let i=0;i<3;i++)await h.poll();h.ack();await p;assert.equal(h.calls.length,1);});
test('resize after request rejects stale rendered signature and requests fresh frame',async()=>{const h=harness(),p=h.start();await h.poll();await h.poll();h.els.stage.getBoundingClientRect=()=>({width:400,height:400});h.els['assembly-canvas'].height=800;h.ack();assert.equal(h.calls.length,0);for(let i=0;i<3;i++)await h.poll();h.ack(undefined,[400,400,800,800]);await p;assert.equal(h.requests.length,2);});
test('reentry ignored; cancelled handoff cannot consume late acknowledgement',async()=>{const h=harness(),p=h.start();await h.start();await h.poll();await h.poll();const old=h.requests[0].detail.requestId;h.els.context.hidden=false;await h.poll();await p;assert.equal(h.calls.length,0);assert.equal(h.docListeners.size,0);const next=h.start();await h.poll();await h.poll();h.ack(old);assert.equal(h.calls.length,0);h.ack();await next;assert.equal(h.calls.length,1);});
test('timeout/pagehide clean timers and listeners without forwarding',async()=>{for(const mode of ['timeout','pagehide']){const h=harness(),p=h.start();await h.poll();await h.poll();if(mode==='timeout')[...h.timers.values()].find(t=>t.ms===60000).fn();else h.listeners.get('pagehide')();await p;assert.equal(h.calls.length,0);assert.equal(h.timers.size,0);assert.equal(h.docListeners.size,0);assert.equal(h.listeners.size,0);}});
test('legacy stop forwards immediately without a readiness wait',async()=>{const h=harness();h.els['record-scene'].textContent='Stop recording';await h.start('record-scene');assert.deepEqual(h.calls,['record-scene']);assert.equal(h.requests.length,0);});
test('runtime acknowledges only after real composer render; request forces dirty without changing quality/motion',()=>{const runtime=readFileSync(new URL('../../preview-b/releases/99d5275244fdabbc301fba262d59e612e7f511121e5e79a5dae5bf936e222e75/assembly-review.js',import.meta.url),'utf8');const start=runtime.indexOf('composer.render();renderedFrames++');assert.ok(start>=0);const ack=runtime.indexOf("'atelier:capture-frame-rendered'",start);assert.ok(ack>start);const handler=runtime.slice(runtime.indexOf('const requestCaptureFrame='),runtime.indexOf("document.addEventListener('atelier:request-capture-frame'"));assert.match(handler,/dirty=true/);assert.doesNotMatch(handler,/quality\s*=|clock\.|animate|setRunning/);});

test('JSON retains direct mapping and export status mirrors runtime errors after closing without camera writes',()=>{
 assert.match(source,/if\(\['capture-scene','record-scene'\]\.includes\(el.dataset.proxy\)\)/);
 assert.doesNotMatch(block,/controls\.target|camera\.|setMode\(/);
 assert.match(source,/if\(exportNoticeActive\)showExportNotice\(exportNoticeMessage\?\?presentationMessage\)/);
 assert.match(block,/exportNoticeMessage=null;taskStatusBaseline=null;if\(!proxy\(id\)\)/);
});


test('visual export feedback hides behind an open tool panel and returns only when closed',()=>{
 const h=harness();
 vm.runInContext("exportNoticeActive=true;showExportNotice('PNG download requested.');",h.context);
 assert.equal(h.els['atelier-export-notice'].hidden,true);
 h.els.context.hidden=true;vm.runInContext("showExportNotice('PNG download requested.');",h.context);
 assert.equal(h.els['atelier-export-notice'].hidden,false);
 h.els.context.hidden=false;vm.runInContext("showExportNotice('Save an image or restore this view.');",h.context);
 assert.equal(h.els['atelier-export-notice'].hidden,true);
 assert.match(source,/updateText\('atelier-panel-status',presentationMessage\)/);
});

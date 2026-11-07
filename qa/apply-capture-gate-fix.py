from pathlib import Path
import sys,hashlib,json,subprocess
r=Path(sys.argv[1]).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
BEFORE={'atelier-preview.js': 'ad2d8b19f4c2a269119f1b739432fc37792ca0409a1e1502340a917b08c1748b', 'assembly-review.js': '489a16d2349ccb2691f3d1724cf4a6b1e65f9ea8638902872e2903f3f2b269a9', 'tests/atelier-capture-handoff.test.mjs': '9cf0ebce131615a7b8582da156001f9ad9d7784ddd3003ba8bbe1ca2bdb7bf9d', 'deployment-manifest.json': 'ea0c1718b2f9383e7e628dcde22973082bb92d54335f7ef5f655b297eb922b8a', 'quality-study/viewer-revision.js': 'a023bd6713444a5af56211b9aa05f493815a359aafe427b680f79f39b780e50c', 'quality-study/viewer-revision.json': '4d3dd9db8e75e8a19fa06257fb947eb489282f0f0630527b121300c3c57d7f97'}
AFTER={'atelier-preview.js': '2056258d342b2b3d3239a53e6d9be5ef8cb69d29ab4735ac6b7fb5ff345f8382', 'assembly-review.js': '52eb488530ef8edc3f3f1535d8240b13e1ab295881abbb26a69e623aa9dce0b8', 'tests/atelier-capture-handoff.test.mjs': '6c1ce9c878c0bcdc7eebd8f889c9792bc062489e9620f0960b21ea8b05429980', 'deployment-manifest.json': 'e5b0f301629214ed5af9f95ce44a24fb2f4ab99ed9b027e1bec0c4a32d6610ce', 'quality-study/viewer-revision.js': '49ec6c8a5713ced937b3fec115635087a134708e7bf96b344a7d31630e3c5de9', 'quality-study/viewer-revision.json': '2cc9243d701cee77f23c15410631f77acc2a7c86d9f9a448443dc99fb8288c2d'}
for name,expected in BEFORE.items():
 if sha(r/name)!=expected:raise SystemExit('Unexpected base bytes: '+name)
p=r/'atelier-preview.js';s=p.read_text();start=s.index('function waitForCaptureLayout(){');end=s.index('async function captureAtFullStage',start)
s=s[:start]+'''let captureFrameSerial=0;
function waitForCaptureLayout(){
 return new Promise((resolve,reject)=>{
  let poll=0,previous='',stable=0,done=false,requestedSignature=null;
  const requestId=++captureFrameSerial;
  const finish=error=>{if(done)return;done=true;clearTimeout(poll);clearTimeout(timeout);window.removeEventListener('pagehide',cancel);document.removeEventListener('atelier:capture-frame-rendered',rendered);error?reject(error):resolve();};
  const cancel=()=>finish(new Error('Capture cancelled because the viewer closed.'));
  const timeout=setTimeout(()=>finish(new Error('The full watch view did not finish resizing. Please try again.')),10000);
  const dimensions=()=>{const r=$('stage').getBoundingClientRect(),canvas=$('assembly-canvas');return [r.width,r.height,canvas.width,canvas.height];};
  const valid=d=>d.every(v=>v>0)&&Math.abs(d[2]*d[1]-d[3]*d[0])<=d[0]+d[1];
  const closed=()=>$('context').hidden&&(!panelMedia.matches||document.body.dataset.panelOpen==='false');
  const rendered=event=>{
   if(event.detail?.requestId!==requestId||!requestedSignature)return;
   if(!$('context').hidden){finish(new Error('Capture cancelled because another tool was opened.'));return;}
   const d=dimensions(),signature=d.join(':');
   if(closed()&&valid(d)&&signature===requestedSignature&&event.detail.dimensions?.join(':')===signature)finish();
   else{requestedSignature=null;stable=0;previous='';}
  };
  window.addEventListener('pagehide',cancel,{once:true});document.addEventListener('atelier:capture-frame-rendered',rendered);
  const check=()=>{
   if(done)return;
   if(!$('context').hidden){finish(new Error('Capture cancelled because another tool was opened.'));return;}
   const d=dimensions(),signature=d.join(':');
   // Timer samples establish geometry stability without depending on GPU frame
   // cadence. A matching real composer-render acknowledgement is still required.
   stable=valid(d)&&closed()&&signature===previous?stable+1:0;previous=signature;
   if(requestedSignature&&signature!==requestedSignature)requestedSignature=null;
   if(stable>=2&&!requestedSignature){requestedSignature=signature;document.dispatchEvent(new CustomEvent('atelier:request-capture-frame',{detail:{requestId}}));}
   if(!done)poll=setTimeout(check,50);
  };
  check();
 });
}
'''+s[end:];p.unlink();p.write_text(s)
p=r/'assembly-review.js';s=p.read_text();needle='let loading = true, failed = false, contextLost = false, dirty = true, firstRender = true;';assert needle in s
s=s.replace(needle,needle+'''
let pendingCaptureFrame=null;
const requestCaptureFrame=event=>{
 const id=event.detail?.requestId;if(!Number.isSafeInteger(id)||id<=0)return;
 pendingCaptureFrame=id;dirty=true;
};
document.addEventListener('atelier:request-capture-frame',requestCaptureFrame);
resources.own('capture frame readiness',()=>{pendingCaptureFrame=null;document.removeEventListener('atelier:request-capture-frame',requestCaptureFrame);});
''')
needle="composer.render();renderedFrames++;dirty=false;presentationGate.rendered(!premiumRequested||premiumActive());"
assert needle in s
s=s.replace(needle,needle+'''
       if(pendingCaptureFrame!==null){
        const requestId=pendingCaptureFrame;pendingCaptureFrame=null;const r=$('stage').getBoundingClientRect();
        document.dispatchEvent(new CustomEvent('atelier:capture-frame-rendered',{detail:{requestId,dimensions:[r.width,r.height,renderer.domElement.width,renderer.domElement.height]}}));
       }
''');p.unlink();p.write_text(s)

p=r/'tests/atelier-capture-handoff.test.mjs';p.unlink();p.write_text('import {test} from \'node:test\';import assert from \'node:assert/strict\';import vm from \'node:vm\';import {readFileSync} from \'node:fs\';\nconst source=readFileSync(new URL(\'../atelier-preview.js\',import.meta.url),\'utf8\'),block=source.split(\'// BEGIN full-stage capture handoff.\')[1].split(\'// END full-stage capture handoff.\')[0];\nfunction harness(){\n const timers=new Map(),listeners=new Map(),docListeners=new Map(),calls=[],requests=[];let serial=0;\n const els={context:{hidden:false},stage:{getBoundingClientRect:()=>({width:400,height:380})},\'assembly-canvas\':{width:800,height:760},status:{textContent:\'\'},\'record-scene\':{textContent:\'Record 8s video\',getAttribute:()=>null},\'capture-scene\':{textContent:\'Save PNG image\',getAttribute:()=>null}};\n const document={body:{dataset:{panelOpen:\'false\'}},createElement:()=>({style:{},setAttribute(){}}),querySelector:()=>({append:n=>els[n.id]=n}),addEventListener:(k,f)=>docListeners.set(k,f),removeEventListener:k=>docListeners.delete(k),dispatchEvent:e=>{requests.push(e);docListeners.get(e.type)?.(e);}};\n const context=vm.createContext({$:id=>els[id],document,panelMedia:{matches:true},taskStatusBaseline:\'old\',CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail;}},window:{addEventListener:(k,f)=>listeners.set(k,f),removeEventListener:k=>listeners.delete(k)},setTimeout:(fn,ms)=>{timers.set(++serial,{fn,ms});return serial;},clearTimeout:k=>timers.delete(k),liveTarget:id=>els[id]?.disabled?null:els[id],proxy:id=>{calls.push(id);return true;},updateText:(id,text)=>els[id].textContent=text,closeContext:()=>els.context.hidden=true});vm.runInContext(block,context);\n const poll=async()=>{const [id,t]=[...timers].find(([,t])=>t.ms===50)||[];assert.ok(t,\'poll scheduled\');timers.delete(id);t.fn();await Promise.resolve();};\n const ack=(requestId=requests.at(-1)?.detail.requestId,dimensions=[400,380,800,760])=>docListeners.get(\'atelier:capture-frame-rendered\')?.({detail:{requestId,dimensions}});\n return {context,els,timers,listeners,docListeners,calls,requests,document,poll,ack,start:id=>vm.runInContext(`captureAtFullStage(\'${id||\'capture-scene\'}\')`,context)};\n}\ntest(\'correct geometry can start after one actual render even with no RAF samples\',async()=>{const h=harness(),p=h.start(\'record-scene\');await h.poll();await h.poll();assert.equal(h.requests.length,1);assert.equal(h.calls.length,0);h.ack();await p;assert.deepEqual(h.calls,[\'record-scene\']);assert.equal(h.timers.size,0);assert.equal(h.docListeners.size,0);});\ntest(\'stable geometry alone cannot authorize capture; wrong request or dimensions rejected\',async()=>{const h=harness(),p=h.start();await h.poll();await h.poll();h.ack(999);assert.equal(h.calls.length,0);h.ack(undefined,[400,380,800,394]);assert.equal(h.calls.length,0);for(let i=0;i<3;i++)await h.poll();h.ack();await p;assert.deepEqual(h.calls,[\'capture-scene\']);});\ntest(\'compact canvas never requests render or captures until resize completes\',async()=>{const h=harness();h.els[\'assembly-canvas\'].height=394;const p=h.start();for(let i=0;i<4;i++)await h.poll();assert.equal(h.requests.length,0);h.els[\'assembly-canvas\'].height=760;for(let i=0;i<3;i++)await h.poll();h.ack();await p;assert.equal(h.calls.length,1);});\ntest(\'resize after request rejects stale rendered signature and requests fresh frame\',async()=>{const h=harness(),p=h.start();await h.poll();await h.poll();h.els.stage.getBoundingClientRect=()=>({width:400,height:400});h.els[\'assembly-canvas\'].height=800;h.ack();assert.equal(h.calls.length,0);for(let i=0;i<3;i++)await h.poll();h.ack(undefined,[400,400,800,800]);await p;assert.equal(h.requests.length,2);});\ntest(\'reentry ignored; cancelled handoff cannot consume late acknowledgement\',async()=>{const h=harness(),p=h.start();await h.start();await h.poll();await h.poll();const old=h.requests[0].detail.requestId;h.els.context.hidden=false;await h.poll();await p;assert.equal(h.calls.length,0);assert.equal(h.docListeners.size,0);const next=h.start();await h.poll();await h.poll();h.ack(old);assert.equal(h.calls.length,0);h.ack();await next;assert.equal(h.calls.length,1);});\ntest(\'timeout/pagehide clean timers and listeners without forwarding\',async()=>{for(const mode of [\'timeout\',\'pagehide\']){const h=harness(),p=h.start();await h.poll();await h.poll();if(mode===\'timeout\')[...h.timers.values()].find(t=>t.ms===10000).fn();else h.listeners.get(\'pagehide\')();await p;assert.equal(h.calls.length,0);assert.equal(h.timers.size,0);assert.equal(h.docListeners.size,0);assert.equal(h.listeners.size,0);}});\ntest(\'legacy stop forwards immediately without a readiness wait\',async()=>{const h=harness();h.els[\'record-scene\'].textContent=\'Stop recording\';await h.start(\'record-scene\');assert.deepEqual(h.calls,[\'record-scene\']);assert.equal(h.requests.length,0);});\ntest(\'runtime acknowledges only after real composer render; request forces dirty without changing quality/motion\',()=>{const runtime=readFileSync(new URL(\'../assembly-review.js\',import.meta.url),\'utf8\');const start=runtime.indexOf(\'composer.render();renderedFrames++\');assert.ok(start>=0);const ack=runtime.indexOf("\'atelier:capture-frame-rendered\'",start);assert.ok(ack>start);const handler=runtime.slice(runtime.indexOf(\'const requestCaptureFrame=\'),runtime.indexOf("document.addEventListener(\'atelier:request-capture-frame\'"));assert.match(handler,/dirty=true/);assert.doesNotMatch(handler,/quality\\s*=|clock\\.|animate|setRunning/);});\n\ntest(\'JSON retains direct mapping and export status mirrors runtime errors after closing without camera writes\',()=>{\n assert.match(source,/if\\(\\[\'capture-scene\',\'record-scene\'\\]\\.includes\\(el.dataset.proxy\\)\\)/);\n assert.doesNotMatch(block,/controls\\.target|camera\\.|setMode\\(/);\n assert.match(source,/if\\(exportNoticeActive\\)showExportNotice\\(exportNoticeMessage\\?\\?presentationMessage\\)/);\n assert.match(block,/exportNoticeMessage=null;taskStatusBaseline=null;if\\(!proxy\\(id\\)\\)/);\n});\n\n\ntest(\'visual export feedback hides behind an open tool panel and returns only when closed\',()=>{\n const h=harness();\n vm.runInContext("exportNoticeActive=true;showExportNotice(\'PNG download requested.\');",h.context);\n assert.equal(h.els[\'atelier-export-notice\'].hidden,true);\n h.els.context.hidden=true;vm.runInContext("showExportNotice(\'PNG download requested.\');",h.context);\n assert.equal(h.els[\'atelier-export-notice\'].hidden,false);\n h.els.context.hidden=false;vm.runInContext("showExportNotice(\'Save an image or restore this view.\');",h.context);\n assert.equal(h.els[\'atelier-export-notice\'].hidden,true);\n assert.match(source,/updateText\\(\'atelier-panel-status\',presentationMessage\\)/);\n});\n')
p=r/'deployment-manifest.json';m=json.loads(p.read_text())
for e in m['files']:
 if e['path'] in ['assembly-review.js','atelier-preview.js']:
  b=(r/e['path']).read_bytes();e.update(sizeBytes=len(b),sha256=hashlib.sha256(b).hexdigest())
p.unlink();p.write_text(json.dumps(m,indent=2)+'\n')
for name in ['quality-study/viewer-revision.js','quality-study/viewer-revision.json']:
 p=r/name;b=p.read_bytes();p.unlink();p.write_bytes(b)
subprocess.run(['node','tools/capture-provenance.mjs'],cwd=r,check=True)
p=r/'deployment-manifest.json';m=json.loads(p.read_text())
for e in m['files']:
 if e['path'].startswith('quality-study/viewer-revision.'):
  b=(r/e['path']).read_bytes();e.update(sizeBytes=len(b),sha256=hashlib.sha256(b).hexdigest())
p.write_text(json.dumps(m,indent=2)+'\n')
for name,expected in AFTER.items():
 if sha(r/name)!=expected:raise SystemExit('Overlay result identity mismatch: '+name)
print('Capture gate overlay verified: 6 declared source files; no asset or quality changes.')

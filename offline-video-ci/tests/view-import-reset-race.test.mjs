import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const runtime=readFileSync(process.env.AERIAL_RUNTIME_TEST_PATH||new URL('../assembly-review.js',import.meta.url),'utf8');
const reset=runtime.slice(runtime.indexOf("$('reset').onclick ="),runtime.indexOf("document.addEventListener('keydown'"));
const importer=runtime.slice(runtime.indexOf('let configurationRequest=0;'),runtime.indexOf('let last = 0;'));
function harness(){
 const elements=new Map();const $=id=>{if(!elements.has(id))elements.set(id,{value:'',checked:false});return elements.get(id);};let imports=0;
 const noop=()=>{};const context={$,pendingCaptures:new Set(),frameVideo:{active:false},
  inspectionDisplay:{wireframe:true,transparentBackplate:true},resetExplosion:noop,crownInteraction:{reset:noop},stopTour:noop,resetMotion:noop,clock:{setSpeed:noop},renderingQuality:noop,initialQuality:'studio',clearSelection:noop,renderExplorer:noop,showAll:noop,announce:noop,
  loading:false,failed:false,lifecycle:{disposed:false},qualityProfiles:{studio:{}},
  validateViewConfiguration:value=>value,
  // Stop at the first post-await mutation boundary; its reachability is the race.
  resolveInspectionState:()=>{imports++;throw new Error('Reached import application');},
 };
 vm.createContext(context);vm.runInContext(reset+'\n'+importer,context);return {$,context,get imports(){return imports;}};
}
test('Reset invalidates an import whose file read has not completed',async()=>{
 const h=harness();let resolve;const pending=new Promise(r=>resolve=r),input={files:[{size:100,text:()=>pending}],value:'pending.json'};
 const completion=h.$('import-config').onchange({target:input});h.$('reset').onclick();
 assert.equal(h.context.pendingCaptures.has('import-config'),false,'Reset must clear the stale import capture blocker');assert.equal(h.context.inspectionDisplay.wireframe,false);assert.equal(h.context.inspectionDisplay.transparentBackplate,false);
 resolve('{}');await completion;assert.equal(h.imports,0,'a stale import must not apply after explicit Reset');
});
test('newer import still supersedes older pending import; departure prevents application',async()=>{
 const h=harness();let release;const old=h.$('import-config').onchange({target:{files:[{size:100,text:()=>new Promise(r=>release=r)}]}});
 await h.$('import-config').onchange({target:{files:[{size:100,text:async()=> '{}'}]}});assert.equal(h.imports,1);release('{}');await old;assert.equal(h.imports,1);
 h.context.lifecycle.disposed=true;await h.$('import-config').onchange({target:{files:[{size:100,text:async()=> '{}'}]}});assert.equal(h.imports,1);
});

test('pending import is tracked until the current request finishes',async()=>{
 const h=harness();let resolve;const task=h.$('import-config').onchange({target:{files:[{size:100,text:()=>new Promise(r=>resolve=r)}]}});assert.equal(h.context.pendingCaptures.has('import-config'),true);resolve('{}');await task;assert.equal(h.context.pendingCaptures.has('import-config'),false);
});
test('active video cannot be changed by a resumed import',async()=>{
 const h=harness();let resolve;const task=h.$('import-config').onchange({target:{files:[{size:100,text:()=>new Promise(r=>resolve=r)}]}});h.context.frameVideo.active=true;resolve('{}');await task;assert.equal(h.imports,0);assert.equal(h.context.pendingCaptures.has('import-config'),false);
});

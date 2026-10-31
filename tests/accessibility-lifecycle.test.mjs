import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
async function module(name){const source=await readFile(new URL('../'+name,import.meta.url),'utf8');return import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));}
const {createPresentationClock}=await module('assembly-clock.js');
const {createViewerLifecycle}=await module('assembly-lifecycle.js');
const {createResourceScope}=await module('assembly-state.js');
const {isEditingControl,closeDisclosureWithFocus,restoreExplorerFocus}=await module('assembly-control-focus.js');
test('hidden time never advances the mechanical pose on resume',()=>{const clock=createPresentationClock({now:()=>0});clock.setRunning('mechanism',true,0);clock.setHidden(true,1000);assert.equal(clock.tick(60000).mechanism,1);clock.setHidden(false,60000);assert.equal(clock.tick(61000).mechanism,2);});
test('cached navigation retains resources but real departure aborts and disposes once',()=>{let paused=0,resumed=0,disposed=0;const lifecycle=createViewerLifecycle({pause:()=>paused++,resume:()=>resumed++,dispose:()=>disposed++});lifecycle.hide({persisted:true});assert.equal(lifecycle.signal.aborted,false);assert.equal(lifecycle.show(),true);assert.equal(resumed,1);lifecycle.hide();lifecycle.hide();assert.equal(lifecycle.signal.aborted,true);assert.equal(disposed,1);assert.equal(lifecycle.show(),false);assert.equal(paused,2);});
test('native and inherited editable controls retain Escape ownership',()=>{assert.equal(isEditingControl({tagName:'SELECT'}),true);assert.equal(isEditingControl({tagName:'SPAN',parentElement:{tagName:'TEXTAREA'}}),true);assert.equal(isEditingControl({tagName:'SPAN',getAttribute:()=>null,parentElement:{getAttribute:()=> 'plaintext-only'}}),true);assert.equal(isEditingControl({tagName:'BUTTON'}),false);});
test('closing a disclosure returns contained focus to its summary',()=>{let closed=false,focused=false;const menu={contains:()=>true,removeAttribute:name=>{closed=name==='open';},querySelector:()=>({focus:()=>focused=true})};assert.equal(closeDisclosureWithFocus(menu,{}),true);assert.ok(closed&&focused);});
test('hidden explorer results return keyboard focus to search',()=>{let focus='';const list={querySelectorAll:()=>[{dataset:{key:'crown'},checkVisibility:()=>false,focus:()=>focus='hidden'}]};assert.equal(restoreExplorerFocus(list,'crown',{focus:()=>focus='search'}),true);assert.equal(focus,'search');});
test('resource cleanup runs in reverse order once and continues after a disposer fails',()=>{
 const scope=createResourceScope(),calls=[];
 scope.own('first',()=>calls.push('first'));
 scope.own('broken',()=>{calls.push('broken');throw new Error('dispose failed');});
 scope.own('last',()=>calls.push('last'));
 assert.throws(()=>scope.dispose(),AggregateError);
 assert.deepEqual(calls,['last','broken','first']);
 assert.doesNotThrow(()=>scope.dispose());
 assert.deepEqual(scope.snapshot(),{disposed:true,active:[]});
});

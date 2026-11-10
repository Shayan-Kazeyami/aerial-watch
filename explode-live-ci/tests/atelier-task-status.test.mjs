import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createAtelierNavigation} from '../atelier-navigation.js';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../atelier-preview.js',import.meta.url),'utf8');
const block=source.split('// BEGIN active task status.')[1].split('// END active task status.')[0];
function harness(){
 let onMutation,discarded=0;
 const status={textContent:'Crown controls opened. Turn while seated, or pull out to set the hands.'};
 const navigation=createAtelierNavigation();
 const context=vm.createContext({navigation,$:()=>status,ready:true,failed:false,presentationState:{phase:'ready'},mode:'explode',MutationObserver:class{constructor(cb){onMutation=cb;}observe(){}takeRecords(){discarded++;}}});
 vm.runInContext(block,context);
 return {context,status,open:mode=>{context.mode=mode;navigation.open(mode);vm.runInContext('beginTaskStatus()',context);},message:()=>vm.runInContext('activeTaskStatus($("viewer-status").textContent)',context),announce:text=>{status.textContent=text;onMutation();},discarded:()=>discarded};
}
test('Time to Explode replaces stale crown instructions, including repeated syncs',()=>{
 const h=harness();h.open('explode');assert.match(h.message(),/Assembly separation/);assert.doesNotMatch(h.message(),/Crown controls opened/);assert.match(h.message(),/Assembly separation/);assert.equal(h.discarded(),1);
});
test('Capture and other task switches get current guidance without changing legacy runtime status',()=>{
 const h=harness(),original=h.status.textContent;
 h.open('capture');assert.match(h.message(),/JSON/);h.open('time');assert.match(h.message(),/pull it out/);h.open('quality');assert.match(h.message(),/preset/);assert.equal(h.status.textContent,original);
});
test('fresh action results, failures and JSON restore announcements override task guidance',()=>{
 for(const message of ['Could not save image: unsupported','Preparing PNG image…','Saved camera, crown, options, time scale, explosion and pose restored. Motion is paused.']){
  const h=harness();h.open('capture');h.announce(message);assert.equal(h.message(),message);
 }
});
test('fresh repeated identical announcements remain valid; stale queued announcements are drained on switch',()=>{
 const h=harness();h.open('explode');h.announce(h.status.textContent);assert.equal(h.message(),h.status.textContent);h.open('capture');assert.match(h.message(),/JSON/);assert.equal(h.discarded(),2);
});
test('loading, failed and degraded presentation messages are never masked',()=>{
 for(const state of [{ready:false},{failed:true},{presentationState:{phase:'degraded'}}]){
  const h=harness();h.open('explode');Object.assign(h.context,state);assert.equal(h.message(),h.status.textContent);
 }
});
test('task switch snapshots status before activating task-specific camera/actions',()=>{
 assert.match(source,/mode=next;beginTaskStatus\(\);/);
 assert.match(source,/const presentationMessage=activeTaskStatus\(ready\|\|failed\?/);
 assert.match(source,/updateText\('status',presentationMessage\);updateText\('atelier-panel-status',presentationMessage\)/);
});


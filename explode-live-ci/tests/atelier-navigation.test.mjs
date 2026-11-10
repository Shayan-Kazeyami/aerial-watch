import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createAtelierNavigation,EXPERIENCE_MODES} from '../atelier-navigation.js';
import {readFileSync} from 'node:fs';
test('utilities preserve every active experience and dismissal never changes it',()=>{
 for(const experience of EXPERIENCE_MODES)for(const utility of ['quality','capture','settings','tour','motion','components']){
  const n=createAtelierNavigation();n.open(experience);n.open(utility);
  assert.equal(n.snapshot().experience,experience);assert.equal(n.snapshot().tool,utility);
  n.close();assert.equal(n.snapshot().experience,experience);assert.equal(n.snapshot().tool,null);
 }
});
test('selection has a precise return route, including a closed panel',()=>{
 for(const tool of ['inside','explode','components','quality',null]){
  const n=createAtelierNavigation();n.open('inside');if(tool)n.open(tool);else n.close();
  const before=n.snapshot();n.select();n.select();assert.equal(n.snapshot().tool,'selection');
  assert.deepEqual(n.returnFromSelection(),before);
 }
});
test('choosing a new task discards a stale selection route',()=>{
 const n=createAtelierNavigation();n.open('inside');n.select();n.open('explode');n.select();
 assert.equal(n.returnFromSelection().tool,'explode');assert.equal(n.snapshot().experience,'explode');
});
test('restoring an imported scene replaces both navigation states without retaining selection history',()=>{
 const n=createAtelierNavigation();n.open('inside');n.select();
 assert.deepEqual(n.restore({experience:'explode',tool:'explode'}),{experience:'explode',tool:'explode',selectionReturn:null});
 n.restore({experience:'invalid'});assert.deepEqual(n.snapshot(),{experience:'explore',tool:null,selectionReturn:null});
});
test('navigation snapshots cannot mutate the pending return route',()=>{
 const n=createAtelierNavigation();n.open('inside');n.select();n.snapshot().selectionReturn.tool='quality';assert.equal(n.returnFromSelection().tool,'inside');
});
test('integration keeps the actual controls, utility indicator and one-click crown directions',()=>{
 const js=readFileSync(new URL('../atelier-preview.js',import.meta.url),'utf8'),css=readFileSync(new URL('../atelier-preview.css',import.meta.url),'utf8');
 assert.match(js,/inspectionControls\.remove\(\);tools\.innerHTML=/);assert.match(js,/\$\('atelier-inspection-host'\)\?\.append\(inspectionControls\)/);
 assert.match(js,/primary\?next===state.experience:open&&next===mode/);assert.match(js,/const resume=next===navigation.snapshot\(\).experience/);
 assert.match(js,/Active inspection:/);assert.match(js,/value:false/);assert.match(js,/Click or tap the dot to pull or push/);assert.doesNotMatch(js,/Double-click to pull or push/);
 assert.match(css,/\.inspection-tools\{display:grid/);assert.doesNotMatch(css,/\.inspection-tools\{position:absolute/);
});

test('selection return restores visible focus and new component identity can reopen its inspector',()=>{
 const js=readFileSync(new URL('../atelier-preview.js',import.meta.url),'utf8');
 assert.match(js,/if\(!state.tool\)\{closeContext\(\);\$\('assembly-canvas'\).focus\(\);\}/);
 assert.match(js,/else \$\('close'\).focus\(\)/);
 assert.match(js,/identity!==selectedIdentity/);
 assert.match(js,/selectedBefore=selected;selectedIdentity=identity/);
});

test('mobile Reset remains discoverable while every task panel is open',()=>{
 const css=readFileSync(new URL('../atelier-preview.css',import.meta.url),'utf8');
 assert.doesNotMatch(css,/\.atelier-live\[data-panel-open=true\] :is\([^}]*\.home[^}]*\)\{display:none/);
});

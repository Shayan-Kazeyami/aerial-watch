import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validateViewConfiguration} from '../assembly-story.js';
const valid=()=>({version:1,view:'face',camera:{position:[0,0,100],target:[0,0,0],zoom:1,fov:32},options:{openWork:true,finishes:true,crystals:false,movementOnly:false,quality:'detail'},clock:{hands:30,mechanism:15,speed:.25}});
test('saved-view validation preserves independent clock tracks and camera without aliasing',()=>{
 const original=valid(),v=validateViewConfiguration(original);assert.equal(v.clock.hands,30);assert.equal(v.clock.mechanism,15);assert.equal(v.clock.speed,.25);
 v.camera.position[0]=7;assert.equal(original.camera.position[0],0);
});
test('malformed view files are rejected before applying any state',()=>{
 for(const change of [v=>v.version=99,v=>v.camera.position=[NaN,0,10],v=>v.camera.target=[0,0,100],v=>v.options.openWork='true',v=>v.clock.speed=-1,v=>v.view='unknown',v=>v.crown={pulled:true,degrees:Infinity}]){
  const v=valid();change(v);assert.throws(()=>validateViewConfiguration(v));
 }
});
test('tour timing follows elapsed seconds rather than rendered-frame count',async()=>{
 const {createTourSequence}=await import('../assembly-story.js');const tour=createTourSequence();tour.start();
 assert.equal(tour.tick(7.5).index,1);assert.equal(tour.tick(14).index,3);
 tour.stop();assert.equal(tour.tick(100),null);
});
test('exploded amount restores explicitly and rejects invalid values',()=>{assert.equal(validateViewConfiguration(valid()).explosion,0);assert.equal(validateViewConfiguration({...valid(),explosion:.65}).explosion,.65);for(const explosion of [-1,1.01,NaN,Infinity,'1'])assert.throws(()=>validateViewConfiguration({...valid(),explosion}),/explosion/);});
test('saved component selection and isolation are bounded and copied',()=>{const c={...valid(),inspection:{selected:['source:0','assembly:CASE'],isolated:['source:0']}};const v=validateViewConfiguration(c);assert.deepEqual(v.inspection,c.inspection);v.inspection.selected.push('source:1');assert.equal(c.inspection.selected.length,2);for(const inspection of [{selected:['source:999'],isolated:null},{selected:['assembly:../bad'],isolated:null},{selected:['source:1','source:1'],isolated:null},{selected:[],isolated:['source:1']}])assert.throws(()=>validateViewConfiguration({...valid(),inspection}),/inspection/);});
test('literal runtime camera views are valid saved-view names',async()=>{const {readFile}=await import('node:fs/promises');const s=await readFile(new URL('../assembly-review.js',import.meta.url),'utf8');for(const [,view]of s.matchAll(/\bview\('([^']+)'/g))assert.doesNotThrow(()=>validateViewConfiguration({...valid(),view}),view);});

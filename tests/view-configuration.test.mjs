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

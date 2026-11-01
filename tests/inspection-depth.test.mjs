import {test} from 'node:test';
import assert from 'node:assert/strict';
import {PerspectiveCamera,Vector3,Box3} from '../vendor/three.module.js';
import {updateInspectionDepth} from '../assembly-depth.js';
const box=()=>new Box3(new Vector3(-.1,-.1,-.1),new Vector3(.1,.1,.1));
test('whole-watch depth safety keeps its existing minimum distance',()=>{
 const c=new PerspectiveCamera(32,1,.1,800);c.position.set(0,0,2);
 const state=updateInspectionDepth(c,new Vector3(),[box()]);assert.equal(state.minimumDistance,9);assert.equal(c.position.z,9);
});
test('isolated tiny parts permit macro inspection without entering the part',()=>{
 const c=new PerspectiveCamera(32,1,.1,800);c.position.set(0,0,.12);
 const state=updateInspectionDepth(c,new Vector3(),[box()],undefined,{distanceFloor:.25,surfacePadding:.05});
 assert.equal(state.minimumDistance,.25);assert.equal(c.position.z,.25);assert(state.near>0&&state.near<.15);
});
test('invalid depth-clearance configuration is rejected',()=>{
 assert.throws(()=>updateInspectionDepth(new PerspectiveCamera(),new Vector3(),[],undefined,{distanceFloor:0}),/clearance/);
});

import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Group,Mesh,Matrix4,Vector3} from '../vendor/three.module.js';
import {createAssemblyExplosion as candidate} from '../assembly-explode.js';
import {createAssemblyExplosion as baseline} from '../assembly-explode-baseline.js';
function fixture(create){
 const root=new Group(),parents=Array.from({length:8},()=>new Group());root.add(...parents);
 const meshes=Array.from({length:166},(_,sourceIndex)=>{const m=new Mesh();m.userData.sourceIndex=sourceIndex;m.position.set(sourceIndex%5,sourceIndex%3,sourceIndex%7);parents[sourceIndex%8].add(m);return m;});
 const api=create({root});api.register(meshes);api.setAmount(1,{instant:true});return {root,parents,meshes,api};
}
function operations(create){
 const f=fixture(create);let inversions=0,writes=0;const invert=Matrix4.prototype.invert;
 Matrix4.prototype.invert=function(){inversions++;return invert.call(this);};
 for(const m of f.meshes){const w=m.parent,update=w.updateMatrix;w.updateMatrix=function(){writes++;return update.call(this);};}
 try{for(let i=0;i<600;i++)f.api.update(1/60);}finally{Matrix4.prototype.invert=invert;}
 return {inversions,writes};
}
test('600 settled frames eliminate all repeated inverse and wrapper writes',()=>{
 const before=operations(baseline),after=operations(candidate);
 assert.deepEqual(before,{inversions:4800,writes:99600});assert.deepEqual(after,{inversions:0,writes:0});
 console.log(JSON.stringify({settledFrames:600,parts:166,parents:8,before,after}));
});
test('cached output matches baseline through root/parent motion, scrubbing, singular recovery and late arrivals',()=>{
 const a=fixture(baseline),b=fixture(candidate);const outA=new Vector3(),outB=new Vector3();
 for(let step=0;step<240;step++){
  for(const f of [a,b]){
   f.root.position.set(Math.sin(step*.1),step*.01,0);f.root.rotation.set(.3,step*.02,-.4);f.root.scale.set(2,3,1.5);
   f.parents.forEach((p,i)=>{p.rotation.set(i*.1,step*.03,i*.07);p.scale.set(step===30?0:.5+i*.1,2,1.3);p.position.set(i,Math.cos(step*.2+i),0);});
   if(step%15===0)f.api.setAmount((step%45)/45,{instant:step%30===0});
   if(step===80){const m=new Mesh();m.userData.assemblyId='DIAL';f.parents[2].add(m);f.meshes.push(m);f.api.register([m]);}
   f.api.update(1/60);f.root.updateMatrixWorld(true);
  }
  assert.equal(a.api.amount,b.api.amount);
  for(let i=0;i<a.meshes.length;i++){
   a.meshes[i].getWorldPosition(outA);b.meshes[i].getWorldPosition(outB);
   assert(outA.distanceTo(outB)<1e-10,`step ${step}, mesh ${i}: ${outA.toArray()} vs ${outB.toArray()}`);
   assert.deepEqual(a.meshes[i].matrix.elements,b.meshes[i].matrix.elements);
  }
 }
 for(const f of [a,b]){f.api.reset({instant:true});f.api.dispose();}
 for(let i=0;i<8;i++)assert.deepEqual(a.parents[i].children.map(o=>o.userData),b.parents[i].children.map(o=>o.userData));
});

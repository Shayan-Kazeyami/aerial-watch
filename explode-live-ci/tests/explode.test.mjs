import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Group,Mesh,BoxGeometry,MeshBasicMaterial,Vector3,Matrix4,Box3} from '../vendor/three.module.js';
import {createAssemblyExplosion,assemblyExplosionOffset} from '../assembly-explode.js';
const near=(a,b)=>assert(Math.abs(a-b)<1e-9,`${a} != ${b}`);
function fixture(){const root=new Group(),branch=new Group();root.add(branch);const meshes=['CASE','DIAL','HOUR','MINUTE','SECONDS','FRONT-CRYSTAL','BEZEL','CASEBACK','REAR-CRYSTAL'].map(assemblyId=>{const m=new Mesh(new BoxGeometry(),new MeshBasicMaterial());m.userData.assemblyId=assemblyId;m.position.set(1,2,3);m.updateMatrix();branch.add(m);return m;});return {root,branch,meshes};}
const snapshot=m=>({matrix:m.matrix.toArray(),position:m.position.toArray(),quaternion:m.quaternion.toArray(),scale:m.scale.toArray(),geometry:m.geometry,auto:m.matrixAutoUpdate});
test('zero, full and partial layers preserve poses and restore exact parent order',()=>{
 const {root,branch,meshes}=fixture(),before=meshes.map(snapshot),children=[...branch.children],e=createAssemblyExplosion({root,duration:1});e.register(meshes);
 assert.deepEqual(branch.children,children);e.setAmount(1);e.update(.5);near(e.amount,.5);
 for(const m of meshes){assert.deepEqual(snapshot(m),before[meshes.indexOf(m)]);near(m.getWorldPosition(new Vector3()).y,2+assemblyExplosionOffset(m)*.5);}
 e.update(.5);assert.equal(e.amount,1);assert.equal(e.animating,false);assert.equal(e.active,true);
 const box=new Box3().setFromObject(root);assert([...box.min,...box.max].every(Number.isFinite));
 e.reset();e.update(1);assert.equal(e.active,false);assert.deepEqual(branch.children,children);for(const m of meshes)assert.equal(m.parent,branch);
});
test('repeated sliders do not accumulate wrappers; retargeting starts at displayed pose',()=>{
 const {root,branch,meshes}=fixture(),e=createAssemblyExplosion({root,duration:1});e.register(meshes);e.setAmount(1);e.update(.5);e.setAmount(1);e.update(.5);assert.equal(e.amount,1);
 for(let i=0;i<30;i++){e.setAmount(.7);e.update(.1);const amount=e.amount;e.setAmount(.2);assert.equal(e.amount,amount);e.update(.1);e.register(meshes);assert.equal(branch.children.length,meshes.length);}
 e.setAmount(.4);e.update(5);assert.equal(e.amount,.4);for(const m of meshes)near(m.getWorldPosition(new Vector3()).y,2+assemblyExplosionOffset(m)*.4);
 e.dispose();assert.deepEqual(branch.children,meshes);e.dispose();assert.deepEqual(branch.children,meshes);
});
test('rotated nonuniform parents and fixed matrices use the root-space watch normal',()=>{
 const {root,branch,meshes}=fixture();root.rotation.set(Math.PI/2,.2,0);root.scale.set(2,3,4);branch.rotation.set(.3,.7,.1);branch.scale.set(.5,2,1.5);
 const m=meshes[1];m.matrixAutoUpdate=false;m.matrix.makeRotationZ(.9).setPosition(5,6,7);const original=m.matrix.toArray();root.updateMatrixWorld(true);
 const start=m.getWorldPosition(new Vector3()),delta=new Vector3(0,24,0).applyMatrix4(root.matrixWorld).sub(new Vector3().applyMatrix4(root.matrixWorld));
 const e=createAssemblyExplosion({root,duration:0});e.register(meshes);e.setAmount(1);const end=m.getWorldPosition(new Vector3());near(end.distanceTo(start.clone().add(delta)),0);assert.deepEqual(m.matrix.toArray(),original);
 root.rotation.z=.4;e.update(0);const after=m.getWorldPosition(new Vector3());assert(after.toArray().every(Number.isFinite));e.reset({instant:true});assert.equal(m.parent,branch);assert.deepEqual(m.matrix.toArray(),original);
});
test('all 166 movement parts separate while local poses and replacement identity remain coherent',()=>{
 const root=new Group(),source=[];for(let i=0;i<166;i++){const m=new Mesh();m.userData.sourceIndex=i;m.position.set(i,i%3,0);m.updateMatrix();root.add(m);source.push(m);}
 const before=source.map(snapshot),e=createAssemblyExplosion({root,duration:0});e.register(source);e.setAmount(1);source.forEach((m,i)=>{assert.notEqual(m.parent,root);assert.deepEqual(snapshot(m),before[i]);near(m.getWorldPosition(new Vector3()).y,(i%3)+assemblyExplosionOffset(m));});
 const authored=new Mesh();authored.userData.premiumFacePart=true;root.add(authored);e.register([authored]);near(authored.getWorldPosition(new Vector3()).y,24);
 authored.name='MINUTE / bored integral hub';authored.userData={designPart:'QUALITY-HAND'};assert.equal(assemblyExplosionOffset(authored),36);
 for(const assemblyId of ['STRAP-UPPER','LUG','BUCKLE','CASE','CROWN'])assert.equal(assemblyExplosionOffset({userData:{assemblyId}}),0);
 const replacement=new Mesh();replacement.userData.replacementForSourceIndex=0;assert.equal(assemblyExplosionOffset(replacement),8);assert.equal(e.snapshot().layers.filter(l=>l.sourceParts>0).length,6);assert.equal(e.snapshot().layers.reduce((n,l)=>n+l.sourceParts,0),166);e.dispose();assert.equal(authored.parent,root);source.forEach(m=>assert.equal(m.parent,root));
});
test('finite bounded input, reduced motion, detached late arrivals and disposal',()=>{
 assert.throws(()=>createAssemblyExplosion({duration:NaN}),/Invalid/);const e=createAssemblyExplosion({duration:0}),root=new Group(),m=new Mesh();m.userData.assemblyId='BEZEL';e.register([m]);e.setAmount(10);assert.equal(e.amount,1);root.add(m);e.update(0);near(m.getWorldPosition(new Vector3()).y,41);
 e.setAmount(-1);assert.equal(e.amount,0);assert.equal(m.parent,root);for(const v of [NaN,Infinity,-Infinity]){assert.throws(()=>e.setAmount(v),/Invalid/);assert.throws(()=>e.update(v),/Invalid/);}assert.throws(()=>e.update(-1),/Invalid/);
 e.setAmount(1);root.scale.y=0;e.update(0);assert(m.parent.position.toArray().every(Number.isFinite));e.dispose();e.dispose();e.register([m]);e.setAmount(1);assert.equal(e.active,false);assert.equal(e.amount,0);assert.equal(m.parent,root);
});
test('many explode/reassemble cycles retain exact geometry bytes, local matrices and sibling slots',()=>{
 const {root,branch,meshes}=fixture(),baseline=meshes.map(snapshot),geometry=meshes.map(m=>Array.from(m.geometry.attributes.position.array));
 const sentinel=new Group();branch.children.splice(3,0,sentinel);sentinel.parent=branch;const order=[...branch.children];
 const e=createAssemblyExplosion({root,duration:.55}).register(meshes);
 for(let i=0;i<50;i++){e.setAmount(1);e.update(.2);e.reset();e.update(1);assert.deepEqual(branch.children,order);meshes.forEach((m,j)=>{assert.deepEqual(snapshot(m),baseline[j]);assert.deepEqual(Array.from(m.geometry.attributes.position.array),geometry[j]);});}
 e.setAmount(1);e.update(.1);e.dispose();assert.deepEqual(branch.children,order);
});
test('completed layers follow subsequent root rotations and parent scale changes',()=>{
 const {root,branch,meshes}=fixture(),m=meshes[1],e=createAssemblyExplosion({root,duration:0}).register(meshes);e.setAmount(1);
 root.rotation.set(.6,.8,.3);root.position.set(30,20,10);root.scale.set(2,3,4);branch.rotation.set(.4,.2,.8);branch.scale.set(3,2,5);e.update(0);
 root.updateMatrixWorld(true);const base=new Vector3().setFromMatrixPosition(m.matrix).applyMatrix4(branch.matrixWorld),delta=new Vector3(0,24,0).applyMatrix4(root.matrixWorld).sub(new Vector3().applyMatrix4(root.matrixWorld));near(m.getWorldPosition(new Vector3()).distanceTo(base.add(delta)),0);
});

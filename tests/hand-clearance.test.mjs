import {test} from 'node:test';
import assert from 'node:assert/strict';
import {BufferGeometry,Float32BufferAttribute,Mesh,Group,MeshBasicMaterial} from '../vendor/three.module.js';
import {createHandClearance,PREMIUM_HAND_CLEARANCE} from '../assembly-hand-clearance.js';
function fixture(){
 const parent=new Group(),material=new MeshBasicMaterial();
 const make=(id,points)=>{const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(points,3));const mesh=new Mesh(geometry,material);mesh.name=id;mesh.userData.assemblyId=id;parent.add(mesh);return mesh;};
 const seconds=make('SECONDS',[0,3.9,0,1,3.96,0,0,4.15,1]);seconds.position.set(-8,0,.016);seconds.rotation.y=.4;
 const staff=make('SECONDS-STAFF',[.18,2.89,0,-.18,2.94,0,.18,4,0]);staff.position.copy(seconds.position);
 return {parent,seconds,staff,exterior:[seconds,staff]};
}
test('premium derived stack translates only seconds depth; lower staff seat stays byte-identical',()=>{
 const f=fixture(),originals=f.exterior.map(m=>m.geometry),arrays=originals.map(g=>Array.from(g.attributes.position.array));const c=createHandClearance(f.exterior);
 assert.equal(c.enabled,false);assert.equal(f.seconds.geometry,originals[0]);c.setEnabled(true);
 assert.notEqual(f.seconds.geometry,originals[0]);assert.notEqual(f.staff.geometry,originals[1]);
 for(let i=0;i<3;i++){assert.equal(f.seconds.geometry.attributes.position.getX(i),arrays[0][3*i]);assert.equal(f.seconds.geometry.attributes.position.getZ(i),arrays[0][3*i+2]);assert.ok(Math.abs(f.seconds.geometry.attributes.position.getY(i)-(arrays[0][3*i+1]-.32))<1e-6);}
 assert.equal(f.staff.geometry.attributes.position.getY(0),arrays[1][1]);assert.equal(f.staff.geometry.attributes.position.getY(1),arrays[1][4]);assert.ok(Math.abs(f.staff.geometry.attributes.position.getY(2)-3.68)<1e-6);
 originals.forEach((g,i)=>assert.deepEqual(Array.from(g.attributes.position.array),arrays[i]));assert.equal(PREMIUM_HAND_CLEARANCE.secondsDepthOffset,-.32);
 c.dispose();f.exterior.forEach((m,i)=>assert.equal(m.geometry,originals[i]));
});
test('toggle idempotence preserves live clock poses, explosion parents/order, materials and original buffers',()=>{
 const f=fixture(),original=f.exterior.map(m=>m.geometry),material=f.seconds.material,c=createHandClearance(f.exterior);c.setEnabled(true);const clones=f.exterior.map(m=>m.geometry);
 const explosion=new Group();f.parent.add(explosion);explosion.add(f.seconds);f.seconds.rotation.y=1.7;f.seconds.position.y=12;
 const q=f.seconds.quaternion.clone(),position=f.seconds.position.clone(),children=[...explosion.children];
 c.setEnabled(true);assert.equal(f.seconds.geometry,clones[0]);c.setEnabled(false);c.setEnabled(false);assert.equal(f.seconds.geometry,original[0]);c.setEnabled(true);
 assert.deepEqual(f.seconds.quaternion.toArray(),q.toArray());assert.deepEqual(f.seconds.position,position);assert.equal(f.seconds.parent,explosion);assert.deepEqual(explosion.children,children);assert.equal(f.seconds.material,material);
 let disposals=0;clones.forEach(g=>g.addEventListener('dispose',()=>disposals++));original.forEach(g=>g.addEventListener('dispose',()=>assert.fail('raw geometry disposed')));
 c.dispose();c.dispose();c.setEnabled(true);assert.equal(disposals,2);assert.equal(c.enabled,false);assert.equal(f.seconds.geometry,original[0]);assert.deepEqual(f.seconds.quaternion.toArray(),q.toArray());assert.deepEqual(f.seconds.position,position);
});
test('missing/duplicate baseline inputs rejected and foreign geometry ownership never overwritten',()=>{
 const f=fixture();assert.throws(()=>createHandClearance([f.seconds]),/SECONDS-STAFF/);assert.throws(()=>createHandClearance([...f.exterior,f.seconds]),/SECONDS/);
 const c=createHandClearance(f.exterior),other=f.seconds.geometry.clone();f.seconds.geometry=other;assert.throws(()=>c.setEnabled(true),/ownership conflict/);c.setEnabled(false);c.dispose();assert.equal(f.seconds.geometry,other);
});

test('actual assembly.glb POSITION buffers derive the audited stack without changing original bytes',async()=>{
 const {readFile}=await import('node:fs/promises');const bytes=await readFile(new URL('../rebuild/assembly.glb',import.meta.url));const jsonLength=bytes.readUInt32LE(12),gltf=JSON.parse(bytes.subarray(20,20+jsonLength).toString()),binaryStart=28+jsonLength;
 const exterior=[];
 for(const node of gltf.nodes){
  if(!['SECONDS','SECONDS-STAFF'].includes(node.extras?.assemblyId))continue;
  const primitive=gltf.meshes[node.mesh].primitives[0],accessor=gltf.accessors[primitive.attributes.POSITION],view=gltf.bufferViews[accessor.bufferView];assert.equal(accessor.componentType,5126);
  const positions=[];for(let i=0;i<accessor.count;i++){const start=binaryStart+(view.byteOffset||0)+(accessor.byteOffset||0)+i*(view.byteStride||12);for(let c=0;c<3;c++)positions.push(bytes.readFloatLE(start+4*c));}
  const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(positions,3));const mesh=new Mesh(geometry);mesh.userData=node.extras;mesh.name=node.name;if(node.translation)mesh.position.fromArray(node.translation);if(node.rotation)mesh.quaternion.fromArray(node.rotation);exterior.push(mesh);
 }
 const original=exterior.map(m=>m.geometry),snapshots=original.map(g=>Array.from(g.attributes.position.array));const c=createHandClearance(exterior);c.setEnabled(true);
 const seconds=exterior.find(m=>m.userData.assemblyId==='SECONDS'),staff=exterior.find(m=>m.userData.assemblyId==='SECONDS-STAFF');
 assert.ok(Math.abs(seconds.geometry.boundingBox.min.y-3.58)<1e-6);assert.ok(Math.abs(seconds.geometry.boundingBox.max.y-3.83)<1e-6);assert.ok(Math.abs(staff.geometry.boundingBox.max.y-3.68)<1e-6);assert.ok(Math.abs(staff.geometry.boundingBox.min.y-2.89)<1e-6);
 original.forEach((g,i)=>assert.deepEqual(Array.from(g.attributes.position.array),snapshots[i]));c.dispose();exterior.forEach((m,i)=>assert.equal(m.geometry,original[i]));
});

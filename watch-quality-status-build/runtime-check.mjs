import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import * as THREE from './staging/preview-b/releases/f3ab38493b7bc5c4af84728add913e54938d0db276143a7b765a7803f361bb44/vendor/three.module.js';
import {createMechanismBatch} from './staging/preview-b/releases/ea85a4e6e44dbbfe4337f1dd8fa376793db7e9ce90628fe1d50b2edef9482de6/assembly-mechanism-batch.js';
let matrixWrites=0;const originalSetter=THREE.BatchedMesh.prototype.setMatrixAt;THREE.BatchedMesh.prototype.setMatrixAt=function(...args){matrixWrites++;return originalSetter.apply(this,args)};
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const raw=(process.env.WATCH_BASE||'strap-combined-qa/resume/recovery-09e3e0ae/preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6')+'/rebuild/assembly.glb';
const baked=(process.env.NORMAL_INPUT||'hardware-normal-qa/recovery-2145')+'/assembly-normal-candidate.glb';
function test(path){
 const bytes=fs.readFileSync(path),len=bytes.readUInt32LE(12),json=JSON.parse(bytes.subarray(20,20+len)),bin=bytes.subarray(28+len);const scene=new THREE.Scene(),materials=json.materials.map(()=>new THREE.MeshPhysicalMaterial());
 function attr(i){const a=json.accessors[i],v=json.bufferViews[a.bufferView],C={5126:Float32Array,5123:Uint16Array,5125:Uint32Array}[a.componentType],size={SCALAR:1,VEC3:3,VEC2:2}[a.type],off=(v.byteOffset||0)+(a.byteOffset||0),b=bin.subarray(off,off+a.count*size*C.BYTES_PER_ELEMENT);return new THREE.BufferAttribute(new C(b.buffer.slice(b.byteOffset,b.byteOffset+b.length)),size)}
 const source=json.nodes.filter(n=>n.extras?.sourceIndex!==undefined).map(n=>{const p=json.meshes[n.mesh].primitives[0],g=new THREE.BufferGeometry();for(const[k,i]of Object.entries(p.attributes))g.setAttribute({POSITION:'position',NORMAL:'normal',TEXCOORD_0:'uv'}[k],attr(i));g.setIndex(attr(p.indices));const m=new THREE.Mesh(g,materials[p.material]);m.userData={...n.extras};m.castShadow=m.receiveShadow=true;scene.add(m);return m});
 const identity=source.map(m=>({g:m.geometry,n:m.geometry.attributes.normal,hash:sha(m.geometry.attributes.normal.array)}));const x=createMechanismBatch({THREE,scene,renderer:{extensions:{has:()=>true}}});x.build(source);const audit=x.snapshot();assert.equal(audit.reusedEntries,58);assert.equal(audit.rejectedReuse,0);
 let maxInstanceError=0;const canonicalData=(awaitData);const byId=new Map(source.map(m=>[m.userData.sourceIndex,m]));
 for(let step=0;step<15;step++){for(const m of source){const s=m.userData.sourceIndex;m.position.set(Math.sin(step+s)*20,Math.cos(s*.1+step)*30,step%3*7);m.quaternion.setFromEuler(new THREE.Euler(step*.01,s*.02,step*.03))}x.beforeRender();for(const e of x.snapshot().entries){const m=byId.get(e.sourceIndex),batch=scene.children.find(b=>b.isBatchedMesh&&b.material===m.material),actual=new THREE.Matrix4(),correction=new THREE.Matrix4().fromArray(canonicalData.find(r=>r.sourceIndex===e.sourceIndex).matrix),expected=new THREE.Matrix4().multiplyMatrices(m.matrixWorld,correction);batch.getMatrixAt(e.instanceId,actual);maxInstanceError=Math.max(maxInstanceError,...actual.elements.map((v,i)=>Math.abs(v-expected.elements[i])));assert(batch.getVisibleAt(e.instanceId));}x.afterRender();assert(source.every(m=>m.visible));const settledWrites=matrixWrites;for(let repeat=0;repeat<3;repeat++){x.beforeRender();x.afterRender();}assert.equal(matrixWrites,settledWrites,'settled corrected instances must not re-upload');}
 assert(source.every((m,i)=>m.geometry===identity[i].g&&m.geometry.attributes.normal===identity[i].n&&sha(m.geometry.attributes.normal.array)===identity[i].hash));

 // Independent assertions on the composed implementation, not a duplicate implementation.
 const target=byId.get(40), row=audit.entries.find(e=>e.sourceIndex===40);
 const owner=scene.children.find(b=>b.isBatchedMesh&&b.material===target.material);
 function frame(){x.beforeRender();x.afterRender();}
 const beforeTiny=matrixWrites;target.position.x+=1e-12;frame();
 assert.equal(matrixWrites,beforeTiny+1,'exact sub-Float32 pose changes still upload');
 const beforeHidden=matrixWrites;target.visible=false;target.position.y+=1;frame();
 assert.equal(matrixWrites,beforeHidden,'invisible mutation does not upload');target.visible=true;frame();
 assert.equal(matrixWrites,beforeHidden+1,'returning visible uploads changed corrected pose');
 const newMaterial=new THREE.MeshPhysicalMaterial();const oldMaterial=target.material;target.material=newMaterial;
 x.beforeRender();assert(target.visible);assert(!owner.getVisibleAt(row.instanceId));x.afterRender();target.material=oldMaterial;
 const parent=new THREE.Group();scene.add(parent);parent.add(target);parent.visible=false;target.position.z+=1;
 const beforeParent=matrixWrites;frame();assert.equal(matrixWrites,beforeParent);parent.visible=true;frame();assert.equal(matrixWrites,beforeParent+1);
 target.scale.x=-1;x.beforeRender();assert(target.visible);assert(!owner.getVisibleAt(row.instanceId));x.afterRender();target.scale.x=1;frame();
 const oldPosition=target.geometry.attributes.position;target.geometry.setAttribute('position',oldPosition.clone());
 x.beforeRender();assert(target.visible);assert(!owner.getVisibleAt(row.instanceId));x.afterRender();target.geometry.setAttribute('position',oldPosition);
 oldPosition.needsUpdate=true;x.beforeRender();assert(target.visible);assert(!owner.getVisibleAt(row.instanceId));x.afterRender();
 // Restore captured version solely inside this isolated fixture to exercise independent guards.
 oldPosition.version--;frame();
 const canonical=byId.get(row.canonical),oldCanonical=canonical.geometry.attributes.normal;
 canonical.geometry.setAttribute('normal',oldCanonical.clone());x.beforeRender();assert(target.visible);assert(!owner.getVisibleAt(row.instanceId));x.afterRender();canonical.geometry.setAttribute('normal',oldCanonical);
 x.setEnabled(false);const beforeDisabled=matrixWrites;frame();assert.equal(matrixWrites,beforeDisabled);assert(source.every(m=>m.visible));x.setEnabled(true);frame();
 const savedSetter=THREE.BatchedMesh.prototype.setMatrixAt;let thrown=false;
 THREE.BatchedMesh.prototype.setMatrixAt=function(...args){if(!thrown){thrown=true;throw new Error('fixture write failure')}return savedSetter.apply(this,args)};
 target.position.z+=2;const beforeThrow=matrixWrites;
 try{assert.throws(()=>x.beforeRender(),/fixture write failure/);}finally{x.afterRender();THREE.BatchedMesh.prototype.setMatrixAt=savedSetter;}
 frame();assert(matrixWrites>beforeThrow,'failed write must retry, never cache failure');
 const replaced=byId.get(40);replaced.geometry.setAttribute('normal',replaced.geometry.attributes.normal.clone());x.beforeRender();assert(replaced.visible);x.afterRender();x.dispose();assert(source.every(m=>m.visible));
 return {path,sha256:sha(bytes),sourceMeshes:source.length,reused:audit.reusedEntries,rejected:audit.rejectedReuse,originalGeometryBufferBytes:audit.originalGeometryBufferBytes,allocatedGeometryBufferBytes:audit.allocatedGeometryBufferBytes,savedBytes:audit.originalGeometryBufferBytes-audit.allocatedGeometryBufferBytes,maxPositionErrorMM:Math.max(...audit.entries.map(e=>e.maxPositionErrorMM)),maxNormalError:Math.max(...audit.entries.map(e=>e.maxNormalError)),maxFloat32InstanceError:maxInstanceError,sourceNormalsUnchanged:true,sameVersionNormalReplacementFallback:true,disposeRestoresVisibility:true,settledCorrectedInstancesSkipUploads:true,independentComposedGuardSuite:true};
}
const {hardwareCanonicalReuse:awaitData}=await import('./staging/preview-b/releases/ea85a4e6e44dbbfe4337f1dd8fa376793db7e9ce90628fe1d50b2edef9482de6/assembly-hardware-canonical-data.js');
assert.equal(sha(fs.readFileSync(raw)),'4a4ae04e5808e705c9a2a96778343578365d100edfed3991d8ff90aeba85d06f');assert.equal(sha(fs.readFileSync(baked)),'6ac638843c56eb4ae2f3d9ee1135facaac085ae70e2292f2b3d30f9673340039');assert.equal(sha(fs.readFileSync('watch-quality-status-build/staging/preview-b/releases/ea85a4e6e44dbbfe4337f1dd8fa376793db7e9ce90628fe1d50b2edef9482de6/assembly-mechanism-batch.js')),'d4e96a759b8596661db1db700def0b33ba2680b01b48465cb778b3a388d7cf87');const results=[test(raw),test(baked)];assert.equal(results[0].savedBytes,results[1].savedBytes);const report={passed:true,scope:'Node/Three187 structural validation using synthetic source-material cohorts, not actual viewer pixels or real-device FPS',batchSHA256:sha(fs.readFileSync('watch-quality-status-build/staging/preview-b/releases/ea85a4e6e44dbbfe4337f1dd8fa376793db7e9ce90628fe1d50b2edef9482de6/assembly-mechanism-batch.js')),results};fs.writeFileSync('watch-quality-status-build/runtime-structural-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));

import assert from 'node:assert/strict';
import * as THREE from '../preview-b/releases/f3ab38493b7bc5c4af84728add913e54938d0db276143a7b765a7803f361bb44/vendor/three.core.js';
import {createMechanismBatch} from './assembly-mechanism-batch.js';
const scene=new THREE.Scene(),parent=new THREE.Group();scene.add(parent);parent.position.set(3,4,5);parent.rotation.x=.4;
const mat=new THREE.MeshStandardMaterial(),source=[];
for(let i=0;i<10;i++){const geo=new THREE.BoxGeometry();geo.clearGroups();const mesh=new THREE.Mesh(geo,mat);mesh.position.x=i;parent.add(mesh);source.push(mesh);}
const cache=createMechanismBatch({THREE,scene,renderer:{extensions:{has:()=>true}}});cache.build(source);const batch=scene.children.find(x=>x.isBatchedMesh);assert(batch);
cache.beforeRender();assert(source.every(m=>!m.visible));const matrix=new THREE.Matrix4();batch.getMatrixAt(2,matrix);assert.deepEqual(matrix.elements,source[2].matrixWorld.elements.map(Math.fround));cache.afterRender();assert(source.every(m=>m.visible));assert(!batch.visible);
source[0].visible=false;source[1].material=mat.clone();source[2].scale.x=-1;const replacement=source[3].geometry.clone();source[3].geometry=replacement;
cache.beforeRender();assert(!batch.getVisibleAt(0));assert(!batch.getVisibleAt(1));assert(!batch.getVisibleAt(2));assert(!batch.getVisibleAt(3));assert(source[1].visible&&source[2].visible&&source[3].visible);cache.afterRender();assert(!source[0].visible);
parent.visible=false;cache.beforeRender();assert(!batch.visible);cache.afterRender();parent.visible=true;
cache.setEnabled(false);cache.beforeRender();assert(source.slice(1).every(m=>m.visible));cache.afterRender();cache.dispose();assert(!scene.children.some(x=>x.isBatchedMesh));
const fallback=createMechanismBatch({THREE,scene,renderer:{extensions:{has:()=>false}}});fallback.build(source);assert.equal(fallback.snapshot().batches,0);
console.log('PASS: parent transforms, source restoration, visibility, material/geometry replacement, negative scale, disable/dispose, no-extension fallback');

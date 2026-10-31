import {test} from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {preparePremiumFace,premiumFaceVisible,PREMIUM_HIDDEN_SOURCES} from '../assembly-premium-face.js';
test('premium face only shows on unobstructed exterior open-work view',()=>{
 const base={enabled:true,openWork:true,movementOnly:false,isolated:false,interior:false};
 assert.equal(premiumFaceVisible(base),true);
 for(const key of ['enabled','openWork'])assert.equal(premiumFaceVisible({...base,[key]:false}),false);
 for(const key of ['movementOnly','isolated','interior'])assert.equal(premiumFaceVisible({...base,[key]:true}),false);
 assert.deepEqual(PREMIUM_HIDDEN_SOURCES,[0,149,155]);
});
test('premium face refuses source geometry and empty asset',()=>{
 assert.throws(()=>preparePremiumFace(new THREE.Group()),/no meshes/);
 const root=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());root.add(mesh);
 assert.throws(()=>preparePremiumFace(root),/authored/);
 mesh.userData.premiumFacePart=true;mesh.userData.sourceIndex=0;assert.throws(()=>preparePremiumFace(root),/authored/);
 delete mesh.userData.sourceIndex;assert.equal(preparePremiumFace(root).meshes.length,1);assert.equal(root.visible,false);
 mesh.geometry.dispose();mesh.material.dispose();
});
test('exported face contains only authored geometry and required named parts',async()=>{
 const {readFile}=await import('node:fs/promises');const b=await readFile(new URL('../premium-face/face-b.glb',import.meta.url));
 assert.equal(b.toString('ascii',0,4),'glTF');const length=b.readUInt32LE(12);const gltf=JSON.parse(b.toString('utf8',20,20+length));
 const nodes=gltf.nodes.filter(n=>n.mesh!==undefined);assert.equal(nodes.length,76);
 assert(nodes.every(n=>n.extras?.premiumFacePart===true&&n.extras.sourceIndex===undefined));
 assert(nodes.some(n=>n.name==='B continuous left aperture dial'));
 assert(nodes.some(n=>n.name==='Champagne aperture rim'));
 assert.equal(nodes.filter(n=>n.name.startsWith('Seconds tick ')).length,60);
});

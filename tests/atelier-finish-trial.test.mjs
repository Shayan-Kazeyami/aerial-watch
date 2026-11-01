import {test} from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {createAssemblyMaterials} from '../assembly-materials.js';
import {preparePremiumFace} from '../assembly-premium-face.js';

test('premium exterior hand classification reaches optional blue without changing other finishes',()=>{
  for(const atelier of [false,true]){
    const baseline=createAssemblyMaterials(null,{atelier});
    const unknown=createAssemblyMaterials(null,{atelier,finish:'unknown'});
    const trial=createAssemblyMaterials(null,{atelier,finish:'atelier2'});
    for(const assemblyId of ['HOUR','MINUTE','SECONDS']){
      const mesh={userData:{assemblyId}},a=baseline.apply(mesh),b=trial.apply(mesh);
      assert.equal(a.userData.finish,'blued');assert.equal(b.userData.finish,'blued');
      assert.equal(a.color.getHex(),0x1a4d80);
      assert.equal(unknown.apply(mesh).color.getHex(),0x1a4d80);
      assert.equal(b.color.getHex(),0x346fa6);
      for(const key of ['metalness','roughness','clearcoat'])assert.equal(a[key],b[key]);
      assert.equal(a.customProgramCacheKey(),b.customProgramCacheKey());
    }
    for(const assemblyId of ['BEZEL','CASE','FRONT-CRYSTAL']){
      const mesh={userData:{assemblyId}},a=baseline.apply(mesh),b=trial.apply(mesh);
      assert(a.color.equals(b.color));assert.equal(a.roughness,b.roughness);
    }
    baseline.dispose();unknown.dispose();trial.dispose();
  }
});

test('SVG04 graphite trial is subtle, quieter and isolated from other finishes and revisions',()=>{
  const priorDocument=globalThis.document;
  globalThis.document={createElement:()=>({getContext:()=>({createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData(){}})})};
  try{
    for(const [revision,finish,active] of [['B-SVG-04','baseline',false],['B-SVG-04','unknown',false],['B-SVG-04','atelier2',true],['B-SVG-03','atelier2',false]]){
      const root=new THREE.Group(),material=new THREE.MeshStandardMaterial({metalness:.02,roughness:.48});
      material.name='Graphite dial';material.color.setRGB(.014,.016,.019);
      const gold=new THREE.MeshStandardMaterial({color:0xb89b70});gold.name='Muted champagne';const goldBefore=gold.color.clone();
      const mesh=new THREE.Mesh(new THREE.BoxGeometry(),[material,gold]);mesh.userData={premiumFacePart:true,designRevision:revision};root.add(mesh);
      const positions=mesh.geometry.attributes.position.array.slice();
      const prepared=preparePremiumFace(root,{finish});
      assert(Math.abs(material.color.r-.014*(active?1.18:1))<1e-12);
      assert.equal(material.bumpScale,active?.003:revision==='B-SVG-04'?.008:.12);
      assert.equal(material.roughness,.48);assert.equal(material.metalness,.02);assert(gold.color.equals(goldBefore));
      assert.deepEqual(mesh.geometry.attributes.position.array,positions);
      prepared.texture.dispose();mesh.geometry.dispose();material.dispose();gold.dispose();
    }
  }finally{if(priorDocument===undefined)delete globalThis.document;else globalThis.document=priorDocument;}
});

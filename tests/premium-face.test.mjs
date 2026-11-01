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
test('B reference palette keeps neutral bearings and silver wheel plates without recoloring barrels',async()=>{
 const {premiumMovementFinishKind:kind}=await import('../assembly-premium-face.js');
 assert.equal(kind({sourceIndex:11,description:'Pierre bombée'}),'steel');
 assert.equal(kind({sourceIndex:99,description:'Planche de roue'}),'steel');
 assert.equal(kind({sourceIndex:112,description:'Serge de balancier'}),'steel');
 assert.equal(kind({sourceIndex:81,description:'Barillet'}),null);
 assert.equal(kind({assemblyId:'HOUR'},'blue hand'),null);
});
test('SVG review route is explicit and preserves exported finish scalars',async()=>{
 const {premiumFaceAsset}=await import('../assembly-premium-face.js');
 assert.equal(premiumFaceAsset('svg'),'premium-face/face-svg-b.glb?v=svg02');
 assert.equal(premiumFaceAsset('https://untrusted.example/model.glb'),'premium-face/face-b.glb');
 const root=new THREE.Group(),material=new THREE.MeshStandardMaterial({metalness:.03,roughness:.59});material.name='Graphite dial';material.color.setRGB(.0018,.002,.0025);
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(),material);mesh.userData={premiumFacePart:true,designRevision:'B-SVG-01'};root.add(mesh);
 const before=material.color.clone();assert.equal(preparePremiumFace(root).revision,'B-SVG-01');assert(material.color.equals(before));assert.equal(material.roughness,.59);assert.equal(material.metalness,.03);
 mesh.geometry.dispose();material.dispose();
});
test('SVG-derived exported overlay is authored-only and includes one unified dial',async()=>{
 const {readFile}=await import('node:fs/promises');const b=await readFile(new URL('../premium-face/face-svg-b.glb',import.meta.url));const gltf=JSON.parse(b.toString('utf8',20,20+b.readUInt32LE(12)));
 const nodes=gltf.nodes.filter(n=>n.mesh!==undefined);assert.equal(nodes.length,73);assert(nodes.every(n=>n.extras?.premiumFacePart&&n.extras.designRevision==='B-SVG-02'&&n.extras.sourceIndex===undefined));
 assert.equal(nodes.filter(n=>n.name==='SVG unified dial and seconds support').length,1);assert.equal(nodes.filter(n=>n.name.startsWith('SVG seconds-tick-')).length,60);
});
test('SVG outer aperture is a concentric circular arc with a constant rim',async()=>{
 const {readFile}=await import('node:fs/promises');const {createHash}=await import('node:crypto');
 const svg=await readFile(new URL('../design-preview/Aerial-Left-Crescent-B-dimensioned.svg',import.meta.url));
 const audit=JSON.parse(await readFile(new URL('../design-preview/svg-face-audit.json',import.meta.url)));
 const geometry=JSON.parse(await readFile(new URL('../design-preview/svg-face-3d-audit.json',import.meta.url)));
 assert.equal(audit.revision,'B-SVG-02');assert.deepEqual(audit.outer_arc_center_mm,[0,0]);assert.equal(audit.outer_arc_radius_mm,15.7);
 assert(Math.abs(audit.constant_outer_rim_mm-.7)<1e-10);assert(audit.outer_arc_max_radial_error_mm<1e-10);
 assert.match(svg.toString(),/A 15\.7,15\.7 0 0 1/);assert.equal(createHash('sha256').update(svg).digest('hex'),geometry.source_svg_sha256);
});

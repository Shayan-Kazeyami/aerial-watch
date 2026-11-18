import test from 'node:test';import assert from 'node:assert/strict';import * as T from '../aerial-watch-geometry-revision-candidate-v2/vendor/three.module.js';
const{createMechanismBatch}=await import(process.env.BASELINE==='1'?'./BASELINE.js':'../watch-current/preview-b/releases/watch-batch-review-local/assembly-mechanism-batch.js');
function setup(){const s=new T.Scene(),geo=new T.BoxGeometry();geo.clearGroups();let mat=new T.MeshStandardMaterial(),ms=Array.from({length:8},()=>{let m=new T.Mesh(geo.clone(),mat);s.add(m);return m});let api=createMechanismBatch({THREE:T,scene:s,renderer:{extensions:{has:()=>true}}});api.build(ms);return{ms,api,b:s.children.find(x=>x.isBatchedMesh)}}
function original(x){x.api.beforeRender();assert.equal(x.b.getVisibleAt(0),false);assert.equal(x.ms[0].visible,true);assert.equal(x.b.getVisibleAt(1),true);x.api.afterRender();x.api.dispose()}
test('unchanged geometry remains eligible',()=>{let x=setup();x.api.beforeRender();assert.equal(x.b.getVisibleAt(0),true);x.api.afterRender();x.api.dispose()});
test('in-place position version update stays authoritative',()=>{let x=setup(),a=x.ms[0].geometry.attributes.position;a.setX(0,100);a.needsUpdate=true;original(x)});
test('in-place normal update stays authoritative',()=>{let x=setup();x.ms[0].geometry.attributes.normal.needsUpdate=true;original(x)});
test('same geometry replacement attribute stays authoritative',()=>{let x=setup(),g=x.ms[0].geometry;g.setAttribute('position',g.attributes.position.clone());original(x)});
test('same geometry index revision stays authoritative',()=>{let x=setup();x.ms[0].geometry.index.needsUpdate=true;original(x)});
test('replacement index stays authoritative',()=>{let x=setup(),g=x.ms[0].geometry;g.setIndex(g.index.clone());original(x)});
test('drawRange no longer full stays authoritative',()=>{let x=setup();x.ms[0].geometry.setDrawRange(0,6);original(x)});
test('material groups added stays authoritative',()=>{let x=setup();x.ms[0].geometry.addGroup(0,6,0);original(x)});
test('attribute addition stays authoritative',()=>{let x=setup(),g=x.ms[0].geometry;g.setAttribute('custom',new T.Float32BufferAttribute(new Float32Array(g.attributes.position.count),1));original(x)});
test('morph position added stays authoritative',()=>{let x=setup(),g=x.ms[0].geometry;g.morphAttributes.position=[g.attributes.position.clone()];original(x)});

for(const name of ['normal','color'])test(`non-position ${name} morph added stays authoritative`,()=>{let x=setup(),g=x.ms[0].geometry;g.morphAttributes[name]=[g.attributes.position.clone()];original(x)});
test('initial non-position morph geometry never enters batch',()=>{let s=new T.Scene(),g=new T.BoxGeometry();g.clearGroups();g.morphAttributes.normal=[g.attributes.normal.clone()];let m=new T.MeshStandardMaterial(),ms=Array.from({length:8},()=>{let x=new T.Mesh(g,m);s.add(x);return x});let a=createMechanismBatch({THREE:T,scene:s,renderer:{extensions:{has:()=>true}}});a.build(ms);assert.equal(a.snapshot().meshes,0);a.beforeRender();assert(ms.every(x=>x.visible));a.dispose()});

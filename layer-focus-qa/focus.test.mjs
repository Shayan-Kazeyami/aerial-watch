import test from 'node:test';import assert from 'node:assert/strict';
import {Group,Mesh,BoxGeometry,MeshBasicMaterial,PerspectiveCamera,Vector3} from './vendor/three.module.js';
import {createLayerFocus,MECHANICAL_FOCUS_IDS} from './assembly-layer-focus.js';
function fixture(){const root=new Group(),camera=new PerspectiveCamera(32,1.2,.1,1000);camera.position.set(60,40,130);camera.up.set(0,1,0);camera.zoom=1.3;const controls={target:new Vector3(2,3,4),update(){throw Error('Controller must not update damping');}};camera.lookAt(controls.target);camera.updateProjectionMatrix();
 const add=(id,parent=root,visible=true)=>{const m=new Mesh(new BoxGeometry(4,5,6),new MeshBasicMaterial());m.userData.sourceIndex=id;m.position.set(id*.1,id*.02,0);m.visible=visible;parent.add(m);return m;};
 const parts=[add(0),add(45),add(85),add(102),add(120),add(150)],hiddenParent=new Group();hiddenParent.visible=false;root.add(hiddenParent);const hidden=add(86,hiddenParent),authored=add(87,root,false),outer=new Mesh(new BoxGeometry(),new MeshBasicMaterial());outer.userData.assemblyId='BEZEL';root.add(outer);
 const c=createLayerFocus({root,camera,controls});return {root,camera,controls,parts,hidden,hiddenParent,authored,outer,c};}
const cam=f=>({p:f.camera.position.toArray(),q:f.camera.quaternion.toArray(),up:f.camera.up.toArray(),zoom:f.camera.zoom,t:f.controls.target.toArray()});
const flags=f=>{const a=[];f.root.traverse(x=>{if(x.isMesh)a.push([x.uuid,x.visible])});return a;};
const poses=f=>{const a=[];f.root.traverse(x=>{if(x.isMesh)a.push([x.uuid,x.position.toArray(),x.quaternion.toArray(),x.scale.toArray(),x.geometry.uuid,x.material.uuid])});return a;};
test('six IDs use exact source classification; exterior unavailable',()=>{const f=fixture();assert.equal(MECHANICAL_FOCUS_IDS.length,6);for(let i=0;i<6;i++)assert.deepEqual(f.c.members(MECHANICAL_FOCUS_IDS[i]),[f.parts[i]]);assert.deepEqual(f.c.members('bezel'),[]);});
test('focus hides nonmembers without material/pose changes and exactly restores camera/visibility',()=>{const f=fixture(),before=cam(f),visible=flags(f),p=poses(f);assert.equal(f.c.focus('train'),true);assert.equal(f.parts[2].visible,true);assert.equal(f.outer.visible,false);assert.equal(f.camera.zoom,1);assert.deepEqual(poses(f),p);assert.equal(f.c.overview(),true);assert.deepEqual(cam(f),before);assert.deepEqual(flags(f),visible);assert.deepEqual(poses(f),p);});
test('switch uses baseline visibility and retains original return state',()=>{const f=fixture(),before=cam(f),visible=flags(f);f.c.focus('train');assert.equal(f.parts[4].visible,false);assert.equal(f.c.focus('balance'),true);assert.equal(f.parts[4].visible,true);assert.equal(f.parts[2].visible,false);f.c.overview();assert.deepEqual(cam(f),before);assert.deepEqual(flags(f),visible);});
test('nested hidden parent and authored variants never become selected or revealed',()=>{const f=fixture();f.c.focus('train');assert.equal(f.hiddenParent.visible,false);assert.equal(f.hidden.visible,false);assert.equal(f.authored.visible,false);assert.deepEqual(f.c.members('train'),[f.parts[2]]);f.c.overview();assert.equal(f.hidden.visible,true);assert.equal(f.hiddenParent.visible,false);assert.equal(f.authored.visible,false);});
test('invalid or empty layer leaves active state untouched',()=>{const f=fixture();f.parts[4].visible=false;f.c.focus('train');const c=cam(f),v=flags(f),s=f.c.snapshot();assert.equal(f.c.focus('bogus'),false);assert.equal(f.c.focus('balance'),false);assert.deepEqual(cam(f),c);assert.deepEqual(flags(f),v);assert.deepEqual(f.c.snapshot(),s);});
test('invisible material excluded, no empty-focus mutation',()=>{const f=fixture();f.parts[2].material.visible=false;const c=cam(f),v=flags(f);assert.equal(f.c.focus('train'),false);assert.deepEqual(cam(f),c);assert.deepEqual(flags(f),v);});
test('visibility-only cancel preserves current camera',()=>{const f=fixture(),v=flags(f);f.c.focus('train');const focused=cam(f);assert.equal(f.c.cancel(),true);assert.deepEqual(cam(f),focused);assert.deepEqual(flags(f),v);assert.equal(f.c.snapshot().active,false);});
test('cancel with camera restores exact overview',()=>{const f=fixture(),c=cam(f);f.c.focus('plate');f.c.cancel({restoreCamera:true});assert.deepEqual(cam(f),c);});
test('dispose restores visibility without disposing geometry/material or restoring camera',()=>{const f=fixture(),v=flags(f);let disposed=0;f.parts.forEach(m=>{m.material.addEventListener('dispose',()=>disposed++);m.geometry.addEventListener('dispose',()=>disposed++);});f.c.focus('calendar');const c=cam(f);f.c.dispose();f.c.dispose();assert.deepEqual(flags(f),v);assert.deepEqual(cam(f),c);assert.equal(disposed,0);assert.equal(f.c.focus('train'),false);assert.equal(f.c.overview(),false);});
test('framed members project inside safe viewport; local pose stays fixed',()=>{const f=fixture();f.root.rotation.x=Math.PI/2;f.root.scale.set(1.2,.8,1.1);f.c.focus('train');const mesh=f.parts[2];mesh.updateWorldMatrix(true,false);const b=mesh.geometry.boundingBox;for(const x of[b.min.x,b.max.x])for(const y of[b.min.y,b.max.y])for(const z of[b.min.z,b.max.z]){const p=new Vector3(x,y,z).applyMatrix4(mesh.matrixWorld).project(f.camera);assert.ok(Math.abs(p.x)<=.650001&&Math.abs(p.y)<=.650001&&p.z>=-1&&p.z<=1,JSON.stringify(p));}});
test('invalid aspect rejects without state mutation',()=>{const f=fixture(),c=createLayerFocus({...f,getAspect:()=>NaN}),before=cam(f),v=flags(f);assert.equal(c.focus('train'),false);assert.deepEqual(cam(f),before);assert.deepEqual(flags(f),v);});
test('focus relaxes minDistance, retains maxDistance and restores limits on every exit',()=>{for(const exit of ['overview','cancel','dispose']){const f=fixture();f.controls.minDistance=9;f.controls.maxDistance=999;f.c.focus('balance');assert.equal(f.controls.minDistance,.25);assert.equal(f.controls.maxDistance,999);f.c[exit]();assert.equal(f.controls.minDistance,9);assert.equal(f.controls.maxDistance,999);}});
test('reframe uses changed aspect/fill without overwriting overview snapshot',()=>{const f=fixture(),original=cam(f),visible=flags(f);let fill=.65;const c=createLayerFocus({...f,getFrameOptions:()=>({aspect:f.camera.aspect,fill})});assert.equal(c.reframe(),false);c.focus('train');const first=cam(f);f.camera.aspect=.6;fill=.5;assert.equal(c.reframe(),true);assert.notDeepEqual(cam(f),first);c.restore({camera:true});assert.deepEqual(cam(f),original);assert.deepEqual(flags(f),visible);});
test('invalid reframe preserves active state and camera',()=>{const f=fixture();let fill=.65;const c=createLayerFocus({...f,getFrameOptions:()=>({aspect:1.2,fill})});c.focus('train');const before=cam(f),v=flags(f);fill=0;assert.equal(c.reframe(),false);assert.deepEqual(cam(f),before);assert.deepEqual(flags(f),v);});
test('reapplyVisibility repairs material-refresh visibility without reframing user orbit or replacing return state',()=>{const f=fixture(),original=cam(f),v=flags(f);assert.equal(f.c.reapplyVisibility(),false);f.c.focus('train');f.camera.position.add(new Vector3(2,1,0));f.controls.target.add(new Vector3(.1,0,0));f.camera.lookAt(f.controls.target);const orbited=cam(f);f.outer.visible=true;f.parts[0].visible=true;f.parts[2].visible=false;f.authored.visible=true;f.hidden.visible=true;assert.equal(f.c.reapplyVisibility(),true);assert.equal(f.outer.visible,false);assert.equal(f.parts[0].visible,false);assert.equal(f.parts[2].visible,true);assert.equal(f.authored.visible,false);assert.equal(f.hidden.visible,false);assert.equal(f.hiddenParent.visible,false);assert.deepEqual(cam(f),orbited);assert.equal(f.c.snapshot().selected,'train');f.c.overview();assert.deepEqual(cam(f),original);assert.deepEqual(flags(f),v);assert.equal(f.c.reapplyVisibility(),false);f.c.dispose();assert.equal(f.c.reapplyVisibility(),false);});
for(const [name,aspect,rect]of [
 ['portrait bottom exclusion',430/760,{left:0,top:0,right:1,bottom:(694-92)/760}],
 ['landscape right exclusion',740/247,{left:0,top:0,right:432/740,bottom:1}],
 ['deep asymmetric inset',1.3,{left:.12,top:.08,right:.48,bottom:.63}]
])test(name+' fits actual transformed 3D corners inside inset rectangle',()=>{
 const f=fixture(),original=cam(f),v=flags(f),p=poses(f);f.camera.aspect=aspect;
 f.root.rotation.set(.6,.4,.2);f.root.scale.set(1.2,.8,2.5);
 const c=createLayerFocus({...f,getFrameOptions:()=>({aspect,fill:.85,rect})});
 assert.equal(c.focus('train'),true);
 const mesh=f.parts[2],b=mesh.geometry.boundingBox;
 const cx=(rect.left+rect.right)/2,cy=(rect.top+rect.bottom)/2,hw=(rect.right-rect.left)*.85/2,hh=(rect.bottom-rect.top)*.85/2;
 for(const x of[b.min.x,b.max.x])for(const y of[b.min.y,b.max.y])for(const z of[b.min.z,b.max.z]){
  const ndc=new Vector3(x,y,z).applyMatrix4(mesh.matrixWorld).project(f.camera),u=(ndc.x+1)/2,w=(1-ndc.y)/2;
  assert.ok(u>=cx-hw-1e-9&&u<=cx+hw+1e-9&&w>=cy-hh-1e-9&&w<=cy+hh+1e-9&&ndc.z>=-1&&ndc.z<=1,JSON.stringify({u,w,rect}));
 }
 assert.deepEqual(poses(f),p);c.overview();assert.deepEqual(cam(f),original);assert.deepEqual(flags(f),v);
});
test('invalid safe rectangles reject initial focus and reframe without state changes',()=>{
 const f=fixture();let rect;const c=createLayerFocus({...f,getFrameOptions:()=>({aspect:f.camera.aspect,rect})});
 for(const bad of [null,{}, {left:0,top:0,right:NaN,bottom:1},{left:-.1,top:0,right:1,bottom:1},{left:0,top:0,right:1.1,bottom:1},{left:.5,top:0,right:.5,bottom:1},{left:0,top:.8,right:1,bottom:.2}]){
  rect=bad;const before=cam(f),v=flags(f);assert.equal(c.focus('train'),false);assert.deepEqual(cam(f),before);assert.deepEqual(flags(f),v);
 }
 rect=undefined;c.focus('train');const before=cam(f),v=flags(f),s=c.snapshot();rect={left:0,top:0,right:1,bottom:Infinity};assert.equal(c.reframe(),false);assert.deepEqual(cam(f),before);assert.deepEqual(flags(f),v);assert.deepEqual(c.snapshot(),s);
});
test('explicit full rect matches legacy no-rect framing',()=>{
 const a=fixture(),b=fixture(),c=createLayerFocus({...b,getFrameOptions:()=>({aspect:b.camera.aspect,fill:.65,rect:{left:0,top:0,right:1,bottom:1}})});
 a.c.focus('train');c.focus('train');for(const k of ['p','q','t'])for(let i=0;i<cam(a)[k].length;i++)assert.ok(Math.abs(cam(a)[k][i]-cam(b)[k][i])<1e-12);
});

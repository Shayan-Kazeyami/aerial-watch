import {baseline as original,candidate,verifyScope} from './assert-scope.mjs';
// CPU-only: actual source-extracted fitBounds/helper/depth with real Three classes.
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import * as vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../preview-b/releases/f3ab38493b7bc5c4af84728add913e54938d0db276143a7b765a7803f361bb44/vendor/three.module.js';
const release=new URL('../preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6/',import.meta.url);
const framing=readFileSync(new URL('assembly-framing.js',release),'utf8');
const depth=readFileSync(new URL('assembly-depth.js',release),'utf8');
function block(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i);assert(i>=0&&j>i);return s.slice(i,j).replace('export ','');}
const math={Vector3:THREE.Vector3,Ray:THREE.Ray};runInNewContext(block(framing,'export function perspectiveFrame','// Panel-only')+'\n'+depth.replace(/^import[^\n]+\n/,'').replace('export ','')+'\nglobalThis.frame=perspectiveFrame;globalThis.updateDepth=updateInspectionDepth;',math);
// Deliberately fabricated thin-object fixture, not source/project metadata.
const cap=new THREE.Box3(new THREE.Vector3(-.55,-.07,-.55),new THREE.Vector3(.55,.07,.55));
const transform=new THREE.Matrix4().makeRotationX(Math.PI/2).multiply(new THREE.Matrix4().makeTranslation(-3.5,1.5,-8));
function corners(box,matrix=new THREE.Matrix4()){const p=[];for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])p.push(new THREE.Vector3(x,y,z).applyMatrix4(matrix));return p;}
function run(source,{near=20,aspect=1.56,isolated=true,points=corners(cap,transform),direction=new THREE.Vector3(-.1,.1,-1).normalize(),target=new THREE.Vector3(0,0,-.2),layer=false,pose=null}={}){
 const camera=new THREE.PerspectiveCamera(35,aspect,near,800);const initialTarget=pose?pose.target:target;camera.position.copy(pose?pose.position:initialTarget.clone().addScaledVector(direction,90));camera.lookAt(initialTarget);camera.updateMatrixWorld(true);
 const controls={target:initialTarget.clone()},calls=[],context={THREE,camera,controls,isolated:isolated?new Set([{}]):null,model:{},explosion:{active:false,amount:0},layerFocus:layer?{selected:true,reframe(){calls.push('layer');}}:null,$:()=>({getBoundingClientRect:()=>({width:600*aspect,height:600})}),visibleFramingPoints(){return points;},perspectiveFrame:math.frame,resize(){calls.push('resize');camera.updateProjectionMatrix();},dirty:false,scale:0};
 runInNewContext(block(source,'function fitBounds(','function view(')+'\nfitBounds();',context);
 const beforeDepth={position:camera.position.clone(),target:controls.target.clone(),scale:context.scale,near:camera.near};
 const box=new THREE.Box3().setFromPoints(points).expandByScalar(isolated?.05:.5);
 const d=math.updateDepth(camera,controls.target,[box],null,isolated?{distanceFloor:.25,surfacePadding:.05}:undefined);
 const projected=points.map(p=>p.clone().project(camera));
 return {camera,controls,beforeDepth,depth:d,projected,calls};
}
function sameFrame(a,b){assert(a.beforeDepth.position.distanceTo(b.beforeDepth.position)<1e-11);assert(a.beforeDepth.target.distanceTo(b.beforeDepth.target)<1e-11);assert(Math.abs(a.beforeDepth.scale-b.beforeDepth.scale)<1e-11);}
test('baseline defect: identical thin-object bounds frame differently depending only on previous near',()=>{const close=run(original,{near:.005}),far=run(original,{near:20});assert(far.beforeDepth.position.distanceTo(close.beforeDepth.position)>30);const extent=r=>Math.max(...r.projected.map(p=>Math.abs(p.y)));assert(extent(far)<.06);assert(extent(close)>.8);});
test('isolated thin-object fit no longer depends on previous whole-watch near or repeated framing',()=>{for(const aspect of [.38,.66,1.56,2.4]){const expected=run(candidate,{near:.005,aspect});for(const near of [.005,.1,2,20,50]){const actual=run(candidate,{near,aspect});sameFrame(expected,actual);assert(actual.camera.near>0&&actual.camera.near<actual.camera.far);for(const p of actual.projected){assert(Math.abs(p.x)<=.900001&&Math.abs(p.y)<=.900001);assert(p.z>-1&&p.z<1);}const repeated=run(candidate,{near:actual.camera.near,aspect,pose:{position:actual.camera.position,target:actual.controls.target}});sameFrame(expected,repeated);}}});
test('thick and offset isolated boxes retain safe depth and full bounds in portrait/landscape',()=>{for(const aspect of [.4,1.6])for(const [lo,hi] of [[[-3,-2,-20],[3,2,20]],[[-.005,-.005,-.005],[.005,.005,.005]],[[11,3,-4],[15,7,-1]]]){const points=corners(new THREE.Box3(new THREE.Vector3(...lo),new THREE.Vector3(...hi))),a=run(candidate,{near:20,aspect,points}),b=run(candidate,{near:.005,aspect,points});sameFrame(a,b);assert(a.camera.position.distanceTo(a.controls.target)>=a.depth.minimumDistance-1e-10);for(const p of a.projected){assert(Math.abs(p.x)<=.900001&&Math.abs(p.y)<=.900001);assert(p.z>-1&&p.z<1);}}});
test('V1 failure reproduced: stale target depth can still leave tiny parts distant',()=>{const v1=original.replace('aspect:r.width/r.height,near:camera.near});\n  if(!framed)return;', 'aspect:r.width/r.height,near:isolated ? .005 : camera.near});\n  if(!framed)return;');const a=run(v1,{near:20,direction:new THREE.Vector3(0,0,1),target:new THREE.Vector3(0,0,100)});assert(Math.max(...a.projected.map(p=>Math.abs(p.y)))<.02);assert(a.controls.target.distanceTo(new THREE.Box3().setFromPoints(corners(cap,transform)).getCenter(new THREE.Vector3()))>90);});
test('isolated target-depth shifts no longer change fit; view direction and full bounds preserved',()=>{for(const direction of [new THREE.Vector3(0,0,1),new THREE.Vector3(-.1,.1,-1).normalize()])for(const aspect of [.4,1.6]){const expected=run(candidate,{aspect,direction,near:.005});for(const offset of [-100,0,100]){const target=new THREE.Vector3(0,0,-.2).addScaledVector(direction,offset),r=run(candidate,{aspect,direction,target,near:20});sameFrame(expected,r);const actualDirection=r.camera.position.clone().sub(r.controls.target).normalize();assert(actualDirection.distanceTo(direction)<1e-11);for(const p of r.projected){assert(Math.abs(p.x)<=.900001&&Math.abs(p.y)<=.900001);assert(p.z>-1&&p.z<1);}}}});
test('empty visible bounds leave camera position/target unchanged and no model parsing occurs',()=>{const r=run(candidate,{points:[]});assert.deepEqual(r.calls,[]);assert.deepEqual(r.beforeDepth.target.toArray(),[0,0,-.2]);});
test('nonisolated whole-watch framing remains byte-for-byte source behavior for all prior near values',()=>{for(const near of [.005,.1,2,20,50])for(const aspect of [.4,1.6]){const a=run(original,{near,aspect,isolated:false}),b=run(candidate,{near,aspect,isolated:false});sameFrame(a,b);assert.deepEqual(a.camera.position.toArray(),b.camera.position.toArray());assert.equal(a.camera.near,b.camera.near);assert.equal(a.camera.far,b.camera.far);}});
test('existing selected-layer reframe branch and all unrelated source bytes remain unchanged',()=>{assert.deepEqual(run(candidate,{layer:true}).calls,['layer','resize']);const before=block(original,'function fitBounds(','function view('),after=block(candidate,'function fitBounds(','function view(');verifyScope();const oldCall='const framed=perspectiveFrame(points,{position:camera.position,target:controls.target,up:camera.up,fov:camera.fov,aspect:r.width/r.height,near:camera.near});';const newCall="// Isolated bounds must not inherit a whole-watch near plane or panned target depth.\n  const framingTarget=isolated?new THREE.Box3().setFromPoints(points).getCenter(new THREE.Vector3()):controls.target;\n  const framingPosition=isolated?framingTarget.clone().add(camera.position.clone().sub(controls.target)):camera.position;\n  const framed=perspectiveFrame(points,{position:framingPosition,target:framingTarget,up:camera.up,fov:camera.fov,aspect:r.width/r.height,near:isolated ? .005 : camera.near});";assert.equal(after.replace(newCall,oldCall),before);});

test('actual integrated Reset callback preserves ordering, repeated and optional-control flows',()=>{
const baseline=original;
function handler(source){const start=source.indexOf("$('reset').onclick = () => {");const end=source.indexOf("\ndocument.addEventListener('keydown'",start);assert(start>=0&&end>start);return source.slice(start,end);}
const checks=[];
function run(source,{on=true,missing=false,repeats=1}={}){
 const events=[],nodes={};for(const id of ['reset','import-config','speed','finish','crystals','open-work','component-search','component-scope'])nodes[id]={value:'old',checked:false};
 if(!missing){nodes['power-path']={checked:on};nodes['power-path-description']={textContent:on?'Barrel → wheel train → escapement → balance.':''};}
 const s={powerPath:on,inspectionDisplay:{wireframe:true},configurationRequest:7,pendingCaptures:new Set(['import-config','other']),openWork:false,initialQuality:'detail',$:id=>nodes[id],crownInteraction:{reset(){events.push('crown');}},clock:{setSpeed(n){events.push(['speed',n]);}},resetExplosion(v){events.push(['explosion',v,s.powerPath,nodes['power-path']?.checked,nodes['power-path-description']?.textContent]);},stopTour(){events.push('tour');},resetMotion(){events.push('motion');},renderingQuality(q){events.push(['quality',q]);},clearSelection(){events.push(['materials',s.powerPath]);},renderExplorer(){events.push('explorer');},showAll(){events.push(['showAll',s.powerPath]);},announce(v){events.push(['announce',v]);}};
 vm.createContext(s);vm.runInContext(handler(source),s);for(let i=0;i<repeats;i++)nodes.reset.onclick();return{s,nodes,events};
}
const bug=run(baseline);assert.equal(bug.s.powerPath,true);assert.equal(bug.nodes['power-path'].checked,true);assert(bug.nodes['power-path-description'].textContent);assert.deepEqual(bug.events.find(e=>Array.isArray(e)&&e[0]==='materials'),['materials',true]);checks.push('baseline bug reproduced: reset retains highlights/UI');
for(const [name,opts]of [['highlighted',{}],['imported highlighted',{on:true}],['default',{on:false}],['repeated',{repeats:2}],['missing optional controls',{missing:true}]]){
 const r=run(candidate,opts),n=opts.repeats||1;assert.equal(r.s.powerPath,false);if(!opts.missing){assert.equal(r.nodes['power-path'].checked,false);assert.equal(r.nodes['power-path-description'].textContent,'');}
 for(const e of r.events.filter(e=>Array.isArray(e)&&['explosion','materials','showAll'].includes(e[0]))){assert.equal(e[e[0]==='explosion'?2:1],false);if(e[0]==='explosion'&&!opts.missing){assert.equal(e[3],false);assert.equal(e[4],'');}}
 assert.equal(r.s.configurationRequest,7+n);assert(!r.s.pendingCaptures.has('import-config'));assert(r.s.pendingCaptures.has('other'));assert.equal(r.nodes['import-config'].value,'');assert.equal(r.nodes.speed.value,'1');assert.equal(r.s.openWork,true);assert.equal(r.nodes.finish.checked,true);assert.equal(r.nodes.crystals.checked,true);assert.equal(r.nodes['component-search'].value,'');assert.equal(r.nodes['component-scope'].value,'all');assert.equal(r.events.filter(e=>e==='motion').length,n);assert.equal(r.events.filter(e=>Array.isArray(e)&&e[0]==='quality'&&e[1]==='detail').length,n);checks.push(name+': clear before explosion/material refresh; original reset effects preserved');
}
// Exact outside-handler bytes ensure Show All, view switches and all other code are untouched.
verifyScope();checks.push('strict full three-reviewed-patch scope; unrelated bytes exact');
const inserted="\n  powerPath=false;if($('power-path'))$('power-path').checked=false;if($('power-path-description'))$('power-path-description').textContent='';\n  ";assert.equal(handler(candidate).replace(inserted,''),handler(baseline));checks.push('only three reset state writes inserted');

});

test('actual integrated selection text fallback and attachment/identity flows',()=>{
const baseline=original;
function block(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i);assert(i>=0&&j>i);return s.slice(i,j);}
function selectText(source,support){const nodes={},events=[],mesh={userData:{sourceIndex:12,description:'Contre pivot',...(support===undefined?{}:{support})}};const group={label:'Cap jewel · OM10 #12',parts:[mesh],key:'source-12'};const c={$:id=>nodes[id]??={hidden:false,disabled:false,checked:false,textContent:'',querySelectorAll(){return[];}},endLayerFocus(){events.push('layer');},stopTour(){events.push('tour');},groups:[group],isolated:null,openWork:true,sourceNeedsBaseline(){return false;},replacedSources:new Set(),premiumFace:null,clearSelection(){events.push('clear');},inspectionBaseline:false,selected:[],movementViews:[],currentView:'interior',updateMaterials(){events.push('materials');},visibility(){events.push('visibility');},fitBounds(){events.push('fit');},view(){events.push('view');},announce(v){events.push(v);}};vm.createContext(c);vm.runInContext(block(source,'function select(mesh) {','function showAll() {')+'\nglobalThis.choose=select;',c);c.choose(mesh);return{c,nodes,events};}
const b=selectText(baseline);assert.equal(b.nodes['part-support'].textContent,'Original OM10 component â€” original placement preserved');
for(const support of [undefined,'','Bridge A']){const a=selectText(baseline,support),b=selectText(candidate,support);assert.equal(b.nodes['part-support'].textContent,support?'Attachment: '+support:'Original OM10 component \u2014 original placement preserved');assert.equal(b.nodes['part-name'].textContent,'Cap jewel · OM10 #12');assert.equal(b.nodes['part-role'].textContent,'Contre pivot');assert.deepEqual(b.events,a.events);assert.equal(b.c.selected[0].userData.sourceIndex,12);}
verifyScope();

});

test('entire candidate equals exactly the three approved source edits',verifyScope);

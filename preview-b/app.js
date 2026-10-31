import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const $=id=>document.getElementById(id), reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let needsRender=true;
const scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(32,1,.1,500);
const renderer=new THREE.WebGLRenderer({canvas:$('scene'),antialias:true,alpha:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.85;
const pmrem=new THREE.PMREMGenerator(renderer), room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;room.dispose();pmrem.dispose();
scene.environmentIntensity=.6;
scene.add(new THREE.HemisphereLight(0xf5f3e7,0x233024,.35));
const key=new THREE.DirectionalLight(0xffe8c5,1.5);key.position.set(12,35,25);scene.add(key);
const rim=new THREE.DirectionalLight(0xdce8ed,1.0);rim.position.set(-30,10,-20);scene.add(rim);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.07;controls.minDistance=18;controls.maxDistance=170;controls.enablePan=true;controls.autoRotateSpeed=.55;
controls.addEventListener('change',()=>needsRender=true);
document.addEventListener('click',()=>needsRender=true);document.addEventListener('input',()=>needsRender=true);
const mount=new THREE.Group();mount.rotation.z=Math.PI;scene.add(mount);
let model=null, parts=[],summary=null,selected=null,isolated=false,target=0,amount=0,playing=false,playDirection=1,loadId=0,loading=true,currentVariant='automatic',lastTime=0,lastFrame=0;
let motionEnabled=!reduced,motionTime=0,motionDirty=true;
function motionUI(){ $('motion').setAttribute('aria-pressed',String(motionEnabled));$('motion').textContent=motionEnabled?'Pause motion':'Animate';$('motion-note').hidden=!motionEnabled; }
motionUI();
function prepareMotion(){
 const groups=[{name:'OM10-00148',anchor:'OM10-00149',rate:1/3600},{name:'OM10-00160',anchor:'OM10-00161',rate:-7.5/3600},{name:'OM10-00163',anchor:'OM10-00164',rate:1/60},{name:'OM10-00145',anchor:'OM10-00146',rate:-.175}];
 for(const p of parts){delete p.userData.motion;p.rotation.set(0,0,0);}
 function find(n,name){if(n.name===name)return n;for(const c of n.children||[]){const hit=find(c,name);if(hit)return hit;}return null;}
 for(const g of groups){const node=find(summary.hierarchy,g.name),anchor=parts.find(p=>p.userData.partNumber===g.anchor);if(!node||!anchor)continue;for(const i of node.meshes){const p=parts.find(p=>p.userData.sourceIndex===i);if(p)p.userData.motion={kind:'wheel',rate:g.rate,pivot:anchor.userData.base};}}
 const anchor=parts.find(p=>p.userData.partNumber==='OM10-00112');
 if(anchor)for(const p of parts)if(['OM10-00112','OM10-00113','OM10-00110','OM10-00111'].includes(p.userData.partNumber))p.userData.motion={kind:'balance',pivot:anchor.userData.base};
 motionDirty=true;
}
function updateParts(){
 for(const p of parts){const b=p.userData.base,m=p.userData.motion;let x=b.x,z=b.z;
 if(m){const angle=m.kind==='balance'?Math.sin(motionTime*Math.PI*2*3.5)*THREE.MathUtils.degToRad(210):motionTime*Math.PI*2*m.rate;const dx=b.x-m.pivot.x,dz=b.z-m.pivot.z; x=m.pivot.x+Math.cos(angle)*dx+Math.sin(angle)*dz;z=m.pivot.z-Math.sin(angle)*dx+Math.cos(angle)*dz;p.rotation.y=angle;}
 else p.rotation.y=0;
 const lift=b.y*.12+Math.round(b.y/.6)*1.8,radial=amount*.13;
 p.position.set(x+b.x*radial,b.y+lift*amount,z+b.z*radial);
 }
 motionDirty=false;needsRender=true;
}
const loader=new GLTFLoader(),cache=new Map();
function home(side='default'){
 const d=amount*30;
 if(side==='front')camera.position.set(0,65+d,.001);
 else if(side==='back')camera.position.set(0,-65-d,.001);
 else camera.position.set(33+d*.3,43+d*.6,48+d*.5);
 if($('viewport').clientWidth<600)camera.position.multiplyScalar(1.4);
 camera.up.set(0,0,-1);controls.target.set(0,0,-1);controls.update();
}
home();
function resize(){const r=$('viewport').getBoundingClientRect();camera.aspect=r.width/r.height;camera.updateProjectionMatrix();renderer.setSize(r.width,r.height,false);needsRender=true;}
new ResizeObserver(resize).observe($('viewport'));resize();
function available(enabled){document.querySelectorAll('.atelier button,.atelier select,#explode').forEach(el=>el.disabled=!enabled);}
function setAmount(v){target=THREE.MathUtils.clamp(v,0,1);$('explode').value=Math.round(target*100);$('percent').textContent=Math.round(target*100)+'%';}
function setPlaying(v){playing=v;$('play').textContent=v?'Ⅱ':'▷';$('play').setAttribute('aria-label',v?'Pause exploded view':'Play exploded view');}
function clearSelection(){if(selected){selected.traverse(n=>{if(n.isMesh){n.material.emissive.setHex(0);n.material.emissiveIntensity=0;}});}selected=null;isolated=false;for(const p of parts)p.visible=true;$('selection').hidden=true;$('isolate').setAttribute('aria-pressed','false');$('isolate').textContent='Isolate component';document.querySelectorAll('.part-row.active').forEach(el=>el.classList.remove('active'));}
function selectPart(p){clearSelection();selected=p;p.traverse(n=>{if(n.isMesh){n.material.emissive.setHex(0xa97d30);n.material.emissiveIntensity=.33;}});const e=p.userData;$('selection-name').textContent=e.partNumber;$('selection-description').textContent=e.description;$('selection-dimensions').textContent=e.dimensions.map(n=>n.toFixed(2)).join(' × ')+' mm';$('selection').hidden=false;document.querySelector(`[data-part="${e.sourceIndex}"]`)?.classList.add('active');}
function fillParts(){const q=$('part-search').value.toLowerCase();$('part-list').replaceChildren();for(const p of parts){const e=p.userData;if(!`${e.partNumber} ${e.description} ${e.sourceIndex}`.toLowerCase().includes(q))continue;const button=document.createElement('button');button.className='part-row';button.dataset.part=e.sourceIndex;button.textContent=e.partNumber+' / '+String(e.sourceIndex+1).padStart(3,'0');const desc=document.createElement('span');desc.textContent=e.description;button.append(desc);button.onclick=()=>selectPart(p);if(p===selected)button.classList.add('active');$('part-list').append(button);}}
async function loadVariant(id){
 const request=++loadId;loading=true;available(false);setPlaying(false);clearSelection();$('loading').hidden=false;$('loading').querySelector('b').textContent='Preparing the movement';$('load-detail').textContent='Loading original CAD geometry…';
 try{
  if(!cache.has(id)){
   const [gltf,meta]=await Promise.all([loader.loadAsync(`assets/${id}.glb`,e=>{$('load-detail').textContent=`Loading geometry · ${(e.loaded/1048576).toFixed(1)} MB`; }),fetch(`assets/${id}-parts.json`).then(r=>{if(!r.ok)throw Error('Component metadata could not load');return r.json();})]);
   cache.set(id,{gltf,meta});
  }
  if(request!==loadId)return;
  if(model)mount.remove(model);const entry=cache.get(id);model=entry.gltf.scene;summary=entry.meta;parts=[];
  model.traverse(n=>{
   if(n.userData.sourceIndex!==undefined){n.userData.base=new THREE.Vector3(...n.userData.sourceCenter);n.position.copy(n.userData.base);parts.push(n);}
   if(n.isMesh){if(!n.userData.materialPrepared){n.material=n.material.clone();n.userData.materialPrepared=true;}n.material.envMapIntensity=.8;}
  });
  parts.sort((a,b)=>a.userData.sourceIndex-b.userData.sourceIndex);mount.add(model);currentVariant=id;needsRender=true;prepareMotion();
  $('part-count').textContent=parts.length;$('fact-parts').textContent=parts.length;$('variant-caption').textContent=id==='automatic'?'AUTOMATIC BETA':id==='manual-a'?'MANUAL A':'MANUAL B';$('part-search').value='';fillParts();amount=target;home();loading=false;available(true);$('loading').hidden=true;motionUI();
 }catch(err){console.error(err);loading=true;$('loading').querySelector('b').textContent='The movement could not load';$('load-detail').textContent='Check that the local server is running, then reload the page.';$('variant').disabled=false;}
}
$('variant').onchange=e=>{setAmount(0);loadVariant(e.target.value);};
$('explode').oninput=e=>{setPlaying(false);setAmount(e.target.value/100);};
$('explore').onclick=()=>{setAmount(target>.45?0:1);setPlaying(false);home();};
$('play').onclick=()=>{if(!playing){playDirection=target>=.99?-1:1;setPlaying(true);}else setPlaying(false);};
$('motion').onclick=()=>{motionEnabled=!motionEnabled;motionUI();};
$('front').onclick=()=>home('front');$('back').onclick=()=>home('back');
$('orbit').onclick=()=>{controls.autoRotate=!controls.autoRotate;$('orbit').setAttribute('aria-pressed',String(controls.autoRotate));};
$('reset').onclick=()=>{clearSelection();setPlaying(false);setAmount(0);motionEnabled=false;motionTime=0;motionDirty=true;motionUI();controls.autoRotate=false;$('orbit').setAttribute('aria-pressed','false');home();};
$('parts-toggle').onclick=()=>{const open=$('parts-panel').hidden;$('parts-panel').hidden=!open;$('parts-toggle').setAttribute('aria-expanded',String(open));if(open)$('part-search').focus();};
$('close-parts').onclick=()=>{$('parts-panel').hidden=true;$('parts-toggle').setAttribute('aria-expanded','false');$('parts-toggle').focus();};
$('part-search').oninput=fillParts;$('clear-selection').onclick=clearSelection;
$('isolate').onclick=()=>{if(!selected)return;isolated=!isolated;for(const p of parts)p.visible=!isolated||p===selected;$('isolate').setAttribute('aria-pressed',String(isolated));$('isolate').textContent=isolated?'Show all components':'Isolate component';};
document.addEventListener('keydown',e=>{if(e.key==='Escape'){clearSelection();$('parts-panel').hidden=true;$('parts-toggle').setAttribute('aria-expanded','false');}});
let down=null;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
renderer.domElement.addEventListener('pointerup',e=>{if(loading||!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=renderer.domElement.getBoundingClientRect();const ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=ray.intersectObjects(parts,true).find(h=>{let n=h.object;while(n&&n!==model){if(!n.visible)return false;n=n.parent;}return true;});if(hit){let n=hit.object;while(n&&n.userData.sourceIndex===undefined)n=n.parent;if(n)selectPart(n);}else clearSelection();down=null;});
function frame(t){requestAnimationFrame(frame);if(t-lastFrame<30)return;const elapsed=Math.min((t-lastTime)/1000,.25),dt=Math.min(elapsed,.08);lastTime=t;lastFrame=t;if(document.hidden)return;if(playing&&!loading){setAmount(target+dt*.15*playDirection);if(target===1||target===0)playDirection*=-1;}const moving=Math.abs(amount-target)>.00001;if(moving){amount=reduced?target:THREE.MathUtils.damp(amount,target,6,dt);if(Math.abs(amount-target)<.00001)amount=target;}if(motionEnabled&&!loading){motionTime+=elapsed;motionDirty=true;}if(moving||motionDirty)updateParts();controls.update();if(needsRender){renderer.render(scene,camera);needsRender=false;}}
requestAnimationFrame(frame);
document.addEventListener('visibilitychange',()=>{if(document.hidden)setPlaying(false);});
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();$('loading').hidden=false;$('loading').querySelector('b').textContent='The 3D view was interrupted';$('load-detail').textContent='Reload this page to restore the movement.';available(false);});
// Read-only runtime snapshot for geometry and interaction verification.
window.om10Inspect=()=>({variant:currentVariant,loading,meshCount:parts.length,target,amount,motionEnabled,motionTime,animatedParts:parts.filter(p=>p.userData.motion).length,balanceHz:3.5,selected:selected?.userData.sourceIndex??null,isolated,visibleParts:parts.filter(p=>p.visible).length,positions:parts.map(p=>({id:p.userData.sourceIndex,base:p.userData.base.toArray(),current:p.position.toArray(),angle:p.rotation.y})),triangles:renderer.info.render.triangles,camera:camera.position.toArray()});
loadVariant('automatic');


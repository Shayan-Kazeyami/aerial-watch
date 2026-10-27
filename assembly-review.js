import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {SSAOPass} from 'three/addons/postprocessing/SSAOPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {createAssemblyMotion, sampleMechanicalTime} from './assembly-motion.js';
import {createAssemblyMaterials,cloneAssemblyMaterial} from './assembly-materials.js';
import {createAssemblyLighting} from './assembly-lighting.js';
import {createDialDetails} from './assembly-dial.js';
import {createOpenFrontFrame} from './assembly-open-front.js';
import {createQualityDesign} from './assembly-design.js';
import {updateInspectionDepth} from './assembly-depth.js';
import {createRefractionAwareAO} from './assembly-glass-ao.js';
import {createPresentationClock} from './assembly-clock.js';
import {partVisible,createVariantManifest,createResourceScope,createObjectTreeDisposer,disposeObjectTree} from './assembly-state.js';
import {loadGLTFAsset,loadProgressiveAssembly} from './assembly-loading.js';
import {createPerformanceMonitor} from './assembly-performance.js';
import {RENDER_PROFILES,resolveRenderResolution} from './assembly-resolution.js';
import {createCrownInteraction,createCrownVisual} from './assembly-crown.js';
import {createCaptureProvenance,embedPNGConfiguration} from './assembly-capture-provenance.js';
import {createCanvasRecorder} from './assembly-recording.js';
import {POWER_PATH,createTourSequence,restoresExterior,sourceNeedsBaseline,validateViewConfiguration} from './assembly-story.js';
import {createViewerLifecycle} from './assembly-lifecycle.js';
import {createFormDetails} from './assembly-form-details.js';
import {createLeatherDetails} from './assembly-leather-details.js';
import {createFrontArchitecture} from './assembly-front-architecture.js';
import {createAssemblyEscapement} from './assembly-escapement.js';
import {createAssemblyCalendar} from './assembly-calendar.js';
import {createAssemblyWinding} from './assembly-winding.js';
import {createAssemblySetting} from './assembly-setting.js';
import {createAssemblySettingEngagement} from './assembly-setting-engagement.js';
import {createCasebackFinish} from './assembly-caseback-finish.js';

const $ = id => document.getElementById(id), scene = new THREE.Scene();
const bootTime=performance.now(),clock=createPresentationClock(),resources=createResourceScope(),performanceMonitor=createPerformanceMonitor();
scene.background = new THREE.Color('#171a19');
scene.fog = new THREE.Fog('#171a19',350,900);
const renderer = new THREE.WebGLRenderer({canvas: $('assembly-canvas'), antialias: true, powerPreference:'high-performance'});
// Count the entire composed frame, including transmission, shadows and AO.
renderer.info.autoReset=false;
renderer.setPixelRatio(2);
renderer.transmissionResolutionScale=2;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const finishes = createAssemblyMaterials(renderer);
scene.environment = finishes.environment; scene.environmentIntensity = .85;
const camera = new THREE.PerspectiveCamera(32,1,.1,800);
const lighting=createAssemblyLighting(scene,{renderer}),{key,floor}=lighting;
const composer = new EffectComposer(renderer);
composer.renderTarget1.samples = composer.renderTarget2.samples = Math.min(4,renderer.capabilities.maxSamples);
composer.addPass(new RenderPass(scene,camera));
const ao = new SSAOPass(scene,camera,1,1,24);
ao.kernelRadius = 1.2; ao.minDistance = .000025; ao.maxDistance = .006;
composer.addPass(ao); composer.addPass(new OutputPass());
const controls = new OrbitControls(camera,renderer.domElement);
renderer.domElement.style.touchAction='pan-y';
resources.own('WebGL renderer',()=>renderer.dispose());
resources.own('studio environment and finish library',()=>finishes.dispose());
resources.own('post-processing composer',()=>{ao.dispose();composer.passes.forEach(pass=>pass!==ao&&pass.dispose?.());composer.dispose();});
resources.own('orbit controls',()=>controls.dispose());
resources.own('studio lighting and floor',()=>lighting.dispose());
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
controls.enableDamping = !reducedMotion.matches; controls.dampingFactor = .09; controls.minZoom = .4; controls.maxZoom = 12;
controls.minDistance = 9; controls.maxDistance = 480;
reducedMotion.addEventListener('change', event => {
  controls.enableDamping = !event.matches;
  if (event.matches) { $('animate-movement').checked = false; $('animate').checked = false; stopTour(); cameraTween = null; setClockPlayback(); }
  dirty = true;
});
controls.addEventListener('change', () => { dirty = true; });

let loading = true, failed = false, contextLost = false, dirty = true, firstRender = true;
let loadPhase='poster',proposalReady=false,proposalLoading=false,loadWarnings=[],variantManifest=null,qualityDesign;
let source = [], exterior = [], selected = [], groups = [], isolated = null, model;
let depthBounds=[];
let interiorView=false,dialDetails,dialFace;
let openWork=true,openDialDetails,openFrontFrame,openPlates=[],craftParts=[],formDetails,leatherDetails,frontArchitecture,frontArchitectureLoading=false,casebackFinish;
const replacedSources=new Set([0,155]);
const openFrontActive=()=>proposalReady&&openWork&&!$('movement-only').checked&&!isolated;
function syncFrontDetails() {
  const active=openFrontActive(),finished=$('finish').checked;
  // Restore the calendar before the older form layer restores its own source.
  if(!active)frontArchitecture?.setEnabled(false);
  formDetails?.setEnabled(active);
  if(active)frontArchitecture?.setEnabled(true);
  crownVisual?.setEnabled(active);
  if(dialDetails) dialDetails.group.visible=finished&&!!dialFace?.visible&&!active;
  if(openDialDetails) openDialDetails.group.visible=finished&&active;
  if(openFrontFrame) {openFrontFrame.group.visible=active;openFrontFrame.setFinish(finished);}
  qualityDesign?.setEnabled(active,{interior:interiorView});qualityDesign?.setFinish(finished);
  if(active&&finished){
    for(const mesh of openFrontFrame?.group.children||[]){
      mesh.userData.finishFaceAxis=[0,0,1];
      if(/polished|hairline/i.test(mesh.name))mesh.userData.finishKind='polished';
      mesh.material=finishes.apply(mesh);
    }
    for(const mesh of qualityDesign?.meshes||[]){
      mesh.userData.finishFaceAxis=/Seconds sleeve/.test(mesh.name)?[0,1,0]:[0,0,1];
      mesh.material=finishes.apply(mesh);
    }
  }
  for(const part of craftParts)part.visible=active&&!interiorView;
  if(active&&!interiorView&&craftParts.length)for(const part of exterior)if(['STRAP-UPPER','STRAP-LOWER'].includes(part.userData.assemblyId))part.visible=false;
}
let scale = 78, currentView = 'three-quarter', elapsed = 0;
let mechanism,escapement,calendar,winding,setting,settingEngagement,handClockOrigin=0, mechanismElapsed = 0, balanceElapsed = 0,crownVisual;
let settingSeconds=0,calendarState=null,engagementState=null;
const sourceRestMatrices=new Map();
let cameraTween = null, tour = false, animationFrame=0;
const tourSequence=createTourSequence();let powerPath=false;
const lifecycle=createViewerLifecycle({pause:()=>{clock.setHidden(true);performanceMonitor.breakCadence();},
  resume:()=>{clock.setHidden(document.hidden);last=frameWindow=performance.now();dirty=true;},
  dispose:()=>{cancelAnimationFrame(animationFrame);try{resources.dispose();}catch(error){console.error('Viewer resource cleanup failed.',error);}}});
const assetOptions=()=>({loader:new GLTFLoader(),signal:lifecycle.signal,disposeUnused:gltf=>disposeObjectTree(gltf.scene)});
const captureProvenance=createCaptureProvenance({signal:lifecycle.signal}),pendingCaptures=new Set();
let quality='detail', renderedFrames=0, frameWindow=performance.now();
const qualityProfiles=RENDER_PROFILES;
const detailSizes = {face:[45,45],interior:[45,45],crown:[18,20],lug:[34,30],buckle:[34,30],balance:[15,14],train:[24,23],winding:[17,18]};
const detailViews = Object.keys(detailSizes);
const movementViews = ['balance','train','winding'];
const interiorOmissions=/^(CASEBACK|BACK-SCREW|REAR-CRYSTAL|STRAP|SPRINGBAR|KEEPER|BUCKLE)/;
const pinPositions={balance:new THREE.Vector3(-3.514,8.063,-2.23),train:new THREE.Vector3(-8,0,-2.3),winding:new THREE.Vector3(6.5,-3.5,-2.4)};
function updatePins() {
  // Showcase focus choices live with the other controls, away from the canvas.
  if($('interior-pins').dataset.controlsInline==='true'){$('interior-pins').hidden=!interiorView;return;}
  const rearFacing=camera.position.clone().sub(controls.target).normalize().z<-.35;
  const show=interiorView&&!isolated&&currentView==='interior'&&!cameraTween&&rearFacing; $('interior-pins').hidden=!show;
  if(!show) return;
  const r=$('stage').getBoundingClientRect();
  for(const button of $('interior-pins').querySelectorAll('[data-pin]')) {
    const point=pinPositions[button.dataset.pin].clone().project(camera);
    button.hidden=point.z< -1||point.z>1||Math.abs(point.x)>.94||Math.abs(point.y)>.94;
    button.style.left=`${(point.x+1)*r.width/2}px`; button.style.top=`${(1-point.y)*r.height/2}px`;
  }
}
const baseMaterials = new WeakMap(), finishMaterials = new WeakMap(), highlights = [];
const hands = [], axis = new THREE.Vector3(0,1,0), turn = new THREE.Quaternion();
const meshes = () => [...source,...exterior];
const eachMaterial = (material,fn) => Array.isArray(material) ? material.map(fn) : fn(material);
const announce = message => { $('viewer-status').textContent = message; };
function stopTour() { tour = false;tourSequence.stop(); cameraTween = null; $('tour').setAttribute('aria-pressed','false'); $('tour').textContent = 'Studio tour'; }
controls.addEventListener('start', () => { stopTour(); cameraTween = null; });
function fail(message,error) {
  failed = true; loadPhase='error'; $('loading').hidden = false; $('load-message').textContent = message; $('retry').hidden = false;
  $('inspection-controls').disabled = true; $('view-controls').disabled = true;
  $('assembly-canvas').setAttribute('aria-busy','false'); announce(message);
  if (error) console.error(error);
}
$('retry').onclick = () => location.reload();
renderer.domElement.addEventListener('webglcontextlost', event => {
  event.preventDefault(); contextLost = true;
  fail('The graphics context was lost. Reload the viewer to restore it. Static inspection renders remain available below.');
});
renderer.domElement.addEventListener('webglcontextrestored', () => {
  $('load-message').textContent = 'Graphics are available again. Reload the viewer to restore the assembly.';
});
function resize() {
  const r = $('stage').getBoundingClientRect(); if (!r.width || !r.height) return;
  const aspect = r.width/r.height;
  const resolution=resolveRenderResolution({width:r.width,height:r.height,quality,devicePixelRatio:window.devicePixelRatio||1,maxTextureSize:renderer.capabilities.maxTextureSize,maxSamples:renderer.capabilities.maxSamples});
  if(Math.abs(renderer.getPixelRatio()-resolution.pixelRatio)>.00001){renderer.setPixelRatio(resolution.pixelRatio);composer.setPixelRatio(resolution.pixelRatio);}
  renderer.transmissionResolutionScale=resolution.transmissionScale;
  renderer.setSize(r.width,r.height,false); composer.setSize(r.width,r.height);
  camera.aspect = aspect;
  camera.updateProjectionMatrix(); dirty = true;
}
function renderingQuality(name) {
  const profile=qualityProfiles[name]; if(!profile) return;
  quality=name; $('render-quality').value=name;
  ao.enabled=profile.ao; renderer.shadowMap.enabled=profile.shadows; key.castShadow=profile.shadows;
  const samples=Math.min(profile.samples,renderer.capabilities.maxSamples);
  for(const target of [composer.renderTarget1,composer.renderTarget2]) if(target.samples!==samples) { target.samples=samples; target.dispose(); }
  if(!profile.shadows && key.shadow.map) { key.shadow.map.dispose(); key.shadow.map=null; }
  renderedFrames=0; frameWindow=performance.now(); resize();
  $('render-status').textContent=`${profile.label} · measuring playback…`;
  announce(`${profile.label} rendering enabled. Every movement and exterior component is retained.`);
}
$('render-quality').onchange=()=>renderingQuality($('render-quality').value);
const stageObserver=new ResizeObserver(() => {
  resize();
  if (loading || !model) return;
  // Finish any in-flight shot before fitting its new aspect ratio. Otherwise
  // the next animation frame would restore the old, clipped camera distance.
  if (cameraTween) {
    camera.position.copy(cameraTween.toPosition); controls.target.copy(cameraTween.toTarget); cameraTween=null;
    camera.lookAt(controls.target);
  }
  if (!isolated && detailViews.includes(currentView) && (movementViews.includes(currentView) || !$('movement-only').checked)) fitDetail(currentView);
  else fitBounds();
});stageObserver.observe($('stage'));resources.own('stage resize observer',()=>stageObserver.disconnect());
function fitDetail(name) {
  const [height,width]=detailSizes[name],r=$('stage').getBoundingClientRect();
  if(!r.width || !r.height) return;
  const direction=camera.position.clone().sub(controls.target).normalize();
  // Narrow face/rear framing includes the offset crown beyond the case rim.
  // Macro dimensions and desktop composition retain their authored bounds.
  const framedWidth=r.width<600&&['face','interior'].includes(name)?52:width;
  scale=Math.max(height,framedWidth/(r.width/r.height)); camera.zoom=1;
  camera.position.copy(controls.target).addScaledVector(direction,scale/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))));
  camera.lookAt(controls.target); resize();
}
function fitBounds() {
  if (!model) return;
  const r = $('stage').getBoundingClientRect(); if (!r.width || !r.height) return;
  model.updateMatrixWorld(true); camera.updateMatrixWorld(true);
  const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0);
  const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1);
  let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
  for (const mesh of meshes()) {
    if (!mesh.visible) continue;
    const box = new THREE.Box3().setFromObject(mesh);
    for (const x of [box.min.x,box.max.x]) for (const y of [box.min.y,box.max.y]) for (const z of [box.min.z,box.max.z]) {
      const p = new THREE.Vector3(x,y,z).sub(controls.target), px = p.dot(right), py = p.dot(up);
      xmin = Math.min(xmin,px); xmax = Math.max(xmax,px); ymin = Math.min(ymin,py); ymax = Math.max(ymax,py);
    }
  }
  if (!Number.isFinite(xmin)) return;
  const offset = right.multiplyScalar((xmin+xmax)/2).add(up.multiplyScalar((ymin+ymax)/2));
  controls.target.add(offset); camera.position.add(offset);
  scale = Math.max(.3,(ymax-ymin)/.84,(xmax-xmin)/(r.width/r.height)/.84); camera.zoom = 1;
  const direction = camera.position.clone().sub(controls.target).normalize();
  let distance = scale/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2)));
  camera.aspect = r.width/r.height; camera.updateProjectionMatrix();
  const points = [];
  for (const mesh of meshes()) if (mesh.visible) {
    const position = mesh.geometry.attributes.position, stride = Math.max(1,Math.ceil(position.count/220));
    for (let index=0;index<position.count;index+=stride) points.push(new THREE.Vector3().fromBufferAttribute(position,index).applyMatrix4(mesh.matrixWorld));
  }
  for (let step=0;step<4;step++) {
    camera.position.copy(controls.target).addScaledVector(direction,distance); camera.lookAt(controls.target); camera.updateMatrixWorld(true);
    let extent = 0;
    for (const point of points) { const projected = point.clone().project(camera); extent = Math.max(extent,Math.abs(projected.x)/.87,Math.abs(projected.y)/.87); }
    if (Math.abs(extent-1)<.01) break; distance *= extent;
  }
  camera.position.copy(controls.target).addScaledVector(direction,distance); camera.lookAt(controls.target); resize();
}
function view(name, transition = true) {
  if (loading || failed) return;
  const fromPosition = camera.position.clone(), fromTarget = controls.target.clone();
  currentView = name;
  if((restoresExterior(name)||name==='crown')&&(name!=='showcase'||!$('movement-only').checked)){interiorView=false;isolated=null;$('movement-only').checked=false;visibility();}
  const shotLighting=lighting.applyShot(name,{instant:!transition||reducedMotion.matches});
  Object.assign(ao,shotLighting.ao);key.castShadow=qualityProfiles[quality].shadows;
  const target = new THREE.Vector3(0,0,-16), direction = new THREE.Vector3(-.46,.22,1);
  if (name === 'showcase') direction.set(-.48,.32,$('movement-only').checked ? -1 : 1);
  if (name === 'front') direction.set(0,0,1);
  if (name === 'side') direction.set(1,.015,.04);
  if (name === 'back') direction.set(-.1,.12,-1);
  if (name === 'face') {
    interiorView=false; $('movement-only').checked=false; isolated=null; visibility();
    target.set(0,0,3.5); direction.set(.035,.065,1);
  }
  if (name === 'interior') {
    interiorView=true; $('movement-only').checked=false; isolated=null; visibility();
    target.set(0,0,-.2); direction.set(-.1,.1,-1);
  }
  if (name === 'lug') { target.set(0,22.4,-.95); direction.set(-.5,.45,1); }
  if (name === 'crown') {target.set(21,0,-.2);direction.set(.8,.16,1);}
  if (name === 'buckle') { target.set(0,-14,-43); direction.set(-.3,-.45,-1); }
  if ($('movement-only').checked) target.set(0,0,.5);
  if (movementViews.includes(name)) {
    if(!$('movement-only').checked) interiorView=true;
    isolated = null; visibility();
    target.set(...(name === 'balance' ? [-3.514,8.063,-.3] : name === 'train' ? [-7.2,-.7,-.2] : [6.5,-3.5,-1.9])); direction.set(-.15,.12,-1);
  }
  camera.zoom = 1; controls.target.copy(target); camera.position.copy(target).addScaledVector(direction.normalize(),155);
  camera.lookAt(target); controls.update();
  if (detailViews.includes(name) && !isolated && (movementViews.includes(name) || !$('movement-only').checked)) fitDetail(name);
  else fitBounds();
  document.querySelectorAll('[data-view]').forEach(button => {
    const active = button.dataset.view === name;
    button.classList.toggle('active',active); button.setAttribute('aria-pressed',String(active));
  });
  $('interior-guide').hidden=!interiorView;
  const explanations={balance:'Follow the balance rim and anchored hairspring. Its bearing cap sits above the staff.',
    train:'The connected train advances in short releases. Its original bridges and bearings remain in place.',
    winding:'The barrel drum feeds the train. The arbor, ratchet and winding wheels stay held while the watch runs.'};
  $('interior-description').textContent=explanations[name]||'The rear cover is removed to reveal the original movement, held inside its case.';
  document.querySelectorAll('[data-focus]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.focus===name)));
  if (transition && !reducedMotion.matches) {
    cameraTween = {fromPosition,fromTarget,toPosition:camera.position.clone(),toTarget:controls.target.clone(),elapsed:0,duration:tour ? 2.8 : .85};
    const fromOffset = fromPosition.clone().sub(fromTarget), toOffset = camera.position.clone().sub(controls.target);
    cameraTween.fromDistance = fromOffset.length(); cameraTween.toDistance = toOffset.length();
    cameraTween.fromDirection = fromOffset.normalize(); cameraTween.rotation = new THREE.Quaternion().setFromUnitVectors(cameraTween.fromDirection,toOffset.normalize());
    camera.position.copy(fromPosition); controls.target.copy(fromTarget); camera.lookAt(controls.target);
  } else cameraTween = null;
}
for (const button of document.querySelectorAll('[data-view]')) button.onclick = () => {
  document.querySelector('.camera-more')?.removeAttribute('open');
  stopTour();
  if (['showcase','three-quarter','back','lug','buckle'].includes(button.dataset.view)) {
    interiorView=false; isolated=null; $('movement-only').checked=false; visibility();
  }
  view(button.dataset.view);
};
for(const button of document.querySelectorAll('[data-pin],[data-focus]')) button.onclick=()=>{stopTour();view(button.dataset.pin||button.dataset.focus);};
$('interior-overview').onclick=()=>{stopTour();view('interior');};
function tourView() {
  const shot=tourSequence.snapshot();
  isolated=null; clearSelection(); $('movement-only').checked=false; view(shot.view);
  if($('tour-step'))$('tour-step').textContent=`${shot.index+1} / ${shot.count} · ${shot.view==='showcase'?'Studio':shot.view}`;
}
$('tour').onclick = () => {
  if (tour) { stopTour(); return; }
  const shot=tourSequence.start({reducedMotion:reducedMotion.matches});tour=shot.running;
  $('tour').setAttribute('aria-pressed',String(tour));$('tour').textContent=tour?'Pause studio tour':'Studio tour';
  tourView();announce(tour?'Six-view studio tour playing. Drag the watch or choose a view to take control.':'Static studio tour opened. Use Previous or Next view to explore at your pace.');
};
for(const [id,direction]of [['tour-previous',-1],['tour-next',1]])if($(id))$(id).onclick=()=>{stopTour();tourSequence.step(direction);tourView();announce('Tour view changed. Automatic motion is paused.');};
if($('power-path'))$('power-path').onchange=()=>{powerPath=$('power-path').checked;updateMaterials();
  if($('power-path-description'))$('power-path-description').textContent=powerPath?'Barrel → wheel train → escapement → balance. Highlights identify original source parts; bridges and bearings remain in place.':'';
  announce(powerPath?'Original movement power path highlighted. Open Interior or Gear train to follow it.':'Power path highlights hidden.');};
function updateMaterials() {
  syncFrontDetails();
  casebackFinish?.setEnabled($('finish').checked);
  scene.environment = $('finish').checked ? finishes.environment : null;
  for (const material of highlights) material.dispose(); highlights.length = 0;
  for (const mesh of [...meshes(),...openPlates,...craftParts]) {
    let base = $('finish').checked && finishMaterials.has(mesh) ? finishMaterials.get(mesh) : baseMaterials.get(mesh);
    if($('finish').checked&&openFrontActive()&&mesh.userData.sourceIndex===149)base=finishes.apply({name:mesh.name,material:baseMaterials.get(mesh),userData:{...mesh.userData,finishKind:'graphite',finishZone:'circular'}});
    if($('finish').checked&&mesh.userData.sourceIndex===149&&formDetails&&!frontArchitecture?.enabled)base=formDetails.calendarMaterial(base);
    const pathStage=powerPath?POWER_PATH.findIndex(stage=>stage.ids.includes(mesh.userData.sourceIndex)):-1;
    mesh.material = selected.includes(mesh)||pathStage>=0 ? eachMaterial(base,material => {
      const highlighted = cloneAssemblyMaterial(material); highlighted.emissive.setHex(selected.includes(mesh)?0x6c8051:[0x927143,0x336e95,0x975b42,0x85599d][pathStage]); highlighted.emissiveIntensity = selected.includes(mesh)?.22:.42;
      highlights.push(highlighted); return highlighted;
    }) : base;
  }
  dirty = true;
}
resources.own('selection and power-path highlights',()=>{for(const material of highlights)material.dispose();highlights.length=0;});
function visibility() {
  const movementOnly = $('movement-only').checked;
  const open=openFrontActive();
  floor.position.y = movementOnly ? -16.5 : interiorView ? -22.5 : -35.2;
  for (const mesh of meshes()) mesh.visible=partVisible(mesh.userData,{isolated:!!isolated,selected:isolated?.has(mesh),movementOnly,
    interior:interiorView,openWork:open,replacedSources,crystals:$('crystals').checked})&&!(open&&mesh.userData.assemblyId==='CHAPTER'&&/mark|baton/i.test(mesh.name));
  for(const mesh of openPlates) mesh.visible=open;
  syncFrontDetails();
  updateMaterials();
  scene.updateMatrixWorld(true);
  const proposed=open?[...openPlates,...(openFrontFrame?.group.children||[]),...(qualityDesign?.meshes||[]),...craftParts.filter(m=>m.visible)]:[];
  depthBounds=[...meshes().filter(mesh=>mesh.visible),...proposed].map(mesh=>new THREE.Box3().setFromObject(mesh).expandByScalar(.5));
  controls.minDistance=9;
  $('interior-guide').hidden=!interiorView;
  // Hidden mechanisms still advance their clock. Catch up before a component is
  // revealed, including when playback was paused while it was out of view.
  applyClockPose(clock.snapshot());
  $('mode-label').textContent = isolated ? `ISOLATED / ${isolated.size} MESH${isolated.size === 1 ? '' : 'ES'}` :
    movementOnly ? 'OM10 / ORIGINAL MOVEMENT' : interiorView ? 'INTERIOR / CASEBACK REMOVED' : open ? 'OPEN-WORK / FRONT DESIGN STUDY' : 'AERIAL / SOLID DIAL';
  $('show-all').disabled = !isolated && !movementOnly && !interiorView;
  $('isolate').disabled = !selected.length || !!isolated;
  $('visible-count').textContent = `${meshes().filter(mesh => mesh.visible).length} of ${meshes().length} original meshes visible${open?` · ${openPlates.length+(openFrontFrame?.count||0)+(qualityDesign?.count||0)} open-work parts`:''}`;
  dirty = true;
}
function clearSelection() {
  selected = []; $('selection').hidden = true; $('isolate').disabled = true; updateMaterials();
  for (const button of $('component-list').querySelectorAll('button')) button.setAttribute('aria-pressed','false');
}
function select(mesh) {
  stopTour();
  const group = groups.find(entry => entry.parts.includes(mesh)); if (!group) return;
  const wasIsolated = !!isolated;
  if(sourceNeedsBaseline(mesh.userData,replacedSources)||mesh.userData.sourceIndex===149||mesh.userData.assemblyId==='CASE') {
    openWork=false;$('open-work').checked=false;
  }
  clearSelection(); selected = group.parts; isolated = null;
  const restoreWatch=mesh.userData.sourceIndex === undefined;
  if (restoreWatch) { $('movement-only').checked = false; interiorView=false; }
  if (mesh.userData.inspectionTransparent) $('crystals').checked = true;
  $('selection').hidden = false; $('part-name').textContent = group.label;
  $('part-role').textContent = mesh.userData.description || mesh.userData.role || 'Part of the named assembly';
  $('part-support').textContent = mesh.userData.support ? 'Attachment: '+mesh.userData.support : 'Original OM10 component — original placement preserved';
  for (const button of $('component-list').querySelectorAll('button')) button.setAttribute('aria-pressed',String(button.dataset.key === group.key));
  updateMaterials(); visibility();
  if (restoreWatch && (movementViews.includes(currentView)||currentView==='interior')) view('showcase');
  else if (wasIsolated) view(currentView);
  announce(`Selected ${group.label}. ${group.parts.length} mesh${group.parts.length === 1 ? '' : 'es'}. Use Isolate selection to inspect.`);
}
function showAll() {
  stopTour();
  interiorView=false; isolated = null; $('movement-only').checked = false; visibility(); view('face');
  announce(openWork?'Complete watch restored with the open-work front proposal.':'Complete solid-dial baseline restored with all 166 original movement meshes.');
}
$('clear').onclick = () => { clearSelection(); announce('Selection cleared.'); };
$('show-all').onclick = showAll;
$('isolate').onclick = () => {
  stopTour();
  isolated = new Set(selected); visibility(); fitBounds();
  announce(`Isolated ${selected.length} mesh${selected.length === 1 ? '' : 'es'}. Show complete assembly restores every component.`);
};
$('movement-only').onchange = () => {
  stopTour(); interiorView=false; isolated = null; clearSelection(); visibility(); view($('movement-only').checked ? 'showcase' : 'face');
};
$('open-work').onchange=()=>{
  stopTour();openWork=$('open-work').checked;isolated=null;$('movement-only').checked=false;clearSelection();
  visibility();view(interiorView?'interior':'face');
  announce(openWork?'Open-work design shown. Two proposed plates retain bearing seats and connecting ribs; the original baseline is available by switching this off.':'Solid-dial baseline restored.');
};
$('crystals').onchange = () => { visibility(); announce($('crystals').checked ? 'Crystals shown.' : 'Crystals hidden in complete assembly views.'); };
$('finish').onchange = () => {
  updateMaterials(); announce($('finish').checked ? 'Atelier finishes enabled: satin silver, brass, steel, ruby and textured leather.' : 'Clay inspection materials restored.');
};
function buildExplorer() {
  const byKey = new Map();
  for (const mesh of meshes()) {
    const original = mesh.userData.sourceIndex !== undefined;
    const key = original ? 'source-'+mesh.userData.sourceIndex : 'assembly-'+(mesh.userData.assemblyId || mesh.uuid);
    if (!byKey.has(key)) byKey.set(key,{key,parts:[],original,
      label:original ? `${mesh.userData.partNumber || mesh.name} · OM10 #${mesh.userData.sourceIndex}` : `${mesh.userData.assemblyId || 'Assembly'} · ${mesh.name}`});
    byKey.get(key).parts.push(mesh);
  }
  groups = [...byKey.values()].sort((a,b) => Number(a.original)-Number(b.original) || a.label.localeCompare(b.label,undefined,{numeric:true}));
  renderExplorer();
}
function renderExplorer() {
  const query = $('component-search').value.trim().toLocaleLowerCase(), scope = $('component-scope').value;
  const matches = groups.filter(group => (scope === 'all' || group.original === (scope === 'movement')) &&
    [group.label,...group.parts.map(mesh => mesh.userData.description || mesh.userData.role || '')].join(' ').toLocaleLowerCase().includes(query));
  const fragment = document.createDocumentFragment();
  for (const group of matches) {
    const item = document.createElement('li'), button = document.createElement('button');
    button.type = 'button'; button.dataset.key = group.key;
    button.textContent = group.label+(group.parts.length > 1 ? ` (${group.parts.length} meshes)` : '');
    button.setAttribute('aria-pressed',String(group.parts.some(mesh => selected.includes(mesh))));
    button.onclick = () => select(group.parts[0]); item.append(button); fragment.append(item);
  }
  $('component-list').replaceChildren(fragment);
  $('search-count').textContent = `${matches.length} of ${groups.length} components${matches.length ? '' : ' — no matches; clear the search or change the group'}`;
}
$('component-search').oninput = renderExplorer;
$('component-scope').onchange = renderExplorer;
function syncSimpleControls(){
  const running=$('animate-movement').checked||$('animate').checked,pulled=crownInteraction.snapshot().pulled;
  if($('play-motion')){$('play-motion').textContent=running?'Pause motion':'Play motion';$('play-motion').setAttribute('aria-pressed',String(running));$('play-motion').disabled=loading||failed||pulled;}
  if($('slow-motion'))$('slow-motion').checked=Number($('speed').value)===.25;
  if($('primary-motion-status'))$('primary-motion-status').textContent=pulled?'Time setting · turn the crown':running?'Movement running':'Motion paused';
}
const crownInteraction=createCrownInteraction({
  secondsPerDegree:20/3,
  onTurn:(degrees,state)=>{winding?.turn(degrees,{pulled:state.pulled});dirty=true;},
  onPull:pulled=>{winding?.setPulled(pulled);if(pulled){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();}else if(winding){winding.apply();dirty=true;}},
  onSetTime:delta=>{settingSeconds-=delta;const stamp=clock.snapshot(),seconds=((stamp.hands-delta)%43200+43200)%43200;applyClockPose(clock.seek(seconds,{track:'hands'}));dirty=true;},
  onChange:state=>{crownVisual?.apply({...state,degrees:state.degrees+(engagementState?.leadInStemDegrees||0)});if($('crown-state'))$('crown-state').textContent=state.pulled?'Pulled · turn to set time':'Seated · turn crown';
    if($('crown-pull')){$('crown-pull').textContent=state.pulled?'Push in to finish':'Pull out to set time';$('crown-pull').setAttribute('aria-pressed',String(state.pulled));}
    if($('crown-help'))$('crown-help').textContent=state.pulled?'Turn left or right to move the hands. Push in when you are done.':'Turn left to wind the gears; turning right lets the clutch return. Watch time stays unchanged.';
    syncSimpleControls();if(model&&!loading)visibility();dirty=true;},
});resources.own('crown interaction',()=>crownInteraction.dispose());
function focusCrown(){if(loading||failed)return;stopTour();clearSelection();isolated=null;interiorView=false;$('movement-only').checked=false;visibility();if($('crown-controls'))$('crown-controls').open=true;view('crown');$('crown-pull')?.focus({preventScroll:true});announce('Crown controls opened. Turn while seated, or pull out to set the hands.');}
if($('crown-focus'))$('crown-focus').onclick=focusCrown;
if($('crown-pull'))$('crown-pull').onclick=()=>{
  const pulled=!crownInteraction.snapshot().pulled;crownInteraction.setPulled(pulled);
  // Retain the free input's tooth take-up when reseated; this is not a stroke
  // and never seeks the hands or changes the held winding drive.
  if(pulled&&engagementState?.ready&&winding){
    const state=crownInteraction.snapshot(),degrees=state.degrees+engagementState.leadInStemDegrees;
    winding.restore({...winding.snapshot(),crownDegrees:degrees});crownInteraction.restore({...state,degrees});applyClockPose(clock.snapshot());
  }
};
for(const [id,degrees]of [['crown-left',-15],['crown-right',15]])if($(id))$(id).onclick=()=>{stopTour();crownInteraction.turn(degrees);};
if($('crown-reset'))$('crown-reset').onclick=()=>{crownInteraction.reset();if(winding)winding.restore({...winding.snapshot(),crownDegrees:0,pulled:false,reverseFreewheel:false});announce('Crown reseated and aligned. The current hand time is retained.');};
if($('play-motion'))$('play-motion').onclick=()=>{if(crownInteraction.snapshot().pulled)return;stopTour();const play=!($('animate-movement').checked||$('animate').checked);$('animate-movement').checked=play;$('animate').checked=play;setClockPlayback();};
if($('slow-motion'))$('slow-motion').onchange=()=>{$('speed').value=$('slow-motion').checked?'0.25':'1';applyClockPose(clock.setSpeed(Number($('speed').value)));syncSimpleControls();dirty=true;};
function motionStatus() {
  $('motion-status').textContent = `Mechanism ${$('animate-movement').checked ? 'running' : 'paused'} · Hands ${$('animate').checked ? 'running' : 'paused'}`;
  syncSimpleControls();
}
function applyClockPose(stamp) {
  mechanismElapsed=balanceElapsed=stamp.mechanism;elapsed=stamp.hands;
  if(escapement)escapement.apply(mechanismElapsed);else mechanism?.apply(mechanismElapsed,balanceElapsed);
  winding?.apply();
  setting?.apply(settingSeconds,escapement?escapement.sample(mechanismElapsed).trainTime:sampleMechanicalTime(mechanismElapsed));
  if(settingEngagement)engagementState=settingEngagement.apply({pulled:crownInteraction.snapshot().pulled,settingSeconds,commonTrainTime:escapement?escapement.sample(mechanismElapsed).trainTime:sampleMechanicalTime(mechanismElapsed),inputDegrees:crownInteraction.snapshot().degrees});
  crownVisual?.apply({...crownInteraction.snapshot(),degrees:crownInteraction.snapshot().degrees+(engagementState?.leadInStemDegrees||0)});
  if(calendar)calendarState=calendar.apply((escapement?escapement.sample(mechanismElapsed).trainTime:sampleMechanicalTime(mechanismElapsed))+settingSeconds);
  const handTime=escapement?escapement.sample(elapsed).trainTime-handClockOrigin:sampleMechanicalTime(elapsed);
  for(const hand of hands)hand.mesh.quaternion.copy(hand.original).multiply(turn.setFromAxisAngle(axis,-2*Math.PI*handTime/hand.period));
  qualityDesign?.syncMotion();
  if($('scrub-value'))$('scrub-value').textContent=`${(mechanismElapsed%60).toFixed(2)} s`;
  if($('scrub-time')&&document.activeElement!==$('scrub-time'))$('scrub-time').value=String(mechanismElapsed%60);
}
function setClockPlayback(timestamp=performance.now()) {
  if(crownInteraction.snapshot().pulled){$('animate-movement').checked=false;$('animate').checked=false;}
  clock.setRunning('mechanism',$('animate-movement').checked,timestamp);
  const stamp=clock.setRunning('hands',$('animate').checked,timestamp);applyClockPose(stamp);motionStatus();dirty=true;
}
function resetHands() { elapsed = 0; for (const hand of hands) hand.mesh.quaternion.copy(hand.original); qualityDesign?.syncMotion();dirty = true; }
$('animate-movement').onchange = () => {
  setClockPlayback();
  announce($('animate-movement').checked ? 'Interior wheel and balance study playing. Use Inspect animated movement for an unobstructed view.' : 'Interior motion paused at its current pose.');
  dirty = true;
};
$('animate').onchange = () => {
  setClockPlayback();
  announce($('animate').checked ? 'Illustrative hand motion playing.' : 'Hand motion paused at its current pose.'); dirty = true;
};
function resetMotion() {
  $('animate-movement').checked = false; $('animate').checked = false;
  const stamp=clock.reset();settingSeconds=0;winding?.reset();crownInteraction.reset();mechanismElapsed = balanceElapsed = 0;mechanism?.reset();resetHands();applyClockPose(stamp);motionStatus();
  if($('scrub-time'))$('scrub-time').value='0';if($('scrub-value'))$('scrub-value').textContent='0.00 s';
}
$('speed').onchange=()=>{applyClockPose(clock.setSpeed(Number($('speed').value)));syncSimpleControls();dirty=true;};
if($('scrub-time'))$('scrub-time').oninput=()=>{
  stopTour();if(crownInteraction.snapshot().pulled)crownInteraction.setPulled(false);const timestamp=performance.now();$('animate-movement').checked=false;$('animate').checked=false;
  clock.setRunning('mechanism',false,timestamp);clock.setRunning('hands',false,timestamp);
  applyClockPose(clock.seek(Number($('scrub-time').value),{timestamp}));motionStatus();dirty=true;
};
$('reset-hands').onclick = () => { resetMotion(); announce('Aligned movement and hand rest poses restored. Motion is paused.'); };
$('inspect-motion').onclick = () => {
  stopTour(); isolated = null; clearSelection(); view('interior');
  $('animate-movement').checked = !reducedMotion.matches;setClockPlayback();
  announce(`Interior view opened. ${openFrontActive()?'The proposed open-work plates are active; original parts remain in the baseline.':'All 166 original movement parts are visible inside the case.'} Choose a numbered focus point for a closer look.`);
  $('assembly-canvas').focus({preventScroll:true}); $('assembly-canvas').scrollIntoView({block:'start',behavior:'auto'});
};
$('reset').onclick = () => {
  crownInteraction.reset();
  stopTour(); resetMotion(); $('speed').value = '1'; $('finish').checked = true; $('crystals').checked = true;
  clock.setSpeed(1);
  openWork=true;$('open-work').checked=true;
  renderingQuality('detail');
  $('component-search').value = ''; $('component-scope').value = 'all'; clearSelection(); renderExplorer(); showAll();
  announce('Open-work presentation restored and motion paused. Original movement geometry remains preserved in the baseline.');
};
document.addEventListener('keydown', event => { if (event.key === 'Escape' && !loading && !failed) { stopTour(); clearSelection();
  if($('crown-controls')?.contains(document.activeElement)){$('crown-controls').open=false;$('crown-focus')?.focus({preventScroll:true});}
} });
controls.listenToKeyEvents(renderer.domElement);
renderer.domElement.addEventListener('keydown', event => {
  if (loading || failed) return;
  if (['+','=','-','_','Home'].includes(event.key)) {
    event.preventDefault();
    stopTour();
    if (event.key === 'Home') view(interiorView?'interior':$('movement-only').checked?'showcase':'face');
    else { camera.zoom = THREE.MathUtils.clamp(camera.zoom*(['+','='].includes(event.key) ? 1.15 : 1/1.15),controls.minZoom,controls.maxZoom); camera.updateProjectionMatrix(); dirty = true; }
  }
});
let down;
renderer.domElement.addEventListener('pointerdown', event => { down = [event.clientX,event.clientY]; });
renderer.domElement.addEventListener('pointercancel', () => { down = null; });
renderer.domElement.addEventListener('pointerup', event => {
  const start = down; down = null;
  if (loading || failed || !start || Math.hypot(event.clientX-start[0],event.clientY-start[1]) > 5) return;
  const r = renderer.domElement.getBoundingClientRect(), ray = new THREE.Raycaster();
  ray.setFromCamera(new THREE.Vector2((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1),camera);
  const proposed=openFrontActive()?[...openPlates,...(openFrontFrame?.group.children||[]),...(qualityDesign?.meshes||[]),...craftParts]:[];
  const hit = ray.intersectObjects([...meshes(),...proposed].filter(mesh => mesh.visible && !mesh.userData.inspectionTransparent),false)[0];
  if(hit && proposed.includes(hit.object)) {
    clearSelection();announce(`${hit.object.name}. Open-work design proposal; inspect its source counterpart in the component explorer.`);
  } else if(hit?.object.userData.assemblyId==='CROWN')focusCrown();
  else if (hit) select(hit.object); else clearSelection();
});
const originalVisibility = ao._overrideVisibility.bind(ao);
ao._overrideVisibility = () => {
  originalVisibility();
  for (const mesh of exterior) if (mesh.visible && mesh.userData.inspectionTransparent) { mesh.visible = false; ao._visibilityCache.push(mesh); }
  for(const detail of [dialDetails,openDialDetails]) if(detail?.group.visible) detail.group.traverse(mesh=>{
    if(mesh.isMesh&&mesh.visible&&mesh.userData.displayDetail){mesh.visible=false;ao._visibilityCache.push(mesh);}
  });
};
const glassAO=createRefractionAwareAO({pass:ao,scene,camera,getCrystals:()=>exterior.filter(mesh=>['FRONT-CRYSTAL','REAR-CRYSTAL'].includes(mesh.userData.assemblyId))});
resources.own('refraction-aligned ambient occlusion',()=>glassAO.dispose());
function proposalWarning(error){
  if(lifecycle.disposed)return;
  proposalLoading=false;proposalReady=false;loadWarnings.push(error.message);visibility();
  announce('Original assembly ready. The optional open-work design could not load; use Retry design to try again.');
  let retry=$('retry-proposal');if(!retry){retry=document.createElement('button');retry.id='retry-proposal';retry.type='button';retry.textContent='Retry design';$('open-work-note').after(retry);}
  retry.onclick=async()=>{retry.disabled=true;proposalLoading=true;try{const result=await loadGLTFAsset('quality-study/open-front-plates.glb',assetOptions());installProposal(result);retry.remove();}catch(e){proposalWarning(e);}finally{if(!lifecycle.disposed)retry.disabled=false;}};
}
function installProposal(result){
  if(lifecycle.disposed){disposeObjectTree((result.gltf||result).scene);return;}
  const proposal=result.gltf||result;performanceMonitor.load(result.metrics||{});
  const candidates=[];proposal.scene.traverse(mesh=>{if(mesh.isMesh)candidates.push(mesh);});
  if(candidates.length!==2||new Set(candidates.map(mesh=>mesh.userData.replacementForSourceIndex)).size!==2||candidates.some(mesh=>!replacedSources.has(mesh.userData.replacementForSourceIndex)))throw new Error('Expected two distinct open-work plates.');
  const disposeProposal=createObjectTreeDisposer(proposal.scene);
  for(const mesh of candidates){
    const original=source.find(part=>part.userData.sourceIndex===mesh.userData.replacementForSourceIndex);
    openPlates.push(mesh);baseMaterials.set(mesh,mesh.material);
    finishMaterials.set(mesh,finishes.apply({name:original.name,userData:original.userData,material:mesh.material}));mesh.castShadow=true;mesh.receiveShadow=true;
  }
  model.add(proposal.scene);resources.own('optional proposed plates',disposeProposal);
  proposalReady=true;proposalLoading=false;variantManifest=createVariantManifest(source,[...openPlates,...openFrontFrame.group.children,...qualityDesign.meshes,...craftParts]);updateMaterials();visibility();
  announce('Open-work design ready. Explore the original movement and blued hands.');
  loadFrontArchitecture();
}
function loadFrontArchitecture(){
  if(!proposalReady||!formDetails||frontArchitecture||frontArchitectureLoading||lifecycle.disposed)return;
  frontArchitectureLoading=true;
  loadGLTFAsset('quality-study/front-architecture-r07.glb',assetOptions()).then(result=>{
    if(lifecycle.disposed){disposeObjectTree(result.gltf.scene);return;}
    try{
      formDetails.setEnabled(false);
      const targets=new Map(openPlates.map(mesh=>[mesh.userData.replacementForSourceIndex,mesh]));
      targets.set(149,source.find(mesh=>mesh.userData.sourceIndex===149));
      frontArchitecture=createFrontArchitecture({targets,candidateScene:result.gltf.scene,revision:'r07',restMatrices:sourceRestMatrices});
      resources.own('R07 front architecture',()=>frontArchitecture.dispose());
      performanceMonitor.load(result.metrics);updateMaterials();visibility();
    }finally{disposeObjectTree(result.gltf.scene);}
  }).catch(error=>{if(!lifecycle.disposed){loadWarnings.push(`Front architecture: ${error.message}`);updateMaterials();visibility();}}).finally(()=>{frontArchitectureLoading=false;});
}
function initializeBaseline(result,metadata){
  if(lifecycle.disposed){disposeObjectTree((result.gltf||result).scene);return;}
  const gltf=result.gltf||result;performanceMonitor.load(result.metrics||{});
  const disposeBaseline=createObjectTreeDisposer(gltf.scene);
  resources.own('original assembly geometry',disposeBaseline);
  model=new THREE.Group();model.rotation.x=Math.PI/2;model.add(gltf.scene);scene.add(model);
  gltf.scene.traverse(mesh=>{
    if(!mesh.isMesh)return;
    if(mesh.userData.sourceIndex!==undefined)source.push(mesh);else exterior.push(mesh);
    if(mesh.userData.inspectionTransparent)mesh.material=eachMaterial(mesh.material,material=>{const glass=material.clone();resources.own('transparent baseline material',()=>glass.dispose());glass.transparent=true;glass.opacity=.15;glass.depthWrite=false;glass.transmission=0;return glass;});
    baseMaterials.set(mesh,mesh.material);finishMaterials.set(mesh,finishes.apply(mesh));mesh.castShadow=!mesh.userData.inspectionTransparent;mesh.receiveShadow=true;
    if(mesh.userData.sourceIndex===undefined){const period={HOUR:43200,MINUTE:3600,SECONDS:60}[mesh.userData.assemblyId];if(period)hands.push({mesh,period,original:mesh.quaternion.clone()});}
  });
  const casebackMesh=exterior.find(mesh=>mesh.userData.assemblyId==='CASEBACK');
  if(casebackMesh){casebackFinish=createCasebackFinish({mesh:casebackMesh});resources.own('caseback cap finish geometry',()=>casebackFinish.dispose());}
  for(const mesh of source){mesh.updateMatrix();sourceRestMatrices.set(mesh.userData.sourceIndex,mesh.matrix.clone());}
  variantManifest=createVariantManifest(source);mechanism=createAssemblyMotion(source,metadata);
  try{calendar=createAssemblyCalendar(source);}catch(error){loadWarnings.push(`Calendar reconstruction unavailable: ${error.message}`);}
  const springMesh=mechanism.entries.find(entry=>entry.kind==='spring').mesh,originalSpringGeometry=springMesh.geometry;
  try{escapement=createAssemblyEscapement(mechanism);handClockOrigin=escapement.sample(0).trainTime;escapement.apply(0);}
  catch(error){loadWarnings.push(`Escapement reconstruction unavailable: ${error.message}`);mechanism.apply(0,0);}
  const displaySpringGeometry=springMesh.geometry;
  try{winding=createAssemblyWinding(source,mechanism);}catch(error){loadWarnings.push(`Winding reconstruction unavailable: ${error.message}`);}
  try{setting=createAssemblySetting(mechanism);}catch(error){loadWarnings.push(`Setting reconstruction unavailable: ${error.message}`);}
  try{if(winding&&setting)settingEngagement=createAssemblySettingEngagement(source,mechanism,winding);}catch(error){loadWarnings.push(`Setting engagement unavailable: ${error.message}`);}
  const crownMesh=exterior.find(mesh=>mesh.userData.assemblyId==='CROWN');
  if(crownMesh){crownVisual=createCrownVisual(crownMesh,{compact:true,stem:source.find(mesh=>mesh.userData.sourceIndex===52),tube:exterior.find(mesh=>mesh.userData.assemblyId==='CROWN-TUBE')});resources.own('crown presentation transform',()=>crownVisual.dispose());}
  dialFace=exterior.find(mesh=>mesh.userData.assemblyId==='DIAL'&&!/mark/i.test(mesh.name));
  dialDetails=createDialDetails({renderer});gltf.scene.add(dialDetails.group);
  openDialDetails=createDialDetails({renderer,openWork:true});gltf.scene.add(openDialDetails.group);
  openFrontFrame=createOpenFrontFrame();gltf.scene.add(openFrontFrame.group);
  qualityDesign=createQualityDesign(source,exterior);gltf.scene.add(qualityDesign.group);
  resources.own('escapement and private spring display',()=>{if(escapement)escapement.dispose();else mechanism.reset();if(displaySpringGeometry!==originalSpringGeometry)displaySpringGeometry.dispose();});
  resources.own('winding train and private clutch spring',()=>winding?.dispose());
  resources.own('manual setting train',()=>setting?.dispose());
  resources.own('setting engagement and private clearance geometry',()=>settingEngagement?.dispose());
  resources.own('indexed calendar and private spring display',()=>calendar?.dispose());
  resources.own('dial printing',()=>{dialDetails.dispose();openDialDetails.dispose();});resources.own('open-work frame',()=>openFrontFrame.dispose());resources.own('quality hand design',()=>qualityDesign.dispose());
  loading=false;$('load-message').textContent='Lighting the watch studio…';$('assembly-canvas').setAttribute('aria-busy','false');
  $('inspection-controls').disabled=false;$('view-controls').disabled=false;$('animate').disabled=hands.length!==3;
  $('animate-movement').checked=!reducedMotion.matches;$('animate').checked=!reducedMotion.matches&&hands.length===3;
  $('finish').checked=true;$('crystals').checked=true;$('open-work').checked=true;updateMaterials();buildExplorer();visibility();
  view(new URLSearchParams(location.search).get('view')==='mechanism'?'interior':'face',false);setClockPlayback();
  announce('Original assembly ready. Preparing the optional open-work design.');
  loadGLTFAsset('quality-study/form-legibility-r01.glb',assetOptions()).then(result=>{
    if(lifecycle.disposed){disposeObjectTree(result.gltf.scene);return;}
    try{
      formDetails=createFormDetails({calendar:source.find(mesh=>mesh.userData.sourceIndex===149),caseMesh:exterior.find(mesh=>mesh.userData.assemblyId==='CASE'),candidateScene:result.gltf.scene});
      resources.own('calendar lettering and lug bevels',()=>formDetails.dispose());
      performanceMonitor.load(result.metrics);updateMaterials();visibility();
      loadFrontArchitecture();
    }finally{disposeObjectTree(result.gltf.scene);}
  }).catch(error=>{if(lifecycle.disposed)return;loadWarnings.push(`Form detail: ${error.message}`);announce('The watch is ready. Additional calendar and edge details are unavailable.');});
  loadGLTFAsset('quality-study/leather-craft-r05.glb',assetOptions()).then(result=>{
    if(lifecycle.disposed){disposeObjectTree(result.gltf.scene);return;}
    try{
    performanceMonitor.load(result.metrics);const clay=new THREE.MeshStandardMaterial({color:0x93989b,roughness:.7});resources.own('craft comparison material',()=>clay.dispose());
    leatherDetails=createLeatherDetails({candidateScene:result.gltf.scene});
    for(const mesh of leatherDetails.meshes){craftParts.push(mesh);baseMaterials.set(mesh,clay);finishMaterials.set(mesh,leatherDetails.materialFor(mesh));}
    model.add(leatherDetails.group);resources.own('R05 leather craft geometry',()=>leatherDetails.dispose());updateMaterials();visibility();
    variantManifest=createVariantManifest(source,[...openPlates,...openFrontFrame.group.children,...qualityDesign.meshes,...craftParts]);
    }finally{disposeObjectTree(result.gltf.scene);}
  }).catch(error=>{if(lifecycle.disposed)return;loadWarnings.push(`Leather detail: ${error.message}`);announce('The watch is ready. Additional leather detail is unavailable.');});
}
loadProgressiveAssembly({
  signal:lifecycle.signal,disposeUnused:result=>disposeObjectTree((result.gltf||result).scene),
  loadBaseline:()=>loadGLTFAsset('rebuild/assembly.glb',{...assetOptions(),onProgress:p=>{if(!lifecycle.disposed&&!failed)$('load-message').textContent=`Preparing the watch · ${(p.loaded/1048576).toFixed(1)} MB`;}}),
  loadMetadata:()=>fetch('assets/manual-a-parts.json',{signal:lifecycle.signal}).then(r=>{if(!r.ok)throw new Error('Movement metadata could not load.');return r.json();}),
  loadProposal:()=>{proposalLoading=true;return loadGLTFAsset('quality-study/open-front-plates.glb',assetOptions());},
  onBaseline:initializeBaseline,onProposal:installProposal,onWarning:proposalWarning,onPhase:phase=>{loadPhase=phase;},
}).catch(error=>{if(!lifecycle.disposed)fail('The assembly could not load. Reload the viewer to retry. Static renders remain available below.',error);});

function captureConfiguration({clockStamp}={}){
  const gl=renderer.getContext(),extension=gl.getExtension('WEBGL_debug_renderer_info');
  const measuredPerformance=performanceMonitor.snapshot(),preview=$('studio-poster')?.querySelector('img');
  const previewEntry=preview?performance.getEntriesByName(preview.currentSrc).at(-1):null;
  return {version:1,date:new Date().toISOString(),design:'Aerial Quality 01',phase:loadPhase,view:currentView,
    camera:{position:camera.position.toArray(),target:controls.target.toArray(),zoom:camera.zoom,fov:camera.fov,near:camera.near,far:camera.far},
    formDetails:{revision:'form-legibility-r01',ready:!!formDetails,enabled:!!formDetails?.enabled,calendarDigitIslands:formDetails?.audit.components??null},
    frontArchitecture:{revision:'front-architecture-r07',ready:!!frontArchitecture,enabled:!!frontArchitecture?.enabled,audit:frontArchitecture?.audit??null},
    escapement:{revision:'r09-contact-reconstruction',ready:!!escapement,limits:escapement?.limits??null},
    calendar:{revision:'r09-indexed-calendar',ready:!!calendar,state:calendarState},
    winding:{revision:'r09-crown-coupling',ready:!!winding,state:winding?.snapshot()??null},
    setting:{revision:'r09-friction-setting',ready:!!setting},
    casebackFinish:{revision:'r10-cap-corner-normals',enabled:!!casebackFinish?.enabled,audit:casebackFinish?.audit??null},
    settingEngagement:{revision:'r09-keyless-endpoints',ready:!!settingEngagement,state:engagementState,limits:settingEngagement?.limits??null},
    leatherCraft:{revision:'leather-craft-r05',ready:!!leatherDetails,parts:craftParts.length},
    compactCrown:!!crownVisual&&openFrontActive(),
    settingSeconds,clock:clockStamp||clock.snapshot(),crown:crownInteraction.snapshot(),sourceAtCapture:captureProvenance.snapshot(),options:{openWork:$('open-work').checked,finishes:$('finish').checked,crystals:$('crystals').checked,movementOnly:$('movement-only').checked,interior:interiorView,powerPath,quality},
    viewport:{width:renderer.domElement.clientWidth,height:renderer.domElement.clientHeight,pixelRatio:renderer.getPixelRatio(),drawingBufferWidth:renderer.domElement.width,drawingBufferHeight:renderer.domElement.height,msaaSamples:composer.renderTarget1.samples,transmissionScale:renderer.transmissionResolutionScale},
    sourceMeshes:source.length,sourceVisible:source.filter(m=>m.visible).length,derivedParts:openPlates.length+(openFrontFrame?.count||0)+(qualityDesign?.count||0)+craftParts.length,lightRig:lighting.shot,
    performance:measuredPerformance,resources:resources.snapshot(),warnings:[...loadWarnings],
    navigationTiming:{moduleBootMs:bootTime,firstInteractiveMs:measuredPerformance.firstInteractiveMs===null?null:bootTime+measuredPerformance.firstInteractiveMs,
      preview:preview?{path:new URL(preview.currentSrc).pathname,decoded:preview.complete&&preview.naturalWidth>0,responseEndMs:previewEntry?.responseEnd??null}:null,
      note:'Times are relative to document navigation. Preview response completion/decoded state does not measure its first painted frame.'},
    pageTransfers:performance.getEntriesByType('resource').map(entry=>({path:new URL(entry.name).pathname,startMs:entry.startTime,endMs:entry.responseEnd,transferBytes:entry.transferSize,encodedBodyBytes:entry.encodedBodySize})),
    GPU:extension?gl.getParameter(extension.UNMASKED_RENDERER_WEBGL):'unavailable',manifest:variantManifest,
    transport:performance.getEntriesByType('resource').filter(e=>/\.glb/.test(e.name)).map(e=>({name:new URL(e.name).pathname,transferSize:e.transferSize,encodedBodySize:e.encodedBodySize,decodedBodySize:e.decodedBodySize,duration:e.duration})),
  };
}
function downloadBlob(blob,name){const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const recorder=createCanvasRecorder({canvas:renderer.domElement,onStatus:announce});
resources.own('canvas motion recorder',()=>recorder.dispose());
if($('record-scene'))$('record-scene').onclick=async()=>{
  $('record-scene').disabled=true;
  try{const result=await recorder.start();downloadBlob(result.blob,'aerial-motion.webm');}
  catch(error){if(error.name!=='AbortError')announce(`Could not record: ${error.message}`);}
  finally{if(!lifecycle.disposed)$('record-scene').disabled=false;}
};
if($('refresh-diagnostics'))$('refresh-diagnostics').onclick=()=>{$('diagnostics-report').textContent=JSON.stringify(captureConfiguration(),null,2);};
if($('start-measurement'))$('start-measurement').onclick=()=>{performanceMonitor.reset();$('diagnostics-report').textContent='New measurement started. Refresh after the desired playback interval.';};
if($('export-config'))$('export-config').onclick=async()=>{
  if(pendingCaptures.has('export-config'))return;pendingCaptures.add('export-config');
  try{await captureProvenance.resolve();if(lifecycle.disposed)return;downloadBlob(new Blob([JSON.stringify(captureConfiguration(),null,2)],{type:'application/json'}),'aerial-view.json');}
  catch(error){announce(`Could not save view: ${error.message}`);}finally{pendingCaptures.delete('export-config');}
};
if($('capture-scene'))$('capture-scene').onclick=async()=>{
  if(pendingCaptures.has('capture-scene'))return;pendingCaptures.add('capture-scene');
  try{await captureProvenance.resolve();if(lifecycle.disposed)return;
    const stamp=clock.tick(performance.now());applyClockPose(stamp);updateInspectionDepth(camera,controls.target,depthBounds,ao);renderer.info.reset();composer.render();
    const configuration=captureConfiguration({clockStamp:stamp}),blob=await new Promise(resolve=>renderer.domElement.toBlob(resolve,'image/png'));
    if(!blob)throw new Error('The canvas could not create an image.');if(lifecycle.disposed)return;
    downloadBlob(await embedPNGConfiguration(blob,configuration),'aerial-studio.png');
  }catch(error){announce(`Could not save image: ${error.message}`);}finally{pendingCaptures.delete('capture-scene');}
};
let configurationRequest=0;
if($('import-config'))$('import-config').onchange=async event=>{
  const input=event.target,file=input.files?.[0];if(!file)return;
  const request=++configurationRequest;
  try{if(loading||failed)throw new Error('Wait for the watch to finish loading.');if(file.size>1048576)throw new Error('View file is too large.');
    const config=validateViewConfiguration(JSON.parse(await file.text()),{qualities:Object.keys(qualityProfiles)});if(lifecycle.disposed||request!==configurationRequest)return;
    stopTour();isolated=null;clearSelection();view(config.view,false);
    openWork=config.options.openWork;$('open-work').checked=openWork;$('finish').checked=config.options.finishes;$('crystals').checked=config.options.crystals;$('movement-only').checked=config.options.movementOnly;
    if(typeof config.options.interior==='boolean')interiorView=config.options.interior;
    powerPath=!!config.options.powerPath;if($('power-path'))$('power-path').checked=powerPath;
    if($('power-path-description'))$('power-path-description').textContent=powerPath?'Barrel → wheel train → escapement → balance. Original source parts highlighted.':'';
    updateMaterials();visibility();renderingQuality(config.options.quality);
    const damping=controls.enableDamping;controls.enableDamping=false;controls.update();
    camera.position.fromArray(config.camera.position);controls.target.fromArray(config.camera.target);camera.zoom=config.camera.zoom;camera.fov=config.camera.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();controls.enableDamping=damping;
    resetMotion();clock.setSpeed(config.clock.speed);
    if(![...$('speed').options].some(option=>Number(option.value)===config.clock.speed)){$('speed').querySelector('[data-saved-speed]')?.remove();const option=new Option(`${config.clock.speed}× · saved time scale`,String(config.clock.speed));option.dataset.savedSpeed='true';$('speed').add(option);}
    $('speed').value=String(config.clock.speed);
    settingSeconds=config.settingSeconds;winding?.restore(config.winding);crownInteraction.restore(config.crown);
    clock.seek(config.clock.mechanism,{track:'mechanism'});applyClockPose(clock.seek(config.clock.hands,{track:'hands'}));if(config.view==='crown'&&$('crown-controls'))$('crown-controls').open=true;motionStatus();dirty=true;announce('Saved camera, crown, options, time scale and pose restored. Motion is paused.');
  }catch(e){if(!lifecycle.disposed&&request===configurationRequest)announce(`Could not restore view: ${e.message}`);}finally{if(request===configurationRequest)input.value='';}
};
let last = 0;
function frame(time) {
  if(lifecycle.disposed)return;
  animationFrame=requestAnimationFrame(frame);
  if (document.hidden || failed || contextLost) { last = time; return; }
  if(time-last<15)return;const cpuStart=performance.now(),stamp=clock.tick(time);
  const delta=Math.min(stamp.delta,.1);last=time;
  const lightingChanged=lighting.update(delta);if(lightingChanged)dirty=true;
  if (cameraTween) {
    cameraTween.elapsed += delta;
    const progress = Math.min(1,cameraTween.elapsed/cameraTween.duration), eased = progress*progress*(3-2*progress);
    controls.target.lerpVectors(cameraTween.fromTarget,cameraTween.toTarget,eased);
    const rotation = new THREE.Quaternion().slerp(cameraTween.rotation,eased);
    const direction = cameraTween.fromDirection.clone().applyQuaternion(rotation);
    camera.position.copy(controls.target).addScaledVector(direction,THREE.MathUtils.lerp(cameraTween.fromDistance,cameraTween.toDistance,eased));
    camera.lookAt(controls.target); dirty = true;
    if (progress === 1) cameraTween = null;
  }
  controls.update();
  for(const id of ['capture-scene','export-config'])if($(id))$(id).disabled=loading||failed||!!cameraTween||pendingCaptures.has(id);
  const ready=String(!loading&&!failed&&!cameraTween&&!lightingChanged);if($('stage').dataset.cameraReady!==ready)$('stage').dataset.cameraReady=ready;
  if(dirty) updatePins();
  if (tour) {
    if(tourSequence.tick(delta))tourView();
  }
  let visibleMotion=false;
  if(!loading){
    const moving=$('animate-movement').checked&&mechanism.entries.some(entry=>entry.mesh.visible&&(entry.kind!=='wheel'||entry.rate!==0));
    const movingHands=$('animate').checked&&(hands.some(hand=>hand.mesh.visible)||openFrontActive());
    if(moving||movingHands){applyClockPose(stamp);dirty=visibleMotion=true;}
  }
  // Canvas capture needs drawn frames even when the watch and camera are paused.
  // Keep its timeline advancing without changing either presentation clock.
  if (dirty || recorder.recording) {
    try {
      const depth=updateInspectionDepth(camera,controls.target,depthBounds,ao);
      controls.minDistance=depth.minimumDistance;
      renderer.info.reset();composer.render();renderedFrames++;dirty=false;
      performanceMonitor.frame({timestamp:time,cpuMs:performance.now()-cpuStart,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,geometries:renderer.info.memory.geometries,textures:renderer.info.memory.textures});
      if(firstRender&&!loading){firstRender=false;$('loading').hidden=true;if($('studio-poster'))$('studio-poster').hidden=true;performanceMonitor.interactive(performance.now()-bootTime);}
    }
    catch (error) { fail('The graphics renderer could not display this assembly. Retry the viewer or inspect the static renders below.',error); }
  }
  if(!loading && time-frameWindow>=1500) {
    const running=visibleMotion || tour || cameraTween || recorder.recording;
    const rate=Math.round(renderedFrames*1000/(time-frameWindow));
    $('render-status').textContent=`${qualityProfiles[quality].label} · ${running ? `${rate} fps` : 'still view, renders on change'}`;
    renderedFrames=0; frameWindow=time;
  }
}
animationFrame=requestAnimationFrame(frame);
document.addEventListener('visibilitychange',()=>{const now=performance.now();clock.setHidden(document.hidden,now);last=frameWindow=now;renderedFrames=0;performanceMonitor.breakCadence();dirty=true;});
window.addEventListener('pagehide',event=>lifecycle.hide(event));
window.addEventListener('pageshow',()=>lifecycle.show());
resize();
window.assemblyInspect = () => ({loading,failed,sourceMeshes:source.length,sourceVisible:source.filter(mesh=>mesh.visible).length,
  interiorView,dialPrinting:!!dialDetails?.group.visible,renderQuality:quality,
  openWork:openFrontActive(),replacementPlates:openPlates.length,
  exteriorMeshes:exterior.length,exteriorVisible:exterior.filter(mesh=>mesh.visible).length,
  hiddenStructuralSource:source.filter(mesh=>!mesh.visible).map(mesh=>mesh.name),movementOnly:$('movement-only').checked,
  crystals:$('crystals').checked,finish:$('finish').checked,animation:$('animate').checked,animationHandCount:hands.length,
  interiorAnimation:$('animate-movement').checked,interiorAnimatedMeshes:mechanism?.count || 0,mechanismElapsed,balanceElapsed,
  studioTour:tour,mechanicalTiming:mechanism?.timing,
  illustrativeElapsed:elapsed,isolated:!!isolated,componentGroups:groups.length,selected:selected.map(mesh=>mesh.name),view:currentView,
  camera:camera.position.toArray(),target:controls.target.toArray(),triangles:meshes().filter(mesh=>mesh.visible).reduce((sum,mesh)=>sum+(mesh.geometry.index?.count||mesh.geometry.attributes.position.count)/3,0)});

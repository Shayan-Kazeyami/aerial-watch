import {assetURL as progressiveAssetURL} from './assembly-asset-routing.js';
import {observeViewerVisibility,skipViewerFrame} from './assembly-screen-visibility.js';
import {createStartupDiagnostics} from './assembly-startup-diagnostics.js';
const startupDiagnostics=createStartupDiagnostics({enabled:new URLSearchParams(location.search).get('profileLoad')==='1'});
startupDiagnostics.mark('module-body-start');
import {createCarrierFinish,carrierFinishRequested} from './assembly-carrier-microfinish.js';
import {createLowerCarrierGoldZone,lowerCarrierGoldRequested} from './assembly-lower-carrier-gold.js';
import {resourceSnapshot,estimateRenderTarget} from './assembly-resource-accounting.js';
import {createInspectionMaterials,inspectionBloomEnabled,applyStrapInspectionVisibility,isStrapInspectionPart,strapInspectionAvailable,strapInspectionSnapshot} from './assembly-inspection.js';
import {leatherCandidateDiagnostics} from './assembly-leather-identity.js';
import {createAssemblyRenderer,disposeAssemblyRenderer} from './assembly-renderer.js';
import {createGPUScenePipeline,installOverscan} from './assembly-render-pipeline.js';
import {COMPAT_LEATHER_URL,COMPAT_LEATHER_IDENTITY,COMPAT_LEATHER_WARNING,loadCompatLeather} from './assembly-leather-compat.js';
import {createBackplate} from './assembly-backplate.js';
import {createDarkBackplateFinish,DARK_BACKPLATE_FINISH} from './assembly-backplate-finish.js';
import {structuralSupportAsset,structuralSupportVisible,structuralSupportSnapshot} from './assembly-structural-support.js';
import {SMAAPass} from './vendor/postprocessing/SMAAPass.js';
import {prepareSMAAPass} from './assembly-smaa-readiness.js';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {createNativeAO} from './assembly-native-ao.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {createAssemblyMotion, sampleMechanicalTime} from './assembly-motion.js';
import {createAssemblyMaterials,cloneAssemblyMaterial} from './assembly-materials.js';
import {createAssemblyLighting} from './assembly-lighting.js';
import {installReceiverPlaneFinish,receiverPlaneFinishEnabled} from './assembly-receiver-plane-finish.js';
import {installAONormalShadowReuse} from './assembly-ao-shadow-reuse.js';
import {createDialDetails} from './assembly-dial.js';
import {createLazyDetail} from './assembly-lazy-detail.js';
import {createDeferredComparisonDetails} from './assembly-comparison-loading.js';
import {createOpenFrontFrame} from './assembly-open-front.js';
import {repairFrontCapNormals} from './assembly-front-cap-normal.js';
import {premiumFaceAsset,preparePremiumFace,premiumFaceVisible,PREMIUM_HIDDEN_SOURCES,premiumMovementFinishKind} from './assembly-premium-face.js?v=svg04';
import {createQualityDesign} from './assembly-design.js';
import {updateInspectionDepth} from './assembly-depth.js?v=b03';
import {createRefractionAwareAO} from './assembly-glass-ao.js';
import {createPresentationClock,sampleSettingHandTime} from './assembly-clock.js';
import {partVisible,createVariantManifest,createResourceScope,createObjectTreeDisposer} from './assembly-state.js';
import {loadJSONAsset,loadProgressiveAssembly} from './assembly-loading.js';
import {loadOptimizedGLTFAsset} from './assembly-optimized-loading.js';
const loadGLTFAsset=(url,options)=>loadOptimizedGLTFAsset(url,options,{optIn:new URLSearchParams(location.search).get('assets')==='meshopt'});
import {createPresentationGate} from './assembly-presentation-gate.js';
import {createPerformanceMonitor} from './assembly-performance.js';
import {createGPUTiming} from './assembly-gpu-timing.js';
import {RENDER_PROFILES,resolveRenderResolution} from './assembly-resolution.js';
import {createCrownInteraction,createCrownVisual} from './assembly-crown.js';
import {createCaptureProvenance,embedPNGConfiguration} from './assembly-capture-provenance.js';
import {componentLabel,componentSearchText,normalizeComponentText} from './assembly-component-labels.js?v=b04';
import {createDownloadManager} from './assembly-download.js';
import {captureCanvasPNG} from './assembly-image-export.js?v=b03';
import {createCanvasRecorder} from './assembly-recording.js';
import {POWER_PATH,createTourSequence,restoresExterior,sourceNeedsBaseline,validateViewConfiguration,resolveInitialView} from './assembly-story.js';
import {createViewerLifecycle} from './assembly-lifecycle.js';
import {createFormDetails} from './assembly-form-details.js';
import {createLeatherDetails} from './assembly-leather-details.js';
import {createPhotoLeatherDetails,photoLeatherAsset,leatherAnisotropy,leatherCaptureRevision} from './assembly-photo-leather.js';
import {loadKtxLeather,KTX_LEATHER_URL} from './assembly-ktx-leather.js';
import {loadR14KtxLeather,R14_LEATHER_URL,R14_NORMAL_IDENTITY} from './assembly-ktx-leather-r14.js';
import {createProgressiveUpgrade} from './assembly-progressive-upgrade-controller.js';
import {fetchProgressiveNormal} from './assembly-fetch-progressive-normal.js';
import {decodeFullKtx} from './assembly-decode-full-ktx.js';
import {createAssemblyExplosion} from './assembly-explode.js';
import {visibleFramingPoints,watchHeadFramingPoints,perspectiveFrame,isPanelOnlyResize} from './assembly-framing.js';
import {createHandClearance,PREMIUM_HAND_CLEARANCE} from './assembly-hand-clearance.js';
import {createCrownCapEligibility} from './assembly-crown-cap-eligibility.js';
import {createFrontArchitecture} from './assembly-front-architecture.js';
import {createAssemblyEscapement} from './assembly-escapement.js';
import {createAssemblyCalendar} from './assembly-calendar.js';
import {createAssemblyWinding} from './assembly-winding.js';
import {createAssemblySetting} from './assembly-setting.js';
import {createAssemblySettingEngagement} from './assembly-setting-engagement.js';
import {createCasebackFinish} from './assembly-caseback-finish.js';
import {closeDisclosureWithFocus,isEditingControl,restoreExplorerFocus} from './assembly-control-focus.js';

const $ = id => document.getElementById(id), scene = new THREE.Scene();
const bootTime=performance.now(),clock=createPresentationClock(),resources=createResourceScope(),performanceMonitor=createPerformanceMonitor();
// Share one disposal boundary across load rejection and registered ownership.
const objectDisposers=new WeakMap();
function ownedObjectTreeDisposer(root){
  if(!objectDisposers.has(root))objectDisposers.set(root,createObjectTreeDisposer(root));
  return objectDisposers.get(root);
}
function disposeObjectTree(root){ownedObjectTreeDisposer(root)();}
const atelierVisuals=document.body.classList.contains('atelier-live')||new URLSearchParams(location.search).get('visual')==='atelier';
const smaaRequested=document.body.classList.contains('atelier-live')&&document.body.dataset.premiumFace==='b'&&new URLSearchParams(location.search).get('antialias')==='smaa';
const softShadowStudy=atelierVisuals&&new URLSearchParams(location.search).get('shadow')==='soft',noAoStudy=atelierVisuals&&new URLSearchParams(location.search).get('ao')==='off';
scene.background = new THREE.Color('#171a19');
scene.fog = new THREE.Fog('#171a19',350,900);
if(atelierVisuals){
 const backdrop=document.createElement('canvas');backdrop.width=backdrop.height=512;const context=backdrop.getContext('2d');
 const gradient=context.createRadialGradient(270,215,20,256,256,330);gradient.addColorStop(0,'#3d413e');gradient.addColorStop(.65,'#2b302c');gradient.addColorStop(1,'#272c28');context.fillStyle=gradient;context.fillRect(0,0,512,512);
 const texture=new THREE.CanvasTexture(backdrop);texture.colorSpace=THREE.SRGBColorSpace;scene.background=texture;scene.fog=null;resources.own('atelier studio backdrop',()=>texture.dispose());
}
startupDiagnostics.mark('renderer-init-start');
const {renderer,identity:backendIdentity,GPU}=await createAssemblyRenderer({canvas:$('assembly-canvas'),antialias:!smaaRequested,requested:new URLSearchParams(location.search).get('backend')||'webgl2',unsupportedReason:new URLSearchParams(location.search).get('finish')==='studio4'?'Studio4 analytic microfinish is not yet ported to the node renderer':null});
startupDiagnostics.mark('renderer-init-end');
if(renderer.isWebGLRenderer)startupDiagnostics.observeWebGL(renderer.getContext());
resources.own('startup diagnostics',()=>startupDiagnostics.stop());
window.__aerialBackend=backendIdentity;
document.documentElement.dataset.renderBackend=backendIdentity.actual;
backendIdentity.transmissionSamples=GPU?'renderer-managed':4;
const passProfiling=!GPU&&new URLSearchParams(location.search).get('profilePass')==='1';
const gpuTiming=createGPUTiming(renderer.getContext?.(),{enabled:!passProfiling&&new URLSearchParams(location.search).get('profile')==='1'});
let passTiming=null;
if(atelierVisuals)renderer.setClearColor(0x191b1a,1);
// Count the entire composed frame, including transmission, shadows and AO.
renderer.info.autoReset=false;
renderer.setPixelRatio(2);
renderer.transmissionResolutionScale=2;
renderer.toneMapping = atelierVisuals&&new URLSearchParams(location.search).get('tone')==='agx'?THREE.AgXToneMapping:THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = (Number(THREE.REVISION)>=187||softShadowStudy)?THREE.PCFShadowMap:THREE.PCFSoftShadowMap;
startupDiagnostics.mark('materials-environment-start');
const finishes = createAssemblyMaterials(renderer,{atelier:atelierVisuals,light:new URLSearchParams(location.search).get('light'),finish:new URLSearchParams(location.search).get('finish')==='brushed'?'atelier3':new URLSearchParams(location.search).get('finish'),clearTransmission:new URLSearchParams(location.search).get('crystal')==='clear'});
startupDiagnostics.mark('materials-environment-end');
scene.environment = finishes.environment; scene.environmentIntensity = .85;
const camera = new THREE.PerspectiveCamera(32,1,.1,800);
if(GPU){camera.coordinateSystem=renderer.coordinateSystem;camera.updateProjectionMatrix();}
const lighting=createAssemblyLighting(scene,{renderer,atelier:atelierVisuals,lightStudy:new URLSearchParams(location.search).get('light'),shadowStudy:atelierVisuals?new URLSearchParams(location.search).get('shadow'):undefined}),{key,floor}=lighting;
if(softShadowStudy)key.shadow.radius=5;
const receiverPlaneFinish=await installReceiverPlaneFinish({renderer,key,enabled:receiverPlaneFinishEnabled({node:!!GPU,atelier:atelierVisuals,requested:new URLSearchParams(location.search).get('shadow')})});
resources.own('receiver-plane shadow finish',()=>receiverPlaneFinish.dispose());
const aoQuery=new URLSearchParams(location.search).get('ao');
const requestedAO=['baseline','ssao'].includes(aoQuery)?'baseline':'gtao';
let composer,ao,bloom,smaa,aoShadowReuse,nativeAO;
if(GPU){({composer,ao,bloom,smaa,aoShadowReuse}=await createGPUScenePipeline({renderer,scene,camera,GPU,identity:backendIdentity,smaaRequested}));}
else{
composer = new EffectComposer(renderer);
composer.renderTarget1.samples = composer.renderTarget2.samples = Math.min(4,renderer.capabilities.maxSamples);
composer.addPass(new RenderPass(scene,camera));
nativeAO=createNativeAO({scene,camera,mode:requestedAO});ao=nativeAO.ao;
aoShadowReuse=new URLSearchParams(location.search).get('perf')==='baseline'?null:installAONormalShadowReuse(ao,{reuseSceneMatrices:true});resources.own('reuse beauty shadows during AO normals',()=>aoShadowReuse?.dispose());
ao.kernelRadius = 1.2; ao.minDistance = .000025; ao.maxDistance = .006;
composer.addPass(ao);bloom=new UnrealBloomPass(new THREE.Vector2(1,1),.07,.25,1.8);bloom.enabled=false;composer.addPass(bloom);smaa=smaaRequested?new SMAAPass():null;if(smaa)composer.addPass(smaa);composer.addPass(new OutputPass());
}
const overscanMargin=new URLSearchParams(location.search).get('overscan')==='off'?0:Number(new URLSearchParams(location.search).get('overscan')||.12);
installOverscan({renderer,composer,scene,camera,identity:backendIdentity,...(composer.aerialGPU||{}),margin:overscanMargin});
if(passProfiling){try{const {createPassTiming}=await import('./assembly-gpu-pass-timing.js');passTiming=createPassTiming(renderer.getContext(),composer.passes,{enabled:true});resources.own('optional GPU pass timing',()=>passTiming.dispose());}catch(error){backendIdentity.limitations.push('GPU pass timing unavailable');console.warn('GPU pass timing unavailable.',error);}}
const controls = new OrbitControls(camera,renderer.domElement);
renderer.domElement.style.touchAction=atelierVisuals?'none':'pan-y';
resources.own('graphics renderer',()=>disposeAssemblyRenderer(renderer,backendIdentity));
resources.own('optional local GPU timing',()=>gpuTiming.dispose());
resources.own('studio environment and finish library',()=>finishes.dispose());
resources.own('post-processing composer',()=>{ao.dispose();composer.passes.forEach(pass=>pass!==ao&&pass.dispose?.());composer.dispose();});
resources.own('orbit controls',()=>controls.dispose());
resources.own('studio lighting and floor',()=>lighting.dispose());
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
controls.enableDamping = !reducedMotion.matches; controls.dampingFactor = .09; controls.minZoom = .4; controls.maxZoom = 12;
controls.minDistance = 9; controls.maxDistance = 480;
reducedMotion.addEventListener('change', event => {
  controls.enableDamping = !event.matches;
  crownVisual?.setPullDuration(event.matches?0:.36);
  crownInteraction.setDuration(event.matches?0:.24);
  if (event.matches) { $('animate-movement').checked = false; $('animate').checked = false; stopTour(); cameraTween = null; crownVisual?.finish(); setClockPlayback(); }
  dirty = true;
});
controls.addEventListener('change', () => { dirty = true; });

let loading = true, failed = false, contextLost = false, dirty = true, firstRender = true;
let loadPhase='poster',proposalReady=false,proposalLoading=false,loadWarnings=[],variantManifest=null,qualityDesign;
let source = [], exterior = [], selected = [], groups = [], isolated = null, model, explosion;
let depthBounds=[];
let interiorView=false,dialDetails,dialDetailLazy,openDialDetailLazy,dialFace;
let openWork=true,openDialDetails,openFrontFrame,openPlates=[],craftParts=[],formDetails,leatherDetails,leatherGeometryProof=null,frontArchitecture,casebackFinish;
let progressiveNormal=null,progressiveNormalState='disabled';
const leatherCompatRequested=new URLSearchParams(location.search).get('leather')==='compat12';
let leatherCompatReady=false;
const leatherCompatibility=()=>({enabled:leatherCompatRequested,loaded:leatherCompatReady,...(leatherCompatRequested?COMPAT_LEATHER_IDENTITY:{})});
const premiumRequested=document.body.dataset.premiumFace==='b';
const presentationGate=createPresentationGate({extraAssets:smaaRequested?['antialias']:[],enabled:document.body.classList.contains('atelier-live')&&premiumRequested,onChange:state=>{
 dirty=true;$('assembly-canvas').setAttribute('aria-busy',String(!state.interactive));
 if(!state.interactive)$('load-message').textContent=state.message;else if(['ready','degraded'].includes(state.phase))$('viewer-status').textContent=state.message;
 document.dispatchEvent(new CustomEvent('atelier:presentation-state',{detail:state}));
}});
const publishPresentation=()=>presentationGate.publish();
document.addEventListener('atelier:request-presentation-state',publishPresentation);
resources.own('presentation readiness',()=>{presentationGate.dispose();document.removeEventListener('atelier:request-presentation-state',publishPresentation);});

let premiumFace=null;
let lowerCarrierGold=null;
// Original-part inspection must not overwrite the selected exterior design.
let inspectionBaseline=false;
const premiumActive=()=>premiumFaceVisible({enabled:!!premiumFace,openWork:openFrontActive(),movementOnly:$('movement-only').checked,isolated:!!isolated,interior:interiorView});
const replacedSources=new Set([0,155]);
const openFrontActive=()=>proposalReady&&openWork&&!inspectionBaseline&&!$('movement-only').checked&&!isolated;
function syncFrontDetails() {
  inspectionMaterials.restore();
  const premium=premiumActive();
  handClearance?.setEnabled(premium);
  const active=openFrontActive()&&!premium,finished=$('finish').checked;
  if(premiumFace)premiumFace.root.visible=premium;
  // Restore the calendar before the older form layer restores its own source.
  if(!active)frontArchitecture?.setEnabled(false);
  formDetails?.setEnabled(active);
  if(active)frontArchitecture?.setEnabled(true);
  crownVisual?.setEnabled(openFrontActive());
  // Premium replaces the complete legacy dial, including its printing layer.
  // Derive this from the selected mode, not the source visibility left by a
  // previous pass through syncFrontDetails().
  const solidPrintVisible=finished&&!!dialFace?.visible&&!active&&!premium;
  const openPrintVisible=finished&&active;
  // Until the selected first frame is revealed, avoid constructing legacy
  // comparison artwork that is hidden by the premium face.
  const mayCreatePrint=!presentationGate.snapshot().enabled||presentationGate.snapshot().interactive;
  if(mayCreatePrint&&solidPrintVisible&&!dialDetails)dialDetails=dialDetailLazy?.ensure();
  if(mayCreatePrint&&openPrintVisible&&!openDialDetails)openDialDetails=openDialDetailLazy?.ensure();
  if(dialDetails) dialDetails.group.visible=solidPrintVisible;
  if(openDialDetails) openDialDetails.group.visible=openPrintVisible;
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
  if(premium){
    for(const mesh of source)if(PREMIUM_HIDDEN_SOURCES.includes(mesh.userData.sourceIndex))mesh.visible=false;
    for(const mesh of exterior)if(['DIAL','CHAPTER'].includes(mesh.userData.assemblyId))mesh.visible=false;
    for(const mesh of openPlates)mesh.visible=structuralSupportVisible({premium,comparison:new URLSearchParams(location.search).get('supports')||'restored',replacementForSourceIndex:mesh.userData.replacementForSourceIndex});
  }
  for(const part of craftParts)part.visible=(active||premium)&&!interiorView;
  if((active||premium)&&!interiorView&&craftParts.length)for(const part of exterior)if(['STRAP-UPPER','STRAP-LOWER'].includes(part.userData.assemblyId))part.visible=false;
  backplate?.syncVisibility({openWork:!backplateGlassComparison&&openFrontActive(),interior:interiorView,movementOnly:$('movement-only').checked,isolated:!!isolated});
  applyStrapInspectionVisibility(model,inspectionDisplay);
  comparisonDetails.update(active&&mayCreatePrint);
}
let scale = 78, currentView = 'three-quarter', elapsed = 0;
let mechanism,escapement,calendar,winding,setting,settingEngagement,handClockOrigin=0, mechanismElapsed = 0, balanceElapsed = 0,crownVisual;
let settingSeconds=0,calendarState=null,engagementState=null;
let handClearance,crownCapFinish,backplate;
let frontCapNormalAudit={applied:false};
const inspectionMaterials=createInspectionMaterials({cloneMaterial:cloneAssemblyMaterial});
let inspectionDisplay={wireframe:false,solidWireframe:false,transparent:false,transparentBackplate:false,hideStrap:false};
function publishInspectionDisplay(){document.dispatchEvent(new CustomEvent('atelier:inspection-state',{detail:{...inspectionDisplay,backplateVisible:!!backplate?.mesh.visible,strapAvailable:strapInspectionAvailable({view:currentView,interior:interiorView,isolated:!!isolated,exploded:!!explosion?.active})}}));}
function changeInspectionDisplay(event){
  if(lifecycle.disposed||loading||failed||!presentationGate.snapshot().interactive)return;
  const {key,value}=event.detail||{};
  if(!Object.hasOwn(inspectionDisplay,key)||typeof value!=='boolean')return;
  if(key==='hideStrap'&&value&&!strapInspectionAvailable({view:currentView,interior:interiorView,isolated:!!isolated,exploded:!!explosion?.active}))return;
  if(key==='hideStrap'&&value&&selected.some(isStrapInspectionPart))clearSelection();
  inspectionDisplay={...inspectionDisplay,[key]:value};if(value&&['wireframe','solidWireframe','transparent'].includes(key))for(const mode of ['wireframe','solidWireframe','transparent'])if(mode!==key)inspectionDisplay[mode]=false;if(key==='hideStrap')visibility();else updateMaterials();publishInspectionDisplay();
  announce(key==='solidWireframe'?(value?'Shaded surfaces with triangle edges.':'Triangle overlay off.'):key==='transparent'?(value?'Transparent assembly inspection on.':'Original materials restored.'):key==='hideStrap'?(value?'Strap, keepers and buckle hidden for inspection. Case and rear cover are unchanged. Use Restore strap or return to Explore.':'Strap assembly restored.'):key==='wireframe'?(value?'Wireframe on for the current assembly.':'Solid surfaces restored.'):(value?'Rear cover transparent. Movement supports remain intact.':'Opaque rear cover restored.'));
}
document.addEventListener('atelier:inspection',changeInspectionDisplay);
resources.own('inspection controls',()=>document.removeEventListener('atelier:inspection',changeInspectionDisplay));
// Explicit comparison only: the selected open-work design uses the opaque metal cover.
const backplateGlassComparison=new URLSearchParams(location.search).get('backplate')==='source';
const sourceRestMatrices=new Map();
let cameraTween = null, tour = false, animationFrame=0;
const tourSequence=createTourSequence();let powerPath=false;
const lifecycle=createViewerLifecycle({pause:()=>{clock.setHidden(true);performanceMonitor.breakCadence();},
  resume:()=>{clock.setHidden(document.hidden);last=frameWindow=performance.now();dirty=true;},
  dispose:()=>{cancelAnimationFrame(animationFrame);inspectionMaterials.dispose();explosion?.dispose();try{resources.dispose();}catch(error){console.error('Viewer resource cleanup failed.',error);}}});
const smaaPreparation=smaa?prepareSMAAPass(smaa,{signal:lifecycle.signal}):null;
smaaPreparation?.ready.then(()=>{presentationGate.settle('antialias');dirty=true;}).catch(error=>{if(!lifecycle.disposed)fail('Antialiasing could not initialize. Reload the viewer to retry.',error);});
const assetOptions=()=>({loader:new GLTFLoader(),signal:lifecycle.signal,disposeUnused:gltf=>disposeObjectTree(gltf.scene)});
const comparisonDetails=createDeferredComparisonDetails({loadForm:loadFormDetails,loadArchitecture:loadFrontArchitecture,onError:(error,stage)=>{
  if(lifecycle.disposed)return;
  loadWarnings.push(`${stage==='form'?'Form detail':'Front architecture'}: ${error.message}`);
  updateMaterials();visibility();
  announce('The watch is ready. Additional comparison details are unavailable. Leave and reopen the comparison to retry.');
}});
resources.own('deferred historical comparison loading',()=>comparisonDetails.dispose());
const captureProvenance=createCaptureProvenance({signal:lifecycle.signal,loadBootRevision:()=>import('./quality-study/viewer-revision.js?v=svg03-photo09').then(module=>module.default)}),pendingCaptures=new Set();
const requestedQuality=new URLSearchParams(location.search).get('quality');
const startPaused=new URLSearchParams(location.search).get('paused')==='1';
const initialQuality=Object.hasOwn(RENDER_PROFILES,requestedQuality)?requestedQuality:(premiumRequested?'balanced':'detail');
let quality=initialQuality, renderedFrames=0, frameWindow=performance.now();
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
const announce = message => { const presentation=presentationGate.snapshot();$('viewer-status').textContent = presentation.enabled&&!['ready','degraded'].includes(presentation.phase)?presentation.message:message; document.dispatchEvent(new Event('studio-state-change')); };
function stopTour() {
  const wasRunning=tour;
  tour = false;tourSequence.stop(); cameraTween = null; $('tour').setAttribute('aria-pressed','false'); $('tour').textContent = 'Studio tour';
  if(wasRunning)announce('Studio tour paused. Choose a view or restart the tour.');
}
controls.addEventListener('start', () => { stopTour(); cameraTween = null; });
function fail(message,error) {
  failed = true; presentationGate.fail(message,error);loadPhase='error'; $('loading').hidden = false; $('load-message').textContent = message; $('retry').hidden = false;
  $('inspection-controls').disabled = true; $('view-controls').disabled = true;
  $('assembly-canvas').setAttribute('aria-busy','false'); announce(message);
  for (const id of ['primary-motion-status','motion-status']) $(id).textContent='Interactive motion unavailable. Reload the viewer to retry.';
  $('render-status').textContent='3D rendering unavailable.';
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
let parametricCase=null;
function renderingQuality(name) {
  const profile=qualityProfiles[name]; if(!profile) return;
  parametricCase?.setTextureQuality?.(name,renderer.capabilities.getMaxAnisotropy());
  quality=name; $('render-quality').value=name;
  leatherDetails?.setAnisotropy?.(leatherAnisotropy(name,renderer.capabilities.getMaxAnisotropy()));if(premiumFace?.texture){premiumFace.texture.anisotropy=leatherAnisotropy(name,renderer.capabilities.getMaxAnisotropy());premiumFace.texture.needsUpdate=true;}ao.enabled=profile.ao&&!noAoStudy;bloom.enabled=inspectionBloomEnabled(atelierVisuals&&name==='studio',inspectionDisplay); renderer.shadowMap.enabled=profile.shadows; key.castShadow=profile.shadows;
  const samples=smaaRequested?0:Math.min(profile.samples,renderer.capabilities.maxSamples);
  if(composer.aerialGPU) composer.aerialGPU.setSamples(samples);
  else for(const target of [composer.renderTarget1,composer.renderTarget2]) if(target.samples!==samples) { target.samples=samples; target.dispose(); }
  if(!profile.shadows && key.shadow.map) { key.shadow.map.dispose(); key.shadow.map=null; }
  renderedFrames=0; frameWindow=performance.now(); resize();
  $('render-status').textContent=`${profile.label} · measuring playback…`;
  announce(`${({efficient:'Smooth',balanced:'Balanced',detail:'Sharp',studio:'Studio'})[name]} quality selected.`);
}
$('render-quality').onchange=()=>renderingQuality($('render-quality').value);
renderingQuality(quality);
function stageFrameState(){return {width:$('stage').getBoundingClientRect().width,viewportWidth:window.innerWidth,viewportHeight:window.innerHeight,panelOpen:document.body.dataset.panelOpen==='true'};}
let previousStageFrame=stageFrameState();
const stageObserver=new ResizeObserver(() => {
  const nextStageFrame=stageFrameState(),panelOnly=isPanelOnlyResize(previousStageFrame,nextStageFrame,document.body.classList.contains('atelier-live'));
  previousStageFrame=nextStageFrame;
  resize();
  // Preserve position, target, zoom and any shot tween across UI-only changes.
  if (panelOnly || loading || !model) return;
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
  if(r.width<600&&['face','interior'].includes(name)){
    const framed=perspectiveFrame(watchHeadFramingPoints(model),{position:camera.position,target:controls.target,up:camera.up,fov:camera.fov,aspect:r.width/r.height,near:camera.near,fill:.94});
    if(framed){controls.target.copy(framed.target);camera.position.copy(framed.position);camera.zoom=1;scale=2*framed.distance*Math.tan(THREE.MathUtils.degToRad(camera.fov/2));camera.lookAt(controls.target);resize();return;}
  }
  const direction=camera.position.clone().sub(controls.target).normalize();
  // Narrow face/rear framing includes the offset crown beyond the case rim.
  // Macro dimensions and desktop composition retain their authored bounds.
  const framedWidth=r.width<600&&['face','interior'].includes(name)?52:width;
  scale=Math.max(height,framedWidth/(r.width/r.height)); camera.zoom=1;
  camera.position.copy(controls.target).addScaledVector(direction,scale/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))));
  camera.lookAt(controls.target); resize();
}
function fitBounds(envelope=!!explosion?.active) {
  if (!model) return;
  const r=$('stage').getBoundingClientRect();if(!r.width||!r.height)return;
  const points=visibleFramingPoints(model,{envelope,amount:explosion?.amount||0});
  const framed=perspectiveFrame(points,{position:camera.position,target:controls.target,up:camera.up,fov:camera.fov,aspect:r.width/r.height,near:camera.near});
  if(!framed)return;
  controls.target.copy(framed.target);camera.position.copy(framed.position);camera.zoom=1;
  scale=2*framed.distance*Math.tan(THREE.MathUtils.degToRad(camera.fov/2));
  camera.lookAt(controls.target);resize();
}
function view(name, transition = true, {explosionEnvelope=false}={}) {
  // A named camera leaves original-only component inspection, not its historical assembly.
  if (loading || failed) return;
  if(name!=='back'&&!explosionEnvelope)inspectionDisplay.hideStrap=false;
  const fromPosition = camera.position.clone(), fromTarget = controls.target.clone();
  if(inspectionBaseline)clearSelection();
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
    target.set(0,0,3.5); direction.set(...(premiumRequested?[0,0,1]:[.035,.065,1]));
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
  else fitBounds(explosionEnvelope||!!explosion?.active);
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
  closeDisclosureWithFocus(document.querySelector('.camera-more'),document.activeElement);
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
const carrierFinish=createCarrierFinish({supported:!!renderer.isWebGLRenderer||renderer.aerialNodeCarrierFinish?.installed===true,implementation:renderer.isWebGLRenderer?'native-glsl':'node-tsl-r02'});
carrierFinish.setEnabled(carrierFinishRequested({premiumRequested,comparison:new URLSearchParams(location.search).get('supports')??'restored',mode:new URLSearchParams(location.search).get('carrierFinish')}));
if(carrierFinish.snapshot.reason){loadWarnings.push(carrierFinish.snapshot.reason);backendIdentity.limitations.push(carrierFinish.snapshot.reason);console.warn(carrierFinish.snapshot.reason);}
resources.own('carrier circular physical finish',()=>carrierFinish.dispose());
function updateMaterials() {
  syncFrontDetails();
  casebackFinish?.setEnabled($('finish').checked);
  scene.environment = $('finish').checked ? finishes.environment : null;
  for (const material of highlights) material.dispose(); highlights.length = 0;
  for (const mesh of [...meshes(),...openPlates,...craftParts]) {
    let base = $('finish').checked && finishMaterials.has(mesh) ? finishMaterials.get(mesh) : baseMaterials.get(mesh);
    if($('finish').checked&&openFrontActive()&&mesh.userData.sourceIndex===149)base=finishes.apply({name:mesh.name,material:baseMaterials.get(mesh),userData:{...mesh.userData,finishKind:'graphite',finishZone:'circular'}});
    if($('finish').checked&&mesh.userData.sourceIndex===149&&formDetails&&!frontArchitecture?.enabled)base=formDetails.calendarMaterial(base);
    const premiumFinish=premiumActive()&&$('finish').checked?premiumMovementFinishKind(mesh.userData,mesh.name):null;
    if(premiumFinish)base=finishes.apply({name:mesh.name,material:baseMaterials.get(mesh),userData:{...mesh.userData,finishKind:premiumFinish}});
    if(lowerCarrierGold&&mesh===lowerCarrierGold.mesh)base=lowerCarrierGold.apply(base,{enabled:premiumActive()&&$('finish').checked&&!frontArchitecture?.enabled});
    base=carrierFinish.apply(mesh,base,{active:premiumActive()&&$('finish').checked});
    const pathStage=powerPath?POWER_PATH.findIndex(stage=>stage.ids.includes(mesh.userData.sourceIndex)):-1;
    mesh.material = selected.includes(mesh)||pathStage>=0 ? eachMaterial(base,material => {
      const highlighted = cloneAssemblyMaterial(material); highlighted.emissive.setHex(selected.includes(mesh)?0x6c8051:[0x927143,0x336e95,0x975b42,0x85599d][pathStage]); highlighted.emissiveIntensity = selected.includes(mesh)?.22:.42;
      highlights.push(highlighted); return highlighted;
    }) : base;
  }
  inspectionMaterials.apply(model,inspectionDisplay);
  bloom.enabled=inspectionBloomEnabled(atelierVisuals&&quality==='studio',inspectionDisplay);
  premiumFace?.tickBatch?.setEnabled?.(!GPU&&new URLSearchParams(location.search).get('tickBatch')==='1'&&!inspectionDisplay.wireframe&&!inspectionDisplay.solidWireframe&&!inspectionDisplay.transparent);
  publishInspectionDisplay();
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
  const proposed=open?(premiumActive()?[...premiumFace.meshes,...openPlates.filter(m=>m.visible),...craftParts.filter(m=>m.visible)]:[...openPlates.filter(m=>m.visible),...(openFrontFrame?.group.visible?openFrontFrame.group.children:[]),...(qualityDesign?.group.visible?qualityDesign.meshes:[]),...craftParts.filter(m=>m.visible)]):[];
  depthBounds=[...meshes().filter(mesh=>mesh.visible),...proposed].map(mesh=>new THREE.Box3().setFromObject(mesh).expandByScalar(isolated ? .05 : .5));
  controls.minDistance=isolated ? .25 : 9;
  $('interior-guide').hidden=!interiorView;
  // Hidden mechanisms still advance their clock. Catch up before a component is
  // revealed, including when playback was paused while it was out of view.
  applyClockPose(clock.snapshot());
  $('mode-label').textContent = inspectionBaseline ? 'ORIGINAL PART / TEMPORARY COMPARISON' : isolated ? `ISOLATED / ${isolated.size} MESH${isolated.size === 1 ? '' : 'ES'}` :
    movementOnly ? 'OM10 / ORIGINAL MOVEMENT' : interiorView ? 'INTERIOR / CASEBACK REMOVED' : open ? 'OPEN-WORK / FRONT DESIGN STUDY' : 'AERIAL / SOLID DIAL';
  $('show-all').disabled = !isolated && !movementOnly && !interiorView && !inspectionBaseline && !inspectionDisplay.hideStrap;
  $('isolate').disabled = !selected.length || !!isolated;
  $('visible-count').textContent = `${meshes().filter(mesh => mesh.visible).length} of ${meshes().length} original meshes visible${open?` · ${openPlates.length+(openFrontFrame?.count||0)+(qualityDesign?.count||0)} open-work parts`:''}`;
  dirty = true;
}
function clearSelection() {
  const restoreDesign=inspectionBaseline;inspectionBaseline=false;if(restoreDesign)isolated=null;
  selected = []; $('selection').hidden = true; $('isolate').disabled = true; updateMaterials();
  for (const button of $('component-list').querySelectorAll('button')) button.setAttribute('aria-pressed','false');
  if(restoreDesign){visibility();fitBounds();}
}
function select(mesh) {
  stopTour();
  const group = groups.find(entry => entry.parts.includes(mesh)); if (!group) return;
  const wasIsolated = !!isolated;
  const inspectOriginal=openWork&&(sourceNeedsBaseline(mesh.userData,replacedSources,{premium:!!premiumFace})||mesh.userData.sourceIndex===149);
  clearSelection(); inspectionBaseline=inspectOriginal;selected = group.parts; isolated = inspectOriginal?new Set(group.parts):null;
  const restoreWatch=mesh.userData.sourceIndex === undefined;
  if (restoreWatch) { $('movement-only').checked = false; interiorView=false; }
  if (mesh.userData.inspectionTransparent) $('crystals').checked = true;
  $('selection').hidden = false; $('part-name').textContent = group.label; $('part-name').title=group.label;
  $('part-role').textContent = mesh.userData.description || mesh.userData.role || 'Part of the named assembly';
  $('part-support').textContent = mesh.userData.support ? 'Attachment: '+mesh.userData.support : 'Original OM10 component — original placement preserved';
  for (const button of $('component-list').querySelectorAll('button')) button.setAttribute('aria-pressed',String(button.dataset.key === group.key));
  updateMaterials(); visibility();
  if(inspectOriginal)fitBounds();
  else if (restoreWatch && (movementViews.includes(currentView)||currentView==='interior')) view('showcase');
  else if (wasIsolated) view(currentView);
  announce(`${inspectionBaseline?'Original component comparison. Restore watch or deselect to return to the selected design. ':''}Selected ${group.label}. ${group.parts.length} mesh${group.parts.length === 1 ? '' : 'es'}. ${inspectionBaseline?'Original part isolated.':'Use Isolate selection to inspect.'}`);
}
function showAll() {
  stopTour();if(inspectionBaseline)clearSelection();
  interiorView=false; isolated = null; $('movement-only').checked = false; visibility(); view('face');
  announce(openWork?'Watch restored.':'Solid-dial watch restored.');
}
$('clear').onclick = () => {
  const key=groups.find(group=>group.parts.some(mesh=>selected.includes(mesh)))?.key;
  clearSelection(); restoreExplorerFocus($('component-list'),key,$('component-search'));
  announce('Selection cleared.');
};
$('show-all').onclick = showAll;
$('isolate').onclick = () => {inspectionDisplay.hideStrap=false;
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
      label:componentLabel(mesh.userData,mesh.name)});
    byKey.get(key).parts.push(mesh);
  }
  groups = [...byKey.values()].sort((a,b) => Number(a.original)-Number(b.original) || a.label.localeCompare(b.label,undefined,{numeric:true}));
  renderExplorer();
}
function renderExplorer() {
  const query = normalizeComponentText($('component-search').value.trim()), scope = $('component-scope').value;
  const matches = groups.filter(group => (scope === 'all' || group.original === (scope === 'movement')) &&
    [group.label,...group.parts.map(mesh => componentSearchText(mesh.userData,mesh.name))].join(' ').toLowerCase().includes(query));
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
let crownUIPulled=false;
const crownInteraction=createCrownInteraction({
  secondsPerDegree:20/3,duration:reducedMotion.matches?0:.24,
  onTurn:(degrees,state)=>{winding?.turn(degrees,{pulled:state.pulled});dirty=true;},
  onPull:pulled=>{winding?.setPulled(pulled);if(pulled){stopTour();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();}else if(winding){winding.apply();dirty=true;}},
  onSetTime:delta=>{settingSeconds-=delta;const stamp=clock.snapshot(),seconds=((stamp.hands-delta)%43200+43200)%43200;clock.seek(seconds,{track:'hands'});dirty=true;},
  onChange:state=>{
    // Stroke frames only update poses. Visibility rebuilds materials and bounds,
    // so reserve that work (and control labels) for a change of clutch mode.
    const modeChanged=crownUIPulled!==state.pulled;
    if(modeChanged){crownUIPulled=state.pulled;
      if($('crown-state'))$('crown-state').textContent=state.pulled?'Pulled · turn to set time':'Seated · turn crown';
      if($('crown-pull')){$('crown-pull').textContent=state.pulled?'Push in to finish':'Pull out to set time';$('crown-pull').setAttribute('aria-pressed',String(state.pulled));}
      if($('crown-help'))$('crown-help').textContent=state.pulled?'Turn left or right to move the hands. Push in when you are done.':'Turn left to wind the gears; turning right lets the clutch return. Watch time stays unchanged.';
      syncSimpleControls();
    }
    if(model&&!loading){if(modeChanged)visibility();else applyClockPose(clock.snapshot());}
    dirty=true;
  },
});resources.own('crown interaction',()=>crownInteraction.dispose());

function registerExplosionParts(){if(!model||!explosion)return;const parts=[];model.traverse(o=>{if(o.isMesh)parts.push(o);});explosion.register(parts);}
function announceAtelierCapabilities(){document.dispatchEvent(new CustomEvent('atelier:capabilities',{detail:{explode:!!explosion&&!loading&&!failed,crownDrag:!!crownVisual&&!loading&&!failed}}));}
function resetExplosion(instant=false){explosion?.reset({instant});document.dispatchEvent(new CustomEvent('atelier:explode-state',{detail:{amount:0}}));dirty=true;}
document.addEventListener('atelier:request-capabilities',announceAtelierCapabilities);
document.addEventListener('atelier:explode',event=>{
 const amount=event.detail?.amount;if(!explosion||loading||failed||!Number.isFinite(amount))return;
 stopTour();registerExplosionParts();
 if(amount>0){cancelCrownGesture();$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();if(!explosion.active){clearSelection();isolated=null;$('movement-only').checked=false;visibility();view('showcase',true,{explosionEnvelope:true});}}
 explosion.setAmount(amount);publishInspectionDisplay();dirty=true;
});

function focusCrown(){resetExplosion(true);if(loading||failed)return;stopTour();clearSelection();isolated=null;interiorView=false;$('movement-only').checked=false;visibility();if($('crown-controls'))$('crown-controls').open=true;view('crown');$('crown-pull')?.focus({preventScroll:true});announce('Crown controls opened. Turn while seated, or pull out to set the hands.');}
if($('crown-focus'))$('crown-focus').onclick=focusCrown;
function setCrownPulled(pulled){
  cancelCrownGesture();crownInteraction.setPulled(pulled);
  // Retain the free input's tooth take-up when reseated; this is not a stroke
  // and never seeks the hands or changes the held winding drive.
  if(pulled&&engagementState?.ready&&winding){
    const state=crownInteraction.snapshot(),degrees=state.degrees+engagementState.leadInStemDegrees;
    winding.restore({...winding.snapshot(),crownDegrees:degrees});crownInteraction.restore({...state,degrees});applyClockPose(clock.snapshot());
  }
}
if($('crown-pull'))$('crown-pull').onclick=()=>setCrownPulled(!crownInteraction.snapshot().pulled);
for(const [id,degrees]of [['crown-left',-15],['crown-right',15]])if($(id))$(id).onclick=()=>{stopTour();crownInteraction.turn(degrees);};
if($('crown-reset'))$('crown-reset').onclick=()=>{cancelCrownGesture();crownInteraction.reset();if(winding)winding.restore({...winding.snapshot(),crownDegrees:0,pulled:false,reverseFreewheel:false});applyClockPose(clock.snapshot());crownVisual?.finish();announce('Crown reseated and aligned. The current hand time is retained.');};
if($('play-motion'))$('play-motion').onclick=()=>{if(crownInteraction.snapshot().pulled)return;if(explosion?.active){announce('Reassemble the watch before playing the mechanism.');return;}stopTour();const play=!($('animate-movement').checked||$('animate').checked);$('animate-movement').checked=play;$('animate').checked=play;setClockPlayback();};
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
  const handTime=sampleSettingHandTime(elapsed,settingSeconds,t=>escapement?escapement.sample(t).trainTime:sampleMechanicalTime(t),escapement?handClockOrigin:0);
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
  cancelCrownGesture();
  $('animate-movement').checked = false; $('animate').checked = false;
  const stamp=clock.reset();settingSeconds=0;winding?.reset();crownInteraction.reset();mechanismElapsed = balanceElapsed = 0;mechanism?.reset();resetHands();applyClockPose(stamp);crownVisual?.finish();motionStatus();
  if($('scrub-time'))$('scrub-time').value='0';if($('scrub-value'))$('scrub-value').textContent='0.00 s';
}
$('speed').onchange=()=>{applyClockPose(clock.setSpeed(Number($('speed').value)));syncSimpleControls();dirty=true;};
if($('scrub-time'))$('scrub-time').oninput=()=>{
  stopTour();cancelCrownGesture();if(crownInteraction.snapshot().pulled)crownInteraction.setPulled(false);const timestamp=performance.now();$('animate-movement').checked=false;$('animate').checked=false;
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
$('reset').onclick = () => {inspectionDisplay={wireframe:false,solidWireframe:false,transparent:false,transparentBackplate:false,hideStrap:false};resetExplosion(true);
  // Reset wins over a view file still being read. Let the same file be chosen again.
  configurationRequest++;if($('import-config'))$('import-config').value='';
  crownInteraction.reset();
  stopTour(); resetMotion(); $('speed').value = '1'; $('finish').checked = true; $('crystals').checked = true;
  clock.setSpeed(1);
  openWork=true;$('open-work').checked=true;
  renderingQuality(initialQuality);
  $('component-search').value = ''; $('component-scope').value = 'all'; clearSelection(); renderExplorer(); showAll();
  announce('Open-work presentation restored and motion paused. Original movement geometry remains preserved in the baseline.');
};
document.addEventListener('keydown', event => { if (event.key === 'Escape' && !loading && !failed) {
  if($('crown-controls')?.contains(document.activeElement)){
    stopTour();clearSelection();$('crown-controls').open=false;$('crown-focus')?.focus({preventScroll:true});return;
  }
  if(isEditingControl(event.target))return;
  const cameraMenu=document.querySelector('.camera-more');
  if(cameraMenu?.open&&cameraMenu.contains(document.activeElement)){
    closeDisclosureWithFocus(cameraMenu,document.activeElement);return;
  }
  stopTour(); clearSelection();
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
  const proposed=openFrontActive()?(premiumActive()?[...premiumFace.meshes,...openPlates.filter(m=>m.visible),...craftParts.filter(m=>m.visible)]:[...openPlates.filter(m=>m.visible),...(openFrontFrame?.group.visible?openFrontFrame.group.children:[]),...(qualityDesign?.group.visible?qualityDesign.meshes:[]),...craftParts.filter(m=>m.visible)]):[];
  const hit = ray.intersectObjects([...meshes(),...proposed].filter(mesh => (mesh.visible||premiumFace?.tickBatch?.raycastVisible?.(mesh)) && !mesh.userData.inspectionTransparent),false)[0];
  if(hit && proposed.includes(hit.object)) {
    clearSelection();announce(`${hit.object.name}. Open-work design proposal; inspect its source counterpart in the component explorer.`);
  } else if(hit?.object.userData.assemblyId==='CROWN')focusCrown();
  else if (hit) select(hit.object); else clearSelection();
});

let crownDrag=null;
function hitCrown(event){if(loading||failed||explosion?.active)return false;const mesh=exterior.find(m=>m.userData.assemblyId==='CROWN');if(!mesh?.visible)return false;const r=renderer.domElement.getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1),camera);return ray.intersectObject(mesh,false).length>0;}
renderer.domElement.addEventListener('pointerdown',event=>{
 if(event.button!==0||!hitCrown(event))return;stopTour();crownDrag={id:event.pointerId,lastY:event.clientY,startX:event.clientX,startY:event.clientY,moved:false};controls.enabled=false;down=null;renderer.domElement.setPointerCapture(event.pointerId);event.preventDefault();event.stopImmediatePropagation();document.dispatchEvent(new CustomEvent('atelier:mode',{detail:{mode:'time'}}));
},true);
renderer.domElement.addEventListener('pointermove',event=>{
 if(!crownDrag||event.pointerId!==crownDrag.id)return;const dy=crownDrag.lastY-event.clientY;crownDrag.lastY=event.clientY;if(Math.hypot(event.clientX-crownDrag.startX,event.clientY-crownDrag.startY)>3)crownDrag.moved=true;if(crownDrag.moved&&dy)crownInteraction.turn(Math.max(-20,Math.min(20,dy*.65)));event.preventDefault();event.stopImmediatePropagation();
},true);
function endCrownDrag(event){if(!crownDrag||event.pointerId!==crownDrag.id)return;const moved=crownDrag.moved;crownDrag=null;controls.enabled=true;if(renderer.domElement.hasPointerCapture(event.pointerId))renderer.domElement.releasePointerCapture(event.pointerId);down=null;event.stopImmediatePropagation();if(!moved)document.dispatchEvent(new CustomEvent('atelier:mode',{detail:{mode:'time'}}));dirty=true;}
renderer.domElement.addEventListener('pointerup',endCrownDrag,true);
renderer.domElement.addEventListener('pointercancel',cancelCrownGesture,true);
function cancelCrownGesture(event){if(event?.type==='pointercancel'&&crownDrag&&event.pointerId!==crownDrag.id)return;if(event?.type==='lostpointercapture'&&!crownDrag)return;crownInteraction.cancel();if(!crownDrag)return;const id=crownDrag.id;crownDrag=null;controls.enabled=true;down=null;if(renderer.domElement.hasPointerCapture(id))renderer.domElement.releasePointerCapture(id);dirty=true;}
renderer.domElement.addEventListener('lostpointercapture',cancelCrownGesture);window.addEventListener('blur',cancelCrownGesture);document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelCrownGesture();});
renderer.domElement.addEventListener('dblclick',event=>{if(!hitCrown(event))return;event.preventDefault();event.stopImmediatePropagation();setCrownPulled(!crownInteraction.snapshot().pulled);document.dispatchEvent(new CustomEvent('atelier:mode',{detail:{mode:'time'}}));},true);

const originalVisibility = ao._overrideVisibility.bind(ao);
ao._overrideVisibility = () => {
  originalVisibility();
  for (const mesh of exterior) if (mesh.visible && mesh.userData.inspectionTransparent) { mesh.visible = false; ao._visibilityCache.push(mesh); }
  for(const detail of [dialDetails,openDialDetails]) if(detail?.group.visible) detail.group.traverse(mesh=>{
    if(mesh.isMesh&&mesh.visible&&mesh.userData.displayDetail){mesh.visible=false;ao._visibilityCache.push(mesh);}
  });
};
const glassAO=GPU?{dispose(){}}:createRefractionAwareAO({reuseSceneMatrices:true,pass:ao,compositeMaterial:nativeAO.compositeMaterial,scene,camera,getCrystals:()=>exterior.filter(mesh=>['FRONT-CRYSTAL','REAR-CRYSTAL'].includes(mesh.userData.assemblyId))});
resources.own('refraction-aligned ambient occlusion',()=>glassAO.dispose());
function proposalWarning(error){
  if(lifecycle.disposed)return;
  proposalLoading=false;loadWarnings.push(error.message);console.warn('Selected open-work design could not load.',error);visibility();presentationGate.settle('proposal',error);
  announce(presentationGate.snapshot().enabled?'The selected open-work design could not load. Reload the viewer to retry.':'Original assembly ready. The optional open-work design could not load; use Retry design to try again.');
  let retry=$('retry-proposal');if(!retry){retry=document.createElement('button');retry.id='retry-proposal';retry.type='button';retry.textContent='Retry design';$('open-work-note').after(retry);}
  retry.onclick=async()=>{retry.disabled=true;proposalLoading=true;presentationGate.retry('proposal');let result;try{result=await loadGLTFAsset(structuralSupportAsset({premiumRequested,comparison:new URLSearchParams(location.search).get('supports')||'restored'}),assetOptions());installProposal(result);retry.remove();}catch(e){if(result)try{disposeObjectTree((result.gltf||result).scene);}catch(cleanupError){console.error('Proposal cleanup failed.',cleanupError);}proposalWarning(e);}finally{if(!lifecycle.disposed)retry.disabled=false;}};
}
function installProposal(result){
  if(lifecycle.disposed){disposeObjectTree((result.gltf||result).scene);return;}
  const proposal=result.gltf||result;performanceMonitor.load(result.metrics||{});
  const candidates=[];proposal.scene.traverse(mesh=>{if(mesh.isMesh)candidates.push(mesh);});
  if(candidates.length!==2||new Set(candidates.map(mesh=>mesh.userData.replacementForSourceIndex)).size!==2||candidates.some(mesh=>!replacedSources.has(mesh.userData.replacementForSourceIndex)))throw new Error('Expected two distinct open-work plates.');
  const disposeProposal=ownedObjectTreeDisposer(proposal.scene);
  for(const mesh of candidates){
    const original=source.find(part=>part.userData.sourceIndex===mesh.userData.replacementForSourceIndex);
    openPlates.push(mesh);baseMaterials.set(mesh,mesh.material);
    finishMaterials.set(mesh,finishes.apply({name:original.name,userData:original.userData,material:mesh.material}));mesh.castShadow=true;mesh.receiveShadow=true;
  }
  model.add(proposal.scene);resources.own('optional proposed plates',disposeProposal);
  if(lowerCarrierGoldRequested({premiumRequested,comparison:new URLSearchParams(location.search).get('supports')??'restored',mode:new URLSearchParams(location.search).get('carrierGold')})&&!lowerCarrierGold){
    const carrier=candidates.find(m=>m.userData.replacementForSourceIndex===0);
    const gold=finishes.apply({name:carrier.name,material:baseMaterials.get(carrier),userData:{sourceIndex:0,finishKind:'brass'}});
    lowerCarrierGold=createLowerCarrierGoldZone(carrier,gold,{requestMode:new URLSearchParams(location.search).get('carrierGold')||'premium-default'});resources.own('lower carrier authored gold finish',()=>lowerCarrierGold.dispose());
  }
  proposalReady=true;proposalLoading=false;variantManifest=createVariantManifest(source,[...(backplate?.meshes||[]),...openPlates,...(premiumFace?.meshes||[]),...openFrontFrame.group.children,...qualityDesign.meshes,...craftParts]);updateMaterials();visibility();
  presentationGate.settle('proposal');
  announce('Open-work design ready. Explore the original movement and blued hands.');
}
async function loadFrontArchitecture(){
  if(lifecycle.disposed||frontArchitecture)return;
  const result=await loadGLTFAsset('quality-study/front-architecture-r07.glb',assetOptions());
  if(lifecycle.disposed){disposeObjectTree(result.gltf.scene);return;}
  let installed,release;
  const formWasEnabled=formDetails.enabled;
  try{
    formDetails.setEnabled(false);
    const targets=new Map(openPlates.map(mesh=>[mesh.userData.replacementForSourceIndex,mesh]));
    targets.set(149,source.find(mesh=>mesh.userData.sourceIndex===149));
    installed=createFrontArchitecture({targets,candidateScene:result.gltf.scene,revision:'r07',restMatrices:sourceRestMatrices});
    frontArchitecture=installed;
    release=resources.own('R07 front architecture',()=>installed.dispose());
    performanceMonitor.load(result.metrics);updateMaterials();visibility();
  }catch(error){
    if(frontArchitecture===installed)frontArchitecture=null;
    if(release)release();else installed?.dispose();
    formDetails.setEnabled(formWasEnabled);
    throw error;
  }finally{disposeObjectTree(result.gltf.scene);}
}
async function loadFormDetails(){
  if(lifecycle.disposed||formDetails)return;
  const result=await loadGLTFAsset('quality-study/form-legibility-r01.glb',assetOptions());
  if(lifecycle.disposed){disposeObjectTree(result.gltf.scene);return;}
  let installed,release;
  try{
    installed=createFormDetails({calendar:source.find(mesh=>mesh.userData.sourceIndex===149),caseMesh:exterior.find(mesh=>mesh.userData.assemblyId==='CASE'),candidateScene:result.gltf.scene,preserveCaseGeometry:!!parametricCase?.enabled});
    formDetails=installed;
    release=resources.own('calendar lettering and lug bevels',()=>installed.dispose());
    performanceMonitor.load(result.metrics);updateMaterials();visibility();
  }catch(error){
    if(formDetails===installed)formDetails=null;
    if(release)release();else installed?.dispose();
    throw error;
  }finally{disposeObjectTree(result.gltf.scene);}
}
function initializeBaseline(result,metadata){
  if(lifecycle.disposed){disposeObjectTree((result.gltf||result).scene);return;}
  const gltf=result.gltf||result;performanceMonitor.load(result.metrics||{});
  const disposeBaseline=ownedObjectTreeDisposer(gltf.scene);
  resources.own('original assembly geometry',disposeBaseline);
  model=new THREE.Group();model.rotation.x=Math.PI/2;model.add(gltf.scene);scene.add(model);explosion=createAssemblyExplosion({root:model,duration:reducedMotion.matches?0:.55});
  gltf.scene.traverse(mesh=>{
    if(!mesh.isMesh)return;
    if(premiumRequested&&mesh.userData.sourceIndex===12){const repair=repairFrontCapNormals(mesh);frontCapNormalAudit={applied:repair.applied,reason:repair.reason??null,revision:repair.revision??null,fixture:repair.fixture??null,faces:repair.faces??0,vertices:repair.vertices??0};if(repair.applied)resources.own('front cap analytical normal geometry',()=>repair.geometry.dispose());}
    if(mesh.userData.sourceIndex!==undefined)source.push(mesh);else exterior.push(mesh);
    if(mesh.userData.inspectionTransparent)mesh.material=eachMaterial(mesh.material,material=>{const glass=material.clone();resources.own('transparent baseline material',()=>glass.dispose());glass.transparent=true;glass.opacity=.15;glass.depthWrite=false;glass.transmission=0;return glass;});
    baseMaterials.set(mesh,parametricCase?.enabled&&mesh===parametricCase.mesh?parametricCase.plainMaterials:mesh.material);finishMaterials.set(mesh,parametricCase?.enabled&&mesh===parametricCase.mesh?parametricCase.materials:finishes.apply(mesh));mesh.castShadow=!mesh.userData.inspectionTransparent;mesh.receiveShadow=true;
    if(mesh.userData.sourceIndex===undefined){const period={HOUR:43200,MINUTE:3600,SECONDS:60}[mesh.userData.assemblyId];if(period)hands.push({mesh,period,original:mesh.quaternion.clone()});}
  });
  const rearWindow=exterior.find(mesh=>mesh.userData.assemblyId==='REAR-CRYSTAL');
  backplate=createBackplate({rearCrystal:rearWindow});rearWindow.parent.add(backplate.mesh);
  exterior.push(backplate.mesh);baseMaterials.set(backplate.mesh,backplate.mesh.material);
  const rearCoverFinish=createDarkBackplateFinish(finishes.apply(backplate.mesh));
  finishMaterials.set(backplate.mesh,rearCoverFinish);
  backplate.mesh.material.color.setHex(DARK_BACKPLATE_FINISH.color);backplate.mesh.material.roughness=DARK_BACKPLATE_FINISH.roughness;
  backplate.audit.finish=DARK_BACKPLATE_FINISH;
  resources.own('backplate private geometry and material',()=>backplate.dispose());
  resources.own('backplate private circular brushed finish',()=>rearCoverFinish.dispose());
  if(premiumRequested){handClearance=createHandClearance(exterior);resources.own('premium seconds hand clearance',()=>handClearance.dispose());}
  if(atelierVisuals&&new URLSearchParams(location.search).get('cap')==='satin'){const crown=exterior.find(mesh=>mesh.userData.assemblyId==='CROWN');crownCapFinish=createCrownCapEligibility(crown,finishMaterials.get(crown),{positionGate:false});crown.geometry=crownCapFinish.geometry;finishMaterials.set(crown,crownCapFinish.material);resources.own('satin crown cap exact eligibility',()=>{crown.material=baseMaterials.get(crown);crownCapFinish.dispose();});}
  const casebackMesh=exterior.find(mesh=>mesh.userData.assemblyId==='CASEBACK');
  if(casebackMesh){casebackFinish=createCasebackFinish({mesh:casebackMesh});resources.own('caseback cap finish geometry',()=>casebackFinish.dispose());}
  for(const mesh of source){mesh.updateMatrix();sourceRestMatrices.set(mesh.userData.sourceIndex,mesh.matrix.clone());}
  variantManifest=createVariantManifest(source,backplate.meshes);mechanism=createAssemblyMotion(source,metadata);
  try{calendar=createAssemblyCalendar(source);}catch(error){loadWarnings.push(`Calendar reconstruction unavailable: ${error.message}`);}
  const springMesh=mechanism.entries.find(entry=>entry.kind==='spring').mesh,originalSpringGeometry=springMesh.geometry;
  try{escapement=createAssemblyEscapement(mechanism);handClockOrigin=escapement.sample(0).trainTime;escapement.apply(0);}
  catch(error){loadWarnings.push(`Escapement reconstruction unavailable: ${error.message}`);mechanism.apply(0,0);}
  const displaySpringGeometry=springMesh.geometry;
  try{winding=createAssemblyWinding(source,mechanism);}catch(error){loadWarnings.push(`Winding reconstruction unavailable: ${error.message}`);}
  try{setting=createAssemblySetting(mechanism);}catch(error){loadWarnings.push(`Setting reconstruction unavailable: ${error.message}`);}
  try{if(winding&&setting)settingEngagement=createAssemblySettingEngagement(source,mechanism,winding);}catch(error){loadWarnings.push(`Setting engagement unavailable: ${error.message}`);}
  const crownMesh=exterior.find(mesh=>mesh.userData.assemblyId==='CROWN');
  if(crownMesh){crownVisual=createCrownVisual(crownMesh,{duration:0,pullDuration:reducedMotion.matches?0:.36,compact:true,stem:source.find(mesh=>mesh.userData.sourceIndex===52),tube:exterior.find(mesh=>mesh.userData.assemblyId==='CROWN-TUBE')});resources.own('crown presentation transform',()=>crownVisual.dispose());}
  dialFace=exterior.find(mesh=>mesh.userData.assemblyId==='DIAL'&&!/mark/i.test(mesh.name));
  dialDetailLazy=createLazyDetail({create:()=>createDialDetails({renderer}),attach:detail=>gltf.scene.add(detail.group)});
  openDialDetailLazy=createLazyDetail({create:()=>createDialDetails({renderer,openWork:true}),attach:detail=>gltf.scene.add(detail.group)});
  openFrontFrame=createOpenFrontFrame();gltf.scene.add(openFrontFrame.group);
  qualityDesign=createQualityDesign(source,exterior);gltf.scene.add(qualityDesign.group);
  resources.own('escapement and private spring display',()=>{if(escapement)escapement.dispose();else mechanism.reset();if(displaySpringGeometry!==originalSpringGeometry)displaySpringGeometry.dispose();});
  resources.own('winding train and private clutch spring',()=>winding?.dispose());
  resources.own('manual setting train',()=>setting?.dispose());
  resources.own('setting engagement and private clearance geometry',()=>settingEngagement?.dispose());
  resources.own('indexed calendar and private spring display',()=>calendar?.dispose());
  resources.own('dial printing',()=>{dialDetailLazy.dispose();openDialDetailLazy.dispose();});resources.own('open-work frame',()=>openFrontFrame.dispose());resources.own('quality hand design',()=>qualityDesign.dispose());
  if(premiumRequested){
    loadGLTFAsset(premiumFaceAsset(new URLSearchParams(location.search).get('face')),assetOptions()).then(result=>{
      if(lifecycle.disposed){disposeObjectTree(result.gltf.scene);return;}
      try{
        premiumFace=preparePremiumFace(result.gltf.scene,{finish:new URLSearchParams(location.search).get('finish')==='studio4'?'brushed':new URLSearchParams(location.search).get('finish'),smoothMarkers:new URLSearchParams(location.search).get('markers')!=='flat',enableTickBatch:!GPU&&new URLSearchParams(location.search).get('tickBatch')==='1'});if(premiumFace.texture){premiumFace.texture.anisotropy=leatherAnisotropy(quality,renderer.capabilities.getMaxAnisotropy());premiumFace.texture.needsUpdate=true;}model.add(premiumFace.root);
        resources.own('B premium dial',ownedObjectTreeDisposer(premiumFace.root));
        performanceMonitor.load(result.metrics||{});variantManifest=createVariantManifest(source,[...(backplate?.meshes||[]),...openPlates,...(premiumFace?.meshes||[]),...(openFrontFrame?.group.children||[]),...(qualityDesign?.meshes||[]),...craftParts]);visibility();
        presentationGate.settle('premiumFace');
        announce('Left Crescent dial ready. Original gear layout preserved.');
      }catch(error){disposeObjectTree(result.gltf.scene);throw error;}
    }).catch(error=>{if(!lifecycle.disposed){loadWarnings.push(`Premium face: ${error.message}`);console.warn('Selected premium dial could not load.',error);presentationGate.settle('premiumFace',error);announce('The selected dial could not load. Reload the viewer to retry.');}});
  }
  loading=false;$('load-message').textContent='Lighting the watch studio…';$('assembly-canvas').setAttribute('aria-busy','false');
  $('inspection-controls').disabled=false;$('view-controls').disabled=false;$('animate').disabled=hands.length!==3;
  $('animate-movement').checked=!startPaused&&!reducedMotion.matches;$('animate').checked=!startPaused&&!reducedMotion.matches&&hands.length===3;
  $('finish').checked=true;$('crystals').checked=true;$('open-work').checked=true;updateMaterials();buildExplorer();visibility();
  view(resolveInitialView(new URLSearchParams(location.search).get('view')),false);setClockPlayback();
  presentationGate.settle('baseline');
  announce('Original assembly ready. Preparing the optional open-work design.');
  const leatherAsset=photoLeatherAsset(new URLSearchParams(location.search).get('leather'))||'quality-study/leather-craft-r05.glb';
  const leatherLoad=leatherAsset===R14_LEATHER_URL?loadR14KtxLeather({onPhase:sample=>startupDiagnostics.mark('leather:'+sample.phase),renderer,makeManager:()=>new THREE.LoadingManager(),makeLoader:manager=>new GLTFLoader(manager),signal:lifecycle.signal,initialNormal:new URLSearchParams(location.search).get('normalStream')==='1'?'progressive-2k':'full',disposeUnused:gltf=>disposeObjectTree(gltf.scene)}):leatherAsset===COMPAT_LEATHER_URL?loadCompatLeather(assetOptions(),{optIn:leatherCompatRequested}):leatherAsset===KTX_LEATHER_URL?loadKtxLeather({renderer,makeManager:()=>new THREE.LoadingManager(),makeLoader:manager=>new GLTFLoader(manager),signal:lifecycle.signal,disposeUnused:gltf=>disposeObjectTree(gltf.scene)}):loadGLTFAsset(leatherAsset,assetOptions());
  leatherLoad.then(result=>{
    if(lifecycle.disposed){disposeObjectTree(result.gltf.scene);return;}
    try{
    leatherGeometryProof=result.metrics?.authoredLeather??null;
    performanceMonitor.load(result.metrics);const clay=new THREE.MeshStandardMaterial({color:0x93989b,roughness:.7});resources.own('craft comparison material',()=>clay.dispose());
    leatherDetails=(photoLeatherAsset(new URLSearchParams(location.search).get('leather'))?createPhotoLeatherDetails:createLeatherDetails)({candidateScene:result.gltf.scene,anisotropy:leatherAnisotropy(quality,renderer.capabilities.getMaxAnisotropy()),shadow:atelierVisuals?new URLSearchParams(location.search).get('shadow'):null});
    if(result.progressiveNormalBytes){
     progressiveNormalState='waiting-for-first-frame';
     progressiveNormal=createProgressiveUpgrade({lowBytes:result.progressiveNormalBytes,
      fetchFull:({low,signal})=>fetchProgressiveNormal({low,signal,baseURL:new URL('leather-assets/r14/',location.href).href}),
      decodeFull:(bytes,{signal})=>decodeFullKtx({bytes,signal,renderer,makeLoader:async()=>{const {KTX2Loader}=await import(progressiveAssetURL('./vendor/loaders/KTX2Loader.js'));return new KTX2Loader().setTranscoderPath(new URL(progressiveAssetURL('./vendor/libs/basis/'),import.meta.url).href).setWorkerLimit(2);}}),
      adopt:texture=>{leatherDetails.upgradeOuterNormal(texture);texture.dispose();progressiveNormalState='full';dirty=true;},
      onError:error=>{progressiveNormalState='failed';loadWarnings.push('Full-resolution leather normal unavailable');console.warn('Progressive normal upgrade failed; initial texture retained.',error);announce('Full-resolution leather could not load. The initial texture remains; reload to retry.');}
     });resources.own('Progressive leather normal',()=>progressiveNormal.dispose());
    }
    for(const mesh of leatherDetails.meshes){craftParts.push(mesh);baseMaterials.set(mesh,clay);finishMaterials.set(mesh,leatherDetails.materialFor(mesh));}
    model.add(leatherDetails.group);resources.own('Authored leather craft geometry',()=>leatherDetails.dispose());updateMaterials();visibility();
    variantManifest=createVariantManifest(source,[...(backplate?.meshes||[]),...openPlates,...(premiumFace?.meshes||[]),...openFrontFrame.group.children,...qualityDesign.meshes,...craftParts]);
    leatherCompatReady=leatherCompatRequested;presentationGate.settle('leather');if(leatherCompatReady)announce(COMPAT_LEATHER_WARNING);
    }finally{disposeObjectTree(result.gltf.scene);}
  }).catch(error=>{if(lifecycle.disposed)return;loadWarnings.push(`Leather detail: ${error.message}`);console.warn('Selected leather could not load.',error);presentationGate.settle('leather',error);announce(presentationGate.snapshot().enabled?'The selected leather could not load. Reload the viewer to retry.':'The watch is ready. Additional leather detail is unavailable.');});
}
const parametricCaseMode=new URLSearchParams(location.search).get('caseStudy')||'source';
function parametricCaseSnapshot(){const mesh=parametricCase?.mesh;return {requestedMode:parametricCaseMode,enabled:!!parametricCase?.enabled,privateOnly:true,effectiveRevision:parametricCase?.ownsGeometry?parametricCase.audit.revision:null,audit:parametricCase?.audit??null,normalProof:parametricCase?.finishNormalProof??null,textureFiltering:parametricCase?.textureFiltering??null,comparison:parametricCase?.finishComparison??null,lugFinish:parametricCase?.lugFinish??null,runtime:mesh?{ownedGeometry:!!parametricCase?.ownsGeometry,geometryUUID:mesh.geometry.uuid,positionCount:mesh.geometry.attributes?.position?.count??0,normalCount:mesh.geometry.attributes?.normal?.count??0,indexCount:mesh.geometry.index?.count??0,triangles:(mesh.geometry.index?.count??0)/3,groups:mesh.geometry.groups.map(g=>({...g})),materials:(Array.isArray(mesh.material)?mesh.material:[mesh.material]).map(m=>({name:m.name,roughness:m.roughness,metalness:m.metalness,texture:!!(m.map||m.normalMap||m.bumpMap||m.roughnessMap)}))}:null};}
startupDiagnostics.mark('required-assets-start');
loadProgressiveAssembly({
  signal:lifecycle.signal,disposeUnused:result=>disposeObjectTree((result.gltf||result).scene),
  loadBaseline:async()=>{
    const baseline=await loadGLTFAsset('rebuild/assembly.glb',{...assetOptions(),onProgress:p=>{if(!lifecycle.disposed&&!failed)$('load-message').textContent=`Preparing the watch · ${(p.loaded/1048576).toFixed(1)} MB`;}});
    if(parametricCaseMode!=='fine-combined')return baseline;
    const root=(baseline.gltf||baseline).scene,disposeOriginal=ownedObjectTreeDisposer(root);
    let replacement;
    try{
      const {createCombinedCaseReplacement,loadCombinedCaseAsset}=await import('./assembly-case-combined.js');
      const cases=[];root.traverse(o=>{if(o.isMesh&&o.userData.assemblyId==='CASE')cases.push(o);});
      if(cases.length!==1)throw new Error('Expected one original CASE.');
      replacement=await createCombinedCaseReplacement({sourceMesh:cases[0],signal:lifecycle.signal,lugFinish:new URLSearchParams(location.search).get('lugFinish')!=='off',nativeRenderer:!!renderer.isWebGLRenderer,nodeLugFinishSupported:renderer.aerialNodeLugFinish?.installed===true,plain:new URLSearchParams(location.search).get('caseFinish')==='plain',mapsEnabled:new URLSearchParams(location.search).get('caseMaps')!=='off',loadCandidate:()=>loadCombinedCaseAsset(assetOptions())});
      if(replacement.lugFinish?.supported===false){const reason=replacement.lugFinish.reason;loadWarnings.push(reason);backendIdentity.limitations.push(reason);console.warn(reason);}
      if(lifecycle.disposed||lifecycle.signal.aborted)throw new DOMException('Selected CASE load cancelled.','AbortError');
      let disposed=false;
      objectDisposers.set(root,()=>{if(disposed)return;disposed=true;try{replacement.dispose();}finally{disposeOriginal();}});
      replacement.setTextureQuality(quality,renderer.capabilities.getMaxAnisotropy());replacement.setEnabled(true);parametricCase=replacement;
    }catch(error){try{replacement?.dispose();}finally{disposeOriginal();}throw error;}
    return baseline;
  },
  loadMetadata:()=>loadJSONAsset('assets/manual-a-parts.json',{signal:lifecycle.signal}),
  loadProposal:()=>{proposalLoading=true;return loadGLTFAsset(structuralSupportAsset({premiumRequested,comparison:new URLSearchParams(location.search).get('supports')||'restored'}),assetOptions());},
  onBaseline:(...args)=>startupDiagnostics.measure('baseline-scene-build',()=>initializeBaseline(...args)),onProposal:(...args)=>startupDiagnostics.measure('proposal-scene-build',()=>installProposal(...args)),onWarning:proposalWarning,onPhase:phase=>{loadPhase=phase;},
}).catch(error=>{if(!lifecycle.disposed)fail(error.name==='TimeoutError'?'Loading took too long. Check your connection and reload the viewer. Static renders remain available below.':'The assembly could not load. Reload the viewer to retry. Static renders remain available below.',error);});


function inspectionReference(mesh){return mesh.userData.sourceIndex!==undefined?'source:'+mesh.userData.sourceIndex:'assembly:'+mesh.userData.assemblyId;}
function resolveInspectionState(state){const resolve=refs=>refs.flatMap(ref=>{const found=meshes().filter(mesh=>inspectionReference(mesh)===ref);if(!found.length)throw new Error('Saved component is unavailable: '+ref);return found;});return {selected:resolve(state.selected),isolated:state.isolated===null?null:resolve(state.isolated)};}
function restoreInspectionState(state){
 clearSelection();selected=state.selected;isolated=state.isolated===null?null:new Set(state.isolated);
 inspectionBaseline=openWork&&selected.some(mesh=>sourceNeedsBaseline(mesh.userData,replacedSources,{premium:!!premiumFace})||mesh.userData.sourceIndex===149);
 if(inspectionBaseline&&isolated===null)isolated=new Set(selected);
 if(selected.length){const group=groups.find(g=>g.parts.includes(selected[0]));$('selection').hidden=false;$('part-name').textContent=group?.label||'Restored components';$('part-role').textContent=selected[0].userData.description||selected[0].userData.role||'Restored assembly selection';$('part-support').textContent=selected[0].userData.support?'Attachment: '+selected[0].userData.support:'Original placement retained';}
 updateMaterials();visibility();renderExplorer();
}

function captureConfiguration({clockStamp}={}){
  const gl=renderer.getContext?.(),extension=gl?.getExtension?.('WEBGL_debug_renderer_info');
  const measuredPerformance=performanceMonitor.snapshot(),preview=$('studio-poster')?.querySelector('img');
  const previewEntry=preview?performance.getEntriesByName(preview.currentSrc).at(-1):null;
  return {progressiveNormal:progressiveNormalState,tickBatch:{requested:new URLSearchParams(location.search).get('tickBatch')==='1',supported:premiumFace?.tickBatch?.supported??false,enabled:premiumFace?.tickBatch?.enabled??false},strapInspection:strapInspectionSnapshot(model),carrierMicrofinish:carrierFinish.snapshot,receiverPlaneFinish:receiverPlaneFinish.audit,markerNormalAudit:premiumFace?.markerNormalAudit??[],ambientOcclusionImplementation:nativeAO?nativeAO.snapshot():{algorithm:'r187 SSAONode',requested:aoQuery||'default',actual:'baseline',reason:aoQuery==='gtao'?'Native GTAO selection does not apply to optional node backend; node GTAO remains separately held':null},lowerCarrierGold:lowerCarrierGold?.snapshot??{requested:false,active:false},parametricCase:parametricCaseSnapshot(),frontCapNormalAudit,leatherCompatibility:leatherCompatibility(),structuralSupport:structuralSupportSnapshot(openPlates,{premium:premiumActive(),comparison:new URLSearchParams(location.search).get('supports')||'restored'}),version:1,date:new Date().toISOString(),inspection:{selected:[...new Set(selected.map(inspectionReference))],isolated:isolated?[...new Set([...isolated].map(inspectionReference))]:null},renderer:{threeRevision:THREE.REVISION,backend:backendIdentity.actual,backendIdentity,smaa:!!smaa,canvasAntialiasRequested:!smaaRequested,transmissionSamples:backendIdentity.transmissionSamples,transmissionPatchActive:THREE.WebGLRenderer?.toString().includes('aerialTransmissionSamples === 0')??false,bloom:bloom.enabled,ambientOcclusion:ao.enabled,aoShadowReuse:!!aoShadowReuse,shadowRadius:key.shadow.radius,shadowNormalBias:key.shadow.normalBias,shadowFilter:renderer.shadowMap.type===THREE.PCFShadowMap?'PCF':'PCFSoft',toneMapping:renderer.toneMapping===THREE.AgXToneMapping?'AgX':'ACES',reflectionRig:atelierVisuals?(['atelier2','atelier3','softbox','studio4'].includes(new URLSearchParams(location.search).get('light'))?new URLSearchParams(location.search).get('light'):'atelier'):'legacy',finishTrial:['atelier2','atelier3','brushed','studio4'].includes(new URLSearchParams(location.search).get('finish'))?new URLSearchParams(location.search).get('finish'):'baseline',clearTransmission:atelierVisuals&&new URLSearchParams(location.search).get('crystal')==='clear'},explosion:explosion?.amount??0,handClearance:{enabled:!!handClearance?.enabled,...PREMIUM_HAND_CLEARANCE},crownCapFinish:{active:!!crownCapFinish&&$('finish').checked,audit:crownCapFinish?.audit??null},premiumFace:{requested:premiumRequested,ready:!!premiumFace,active:premiumActive(),revision:premiumFace?.revision??null,materials:(premiumFace?.meshes??[]).filter(mesh=>(Array.isArray(mesh.material)?mesh.material:[mesh.material]).some(m=>/Graphite/i.test(m.name))).map(mesh=>({name:mesh.name,receiveShadow:mesh.receiveShadow,materials:(Array.isArray(mesh.material)?mesh.material:[mesh.material]).map(m=>({name:m.name,bump:!!m.bumpMap,roughnessMap:!!m.roughnessMap,normal:!!m.normalMap,bumpScale:m.bumpScale,textureRevision:m.bumpMap?.userData?.brushRevision??null}))}))},design:premiumRequested?'Aerial Left Crescent B':'Aerial Quality 01',phase:loadPhase,view:currentView,
    camera:{position:camera.position.toArray(),target:controls.target.toArray(),zoom:camera.zoom,fov:camera.fov,near:camera.near,far:camera.far},
    formDetails:{revision:'form-legibility-r01',ready:!!formDetails,enabled:!!formDetails?.enabled,calendarDigitIslands:formDetails?.audit.components??null},
    frontArchitecture:{revision:'front-architecture-r07',ready:!!frontArchitecture,enabled:!!frontArchitecture?.enabled,audit:frontArchitecture?.audit??null},
    escapement:{revision:'r09-contact-reconstruction',ready:!!escapement,limits:escapement?.limits??null},
    calendar:{revision:'r09-indexed-calendar',ready:!!calendar,state:calendarState},
    winding:{revision:'r09-crown-coupling',ready:!!winding,state:winding?.snapshot()??null},
    setting:{revision:'r09-friction-setting',ready:!!setting},
    backplate:{visible:!!backplate?.mesh.visible,mode:backplateGlassComparison?'exhibition-glass-comparison':inspectionDisplay.transparentBackplate?'transparent-cover-inspection':'dark-metal-cover',audit:backplate?.audit??null},
    casebackFinish:{revision:'r10-cap-corner-normals',enabled:!!casebackFinish?.enabled,audit:casebackFinish?.audit??null},
    settingEngagement:{revision:'r09-keyless-endpoints',ready:!!settingEngagement,state:engagementState,limits:settingEngagement?.limits??null},
    leatherShadow:leatherDetails?.shadowAudit??null,
    leatherCraft:{effectiveOuterMaterials:(leatherDetails?.meshes??[]).filter(mesh=>mesh.userData.designPart==='QUALITY-STRAP'&&/^(ISOLATED STUDY|leather \/)/.test(mesh.material.name)).map(mesh=>({mesh:mesh.name,material:mesh.material.name,normalScale:mesh.material.normalScale?.toArray()??null,baseColorFactor:mesh.material.color?.toArray()??null,roughnessFactor:mesh.material.roughness,positionCount:mesh.geometry.attributes.position.count,uvCount:mesh.geometry.attributes.uv?.count??0,indexCount:mesh.geometry.index?.count??0,maps:Object.fromEntries(['map','normalMap','roughnessMap'].map(key=>{const t=mesh.material[key];return[key,t?{repeat:t.repeat.toArray(),offset:t.offset.toArray(),rotation:t.rotation,texCoord:t.channel,format:t.format,colorSpace:t.colorSpace,anisotropy:t.anisotropy}:null];}))})),variant:new URLSearchParams(location.search).get('leather'),candidate:new URLSearchParams(location.search).get('leather')==='craft14'?{...leatherCandidateDiagnostics(leatherGeometryProof),normalIdentity:R14_NORMAL_IDENTITY}:null,revision:leatherCaptureRevision(new URLSearchParams(location.search).get('leather'),leatherDetails?.revision),ready:!!leatherDetails,parts:craftParts.length,filtering:leatherDetails?.filtering??null},
    compactCrown:!!crownVisual&&openFrontActive(),
    settingSeconds,clock:clockStamp||clock.snapshot(),crown:crownInteraction.snapshot(),sourceAtCapture:captureProvenance.snapshot(),options:{...inspectionDisplay,openWork:$('open-work').checked,finishes:$('finish').checked,crystals:$('crystals').checked,movementOnly:$('movement-only').checked,interior:interiorView,powerPath,quality},
    viewport:{width:renderer.domElement.clientWidth,height:renderer.domElement.clientHeight,pixelRatio:renderer.getPixelRatio(),drawingBufferWidth:renderer.domElement.width,drawingBufferHeight:renderer.domElement.height,msaaSamples:composer.renderTarget1.samples,transmissionScale:backendIdentity.transmission?.effectiveScale??renderer.transmissionResolutionScale,requestedTransmissionScale:renderer.transmissionResolutionScale},
    sourceMeshes:source.length,sourceVisible:source.filter(m=>m.visible).length,derivedParts:(backplate?.meshes.length||0)+(premiumFace?.meshes.length||0)+openPlates.length+(openFrontFrame?.count||0)+(qualityDesign?.count||0)+craftParts.length,lightRig:lighting.shot,
    resourceAccounting:window.assemblyResourceInspect?.()??null,performance:measuredPerformance,gpuTiming:gpuTiming.snapshot(),gpuPassTiming:passTiming?.snapshot()??null,resources:resources.snapshot(),warnings:[...loadWarnings],
    navigationTiming:{moduleBootMs:bootTime,firstInteractiveMs:measuredPerformance.firstInteractiveMs===null?null:bootTime+measuredPerformance.firstInteractiveMs,
      preview:preview?{path:new URL(preview.currentSrc).pathname,decoded:preview.complete&&preview.naturalWidth>0,responseEndMs:previewEntry?.responseEnd??null}:null,
      note:'Times are relative to document navigation. Preview response completion/decoded state does not measure its first painted frame.'},
    pageTransfers:performance.getEntriesByType('resource').map(entry=>({path:new URL(entry.name).pathname,startMs:entry.startTime,endMs:entry.responseEnd,transferBytes:entry.transferSize,encodedBodyBytes:entry.encodedBodySize})),
    GPU:extension?gl.getParameter(extension.UNMASKED_RENDERER_WEBGL):'unavailable',manifest:variantManifest,
    transport:performance.getEntriesByType('resource').filter(e=>/\.glb/.test(e.name)).map(e=>({name:new URL(e.name).pathname,transferSize:e.transferSize,encodedBodySize:e.encodedBodySize,decodedBodySize:e.decodedBodySize,duration:e.duration})),
  };
}
const downloads=createDownloadManager();
resources.own('download object URLs',()=>downloads.dispose());
const downloadBlob=(blob,name)=>downloads.save(blob,name);
const recorder=createCanvasRecorder({canvas:renderer.domElement,onStatus:announce});
resources.own('canvas motion recorder',()=>recorder.dispose());
if($('record-scene'))$('record-scene').onclick=async()=>{
  $('record-scene').disabled=true;
  try{const result=await recorder.start();downloadBlob(result.blob,'aerial-motion.webm');}
  catch(error){if(error.name!=='AbortError')announce(`Could not record: ${error.message}`);}
  finally{if(!lifecycle.disposed)$('record-scene').disabled=false;}
};
if($('refresh-diagnostics'))$('refresh-diagnostics').onclick=()=>{$('diagnostics-report').textContent=JSON.stringify(captureConfiguration(),null,2);};
if($('start-measurement'))$('start-measurement').onclick=()=>{performanceMonitor.reset();gpuTiming.reset();passTiming?.reset();$('diagnostics-report').textContent='New measurement started. Refresh after the desired playback interval.';};
if($('export-config'))$('export-config').onclick=async()=>{
  if(crownInteraction.active||crownVisual?.active||pendingCaptures.has('export-config'))return;pendingCaptures.add('export-config');
  try{await captureProvenance.resolve();if(lifecycle.disposed)return;if(crownInteraction.active||crownVisual?.active)throw new Error('Wait for the crown motion to finish.');downloadBlob(new Blob([JSON.stringify(captureConfiguration(),null,2)],{type:'application/json'}),'aerial-view.json');}
  catch(error){announce(`Could not save view: ${error.message}`);}finally{pendingCaptures.delete('export-config');}
};
if($('capture-scene'))$('capture-scene').onclick=async()=>{
  if(crownInteraction.active||crownVisual?.active||pendingCaptures.has('capture-scene'))return;pendingCaptures.add('capture-scene');announce('Preparing PNG image…');
  try{await captureProvenance.resolve();if(lifecycle.disposed)return;if(crownInteraction.active||crownVisual?.active)throw new Error('Wait for the crown motion to finish.');
    const stamp=clock.tick(performance.now());applyClockPose(stamp);updateInspectionDepth(camera,controls.target,depthBounds,ao,isolated?{distanceFloor:.25,surfacePadding:.05}:undefined);renderer.info.reset();
    const gpuSample=gpuTiming.begin();try{composer.render();}finally{if(gpuSample)gpuTiming.end();}
    const configuration=captureConfiguration({clockStamp:stamp}),blob=await captureCanvasPNG(renderer.domElement);
    if(!blob)throw new Error('The canvas could not create an image.');if(lifecycle.disposed)return;
    downloadBlob(await embedPNGConfiguration(blob,configuration),'aerial-studio.png');announce('PNG download requested. Check your browser downloads.');
  }catch(error){announce(`Could not save image: ${error.message}`);}finally{pendingCaptures.delete('capture-scene');}
};
let configurationRequest=0;
if($('import-config'))$('import-config').onchange=async event=>{
  const input=event.target,file=input.files?.[0];if(!file)return;
  const request=++configurationRequest;
  try{if(loading||failed)throw new Error('Wait for the watch to finish loading.');if(file.size>1048576)throw new Error('View file is too large.');
    const config=validateViewConfiguration(JSON.parse(await file.text()),{qualities:Object.keys(qualityProfiles)});if(lifecycle.disposed||request!==configurationRequest)return;
    const restoredInspection=resolveInspectionState(config.inspection);explosion?.reset({instant:true});
    stopTour();isolated=null;clearSelection();view(config.view,false);
    openWork=config.options.openWork;$('open-work').checked=openWork;$('finish').checked=config.options.finishes;$('crystals').checked=config.options.crystals;$('movement-only').checked=config.options.movementOnly;
    if(typeof config.options.interior==='boolean')interiorView=config.options.interior;
    inspectionDisplay={wireframe:config.options.wireframe===true,solidWireframe:config.options.solidWireframe===true,transparent:config.options.transparent===true,transparentBackplate:config.options.transparentBackplate===true,hideStrap:config.options.hideStrap===true};
    powerPath=!!config.options.powerPath;if($('power-path'))$('power-path').checked=powerPath;
    if($('power-path-description'))$('power-path-description').textContent=powerPath?'Barrel → wheel train → escapement → balance. Original source parts highlighted.':'';
    updateMaterials();visibility();renderingQuality(config.options.quality);
    const damping=controls.enableDamping;controls.enableDamping=false;controls.update();
    camera.position.fromArray(config.camera.position);controls.target.fromArray(config.camera.target);camera.zoom=config.camera.zoom;camera.fov=config.camera.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();controls.enableDamping=damping;
    resetMotion();clock.setSpeed(config.clock.speed);
    if(![...$('speed').options].some(option=>Number(option.value)===config.clock.speed)){$('speed').querySelector('[data-saved-speed]')?.remove();const option=new Option(`${config.clock.speed}× · saved time scale`,String(config.clock.speed));option.dataset.savedSpeed='true';$('speed').add(option);}
    $('speed').value=String(config.clock.speed);
    settingSeconds=config.settingSeconds;winding?.restore(config.winding);crownInteraction.restore(config.crown);
    clock.seek(config.clock.mechanism,{track:'mechanism'});applyClockPose(clock.seek(config.clock.hands,{track:'hands'}));crownVisual?.finish();restoreInspectionState(restoredInspection);if(config.view==='crown'&&$('crown-controls'))$('crown-controls').open=true;registerExplosionParts();explosion?.setAmount(config.explosion,{instant:true});document.dispatchEvent(new CustomEvent('atelier:explode-state',{detail:{amount:config.explosion,reason:'restore',view:config.view,interior:interiorView,crownPulled:!!config.crown.pulled,selected:restoredInspection.selected.length>0,isolated:restoredInspection.isolated!==null}}));motionStatus();dirty=true;announce('Saved camera, crown, options, time scale, explosion and pose restored. Motion is paused.');
  }catch(e){if(!lifecycle.disposed&&request===configurationRequest)announce(`Could not restore view: ${e.message}`);}finally{if(request===configurationRequest)input.value='';}
};
let last = 0;
const screenVisibility=observeViewerVisibility($('stage'),{onChange:visible=>{
  if(visible){const now=performance.now();clock.tick(now);last=frameWindow=now;renderedFrames=0;performanceMonitor.breakCadence();dirty=true;}
}});
resources.own('screen visibility observer',()=>screenVisibility.dispose());
function frame(time) {
  if(lifecycle.disposed)return;
  animationFrame=requestAnimationFrame(frame);
  gpuTiming.poll();passTiming?.poll(); // Resolve earlier samples even when this frame will not draw.
  if (skipViewerFrame({hidden:document.hidden,failed,contextLost,viewportVisible:screenVisibility.visible,recording:recorder.recording})) { last = time; return; }
  if(time-last<15)return;const cpuStart=performance.now(),stamp=clock.tick(time);
  // Camera, lighting and tour are presentation timelines, not physics steps.
  // Clamping elapsed time made a short camera move take many seconds at low FPS.
  const delta=Math.max(0,stamp.delta);last=time;
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
  for(const id of ['capture-scene','export-config'])if($(id))$(id).disabled=loading||failed||!!cameraTween||crownInteraction.active||!!crownVisual?.active||!!explosion?.animating||pendingCaptures.has(id);
  const ready=String(!loading&&!failed&&!cameraTween&&!lightingChanged&&!crownInteraction.active&&!crownVisual?.active);if($('stage').dataset.cameraReady!==ready)$('stage').dataset.cameraReady=ready;
  if(dirty) updatePins();
  if (tour) {
    if(tourSequence.tick(delta))tourView();
  }
  let visibleMotion=false;
  // Queue rotation until the independent axial presentation reaches its endpoint.
  const crownChanged=!loading&&!explosion?.active&&!crownVisual?.pullActive&&crownInteraction.update(delta);
  if(crownChanged){dirty=visibleMotion=true;}
  if(!loading&&!explosion?.active){
    const moving=$('animate-movement').checked&&mechanism.entries.some(entry=>entry.mesh.visible&&(entry.kind!=='wheel'||entry.rate!==0));
    const movingHands=$('animate').checked&&(hands.some(hand=>hand.mesh.visible)||openFrontActive());
    if((moving||movingHands)&&!crownChanged){applyClockPose(clock.snapshot(time));dirty=visibleMotion=true;}
  }
  if(explosion?.active){registerExplosionParts();if(explosion.update(delta))dirty=visibleMotion=true;}
  if(crownVisual?.update(delta)){dirty=true;visibleMotion=true;}
  // Canvas capture needs drawn frames even when the watch and camera are paused.
  // Keep its timeline advancing without changing either presentation clock.
  if ((dirty || recorder.recording) && presentationGate.snapshot().canRender) {
    try {
      const depth=updateInspectionDepth(camera,controls.target,depthBounds,ao,isolated?{distanceFloor:.25,surfacePadding:.05}:undefined);
      controls.minDistance=depth.minimumDistance;
      if(firstRender)startupDiagnostics.mark('first-frame-submit-start');
      renderer.info.reset();const gpuSample=gpuTiming.begin();
      try{composer.render();renderedFrames++;dirty=false;presentationGate.rendered(!premiumRequested||premiumActive());}finally{if(gpuSample)gpuTiming.end();}
      if(firstRender)startupDiagnostics.mark('first-frame-submit-end');
      performanceMonitor.frame({timestamp:time,cpuMs:performance.now()-cpuStart,drawCalls:renderer.info.render.drawCalls??renderer.info.render.calls,triangles:renderer.info.render.triangles,geometries:renderer.info.memory.geometries,textures:renderer.info.memory.textures});
      if(firstRender&&!loading&&presentationGate.snapshot().interactive){firstRender=false;if(progressiveNormal){progressiveNormalState='upgrading';progressiveNormal.afterFirstSelectedFrame();}startupDiagnostics.mark('first-selected-frame');startupDiagnostics.stop();$('loading').hidden=true;if($('studio-poster'))$('studio-poster').hidden=true;performanceMonitor.interactive(performance.now()-bootTime);announceAtelierCapabilities();}
    }
    catch (error) { fail('The graphics renderer could not display this assembly. Retry the viewer or inspect the static renders below.',error); }
  }
  if(!loading && time-frameWindow>=1500) {
    const running=visibleMotion || tour || cameraTween || recorder.recording;
    const rate=Math.round(renderedFrames*1000/(time-frameWindow));
    $('render-status').textContent=`${backendIdentity.actual}${backendIdentity.fallbackReason?' (fallback)':''} · ${qualityProfiles[quality].label} · ${running ? `${rate} fps` : 'still view, renders on change'}`;
    renderedFrames=0; frameWindow=time;
  }
}
animationFrame=requestAnimationFrame(frame);
document.addEventListener('visibilitychange',()=>{const now=performance.now();clock.setHidden(document.hidden,now);last=frameWindow=now;renderedFrames=0;performanceMonitor.breakCadence();dirty=true;});
window.addEventListener('pagehide',event=>lifecycle.hide(event));
window.addEventListener('pageshow',()=>lifecycle.show());
resize();
window.assemblyResourceInspect=()=>{
 const inventory=resourceSnapshot({renderer,scene,targets:[...(composer.aerialTargets?.()||[]),...(glassAO.renderTargets?.()||[])]});
 if(!GPU&&backendIdentity.overscan){const p=backendIdentity.overscan,scale=renderer.transmissionResolutionScale;inventory.privateTargetEstimates=[{...estimateRenderTarget({label:'native WebGL internal transmission (not publicly observable)',width:Math.floor(p.renderWidth*scale),height:Math.floor(p.renderHeight*scale),samples:Math.max(4,renderer.capabilities.samples||0),generateMipmaps:true,resolveDepthBuffer:false,storeMultisampledDepthBuffer:false}),formatAssumption:'Conservative RGBA16F scenario; renderer may use RGBA8 if half-float attachment support is absent. Not a measured target.'}];}
 return inventory;
};
window.assemblyInspect = () => ({viewportVisible:screenVisibility.visible,comparisonLoading:comparisonDetails.snapshot(),strapInspection:strapInspectionSnapshot(model),startup:startupDiagnostics.snapshot(),parametricCase:parametricCaseSnapshot(),inspectionDisplay:{...inspectionDisplay,...inspectionMaterials.snapshot()},leatherCompatibility:leatherCompatibility(),backplate:{visible:!!backplate?.mesh.visible,mode:backplateGlassComparison?'exhibition-glass-comparison':inspectionDisplay.transparentBackplate?'transparent-cover-inspection':'dark-metal-cover',audit:backplate?.audit??null},loading,failed,presentation:presentationGate.snapshot(),sourceMeshes:source.length,sourceVisible:source.filter(mesh=>mesh.visible).length,
  interiorView,dialPrinting:!!dialDetails?.group.visible,renderQuality:quality,
  openWork:openFrontActive(),replacementPlates:openPlates.length,
  exteriorMeshes:exterior.length,exteriorVisible:exterior.filter(mesh=>mesh.visible).length,
  hiddenStructuralSource:source.filter(mesh=>!mesh.visible).map(mesh=>mesh.name),movementOnly:$('movement-only').checked,
  crystals:$('crystals').checked,finish:$('finish').checked,animation:$('animate').checked,animationHandCount:hands.length,
  interiorAnimation:$('animate-movement').checked,interiorAnimatedMeshes:mechanism?.count || 0,mechanismElapsed,balanceElapsed,
  studioTour:tour,mechanicalTiming:mechanism?.timing,
  illustrativeElapsed:elapsed,isolated:!!isolated,componentGroups:groups.length,selected:selected.map(mesh=>mesh.name),view:currentView,
  camera:camera.position.toArray(),target:controls.target.toArray(),triangles:meshes().filter(mesh=>mesh.visible).reduce((sum,mesh)=>sum+(mesh.geometry.index?.count||mesh.geometry.attributes.position.count)/3,0)});

let strapQaState=null,strapQaOriginal=null,strapQaCandidate=null,strapQaVisibility=null;
function strapUpper(){return (leatherDetails?.meshes||[]).filter(m=>m.userData.designPart==='QUALITY-STRAP'&&['STRAP-UPPER','STRAP-LOWER'].includes(m.userData.replacesAssemblyId));}
function strapQaApply(){
 if(!strapQaState)return;const {view,variant}=strapQaState;const all=strapUpper();
 // Native installed geometry only: never swap geometry in this release gate.
 const [half,side,kind]=view.split('/');const owner=half==='lower'?'STRAP-LOWER':'STRAP-UPPER';
 const body=all.filter(m=>m.userData.replacesAssemblyId===owner);
 const show=new Set((leatherDetails?.meshes||[]).filter(m=>m.userData.replacesAssemblyId===owner));
 scene.traverse(o=>{if(o.isMesh)o.visible=show.has(o)});for(const m of show)for(let p=m;p;p=p.parent)p.visible=true;
 depthBounds=body.map(m=>new THREE.Box3().setFromObject(m));
 const sx=side==='left'?-1:1,sy=half==='lower'?-1:1;
 let position,target,fov;
 if(kind==='close'){position=[sx*12.5,sy*20.9,2.8];target=[sx*9.94,sy*22.4,.52];fov=12;}
 else if(kind==='neck'){position=[sx*12,sy*20,-1];target=[sx*9.94,sy*22.4,-2.5];fov=18;}
 else if(kind==='context'){position=[sx*14,sy*20.9,1.6];target=[sx*9.94,sy*22.4,-.8];fov=38;}
 else {position=[35,-sy*15,18];target=[0,sy*10,-15];fov=50;}
 camera.up.set(0,0,1);camera.position.fromArray(position);controls.target.fromArray(target);camera.fov=fov;camera.near=.01;camera.updateProjectionMatrix();camera.lookAt(controls.target);
}
window.__strapQaSetup=async()=>{if(strapUpper().length!==6)throw Error('Expected six native body meshes');strapQaVisibility=new Map();scene.traverse(o=>{if(o.isMesh)strapQaVisibility.set(o,o.visible)});stopTour();cameraTween=null;controls.enabled=false;controls.enableDamping=false;$('animate-movement').checked=false;$('animate').checked=false;setClockPlayback();return {inspect:assemblyInspect(),leather:{ready:!!leatherDetails,diagnostics:leatherCandidateDiagnostics(leatherGeometryProof),revision:leatherDetails?.revision},bodies:strapUpper().map(m=>({name:m.name,material:m.material.name,triangles:m.geometry.index.count/3}))};};
window.__strapQaView=(view,variant)=>{strapQaState={view,variant};strapQaApply();dirty=true;return {view,variant,camera:camera.position.toArray(),target:controls.target.toArray(),upper:strapUpper().map(m=>({name:m.name,triangles:m.geometry.index.count/3,materialUUID:m.material.uuid,material:m.material.name,maps:Object.fromEntries(['map','normalMap','roughnessMap'].map(k=>[k,m.material[k]?{uuid:m.material[k].uuid,compressed:!!m.material[k].isCompressedTexture,format:m.material[k].format,anisotropy:m.material[k].anisotropy,width:m.material[k].image?.width,height:m.material[k].image?.height}:null]))}))};};
window.__strapQaCapture=()=>{strapQaApply();composer.render();renderer.getContext().finish();return {png:renderer.domElement.toDataURL('image/png'),width:renderer.domElement.width,height:renderer.domElement.height,lightingShot:lighting.shot,cameraZoom:camera.zoom,cameraMatrix:camera.matrixWorld.toArray(),progressiveNormal:progressiveNormalState,effectiveQuality:quality,renderer:renderer.constructor.name,webglRenderer:renderer.getContext().getParameter(renderer.getContext().RENDERER),camera:{fov:camera.fov,position:camera.position.toArray(),target:controls.target.toArray()},drawCalls:renderer.info.render.calls};};
const strapQaNormalMaps=new Map();window.__strapQaNormalMap=(enabled)=>{for(const m of strapUpper()){const mat=m.material;if(!strapQaNormalMaps.has(mat))strapQaNormalMaps.set(mat,mat.normalMap);mat.normalMap=enabled?strapQaNormalMaps.get(mat):null;mat.needsUpdate=true;}dirty=true;};

window.__strapQaQuality=(name)=>{renderingQuality(name);return quality;};

let strapRaking=null;window.__strapQaRake=(half,side)=>{if(!strapRaking){strapRaking=new THREE.DirectionalLight(0xffffff,3);scene.add(strapRaking,strapRaking.target);}const sx=side==='left'?-1:1,sy=half==='lower'?-1:1;strapRaking.position.set(sx*12,sy*20,-2);strapRaking.target.position.set(sx*9.94,sy*22.4,-2.5);};

window.__strapQaLit=(half,side)=>{const sx=side==='left'?-1:1,sy=half==='lower'?-1:1;const key=new THREE.DirectionalLight(0xffffff,8);key.position.set(sx*20,sy*17,5);key.target.position.set(sx*9.94,sy*22.4,-1);scene.add(key,key.target);scene.add(new THREE.AmbientLight(0xffffff,2));};

window.__strapWhole=()=>{strapQaState=null;for(const[o,v]of strapQaVisibility)o.visible=v;depthBounds=[];camera.up.set(0,0,1);camera.position.set(65,-90,80);controls.target.set(0,0,0);camera.fov=35;camera.near=.1;camera.updateProjectionMatrix();camera.lookAt(controls.target);dirty=true;};
window.__strapControls=()=>{const refs=strapUpper().map(m=>({m,g:m.geometry,mat:m.material}));$('reset').click();const finish=$('finish');finish.checked=false;finish.dispatchEvent(new Event('change'));finish.checked=true;finish.dispatchEvent(new Event('change'));return {sameGeometry:refs.every(r=>r.m.geometry===r.g),sameMaterials:refs.every(r=>r.m.material===r.mat),triangles:strapUpper().reduce((n,m)=>n+m.geometry.index.count/3,0),hybrid:hybridCaseSnapshot()};};
let budgetPose=null;function budgetQaApply(){if(!budgetPose)return;cameraTween=null;camera.position.fromArray(budgetPose.position);controls.target.fromArray(budgetPose.target);controls.minDistance=0;controls.maxDistance=Infinity;camera.fov=budgetPose.fov;camera.zoom=1;camera.aspect=800/600;camera.lookAt(controls.target);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);}
window.__budgetConfigure=(mode,view)=>{
 const stage=$('stage');stage.style.width='800px';stage.style.height='600px';stage.style.minHeight='600px';stage.style.maxHeight='none';
 __strapWhole();applyClockPose(clock.seek(0));renderingQuality(mode);resize();
 if(view==='front'){camera.position.set(0,-9,90);controls.target.set(0,0,0);camera.fov=35;}
 if(view==='oblique'){camera.position.set(45,-60,35);controls.target.set(0,0,0);camera.fov=30;}
 budgetPose={position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov};budgetQaApply();
 // Same rendering state for both variants; do not turn off effects to hide differences.
 return {quality,stage:stage.getBoundingClientRect().toJSON(),camera:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov};
};
window.__budgetCapture=()=>{
 budgetQaApply();const start=performance.now();const cap=__strapQaCapture();return {...cap,transmission:backendIdentity.transmission,overscan:backendIdentity.overscan,actualTarget:window.__qaTransmissionTarget,captureWallMS:performance.now()-start,scope:'Software-rendered capture wall time includes export and is not hardware GPU timing or device FPS.'};
};
// Release-only verification helpers. No application policy or model substitution.
let releaseReferences=null;
window.__releaseInvariant=()=>{
 const meshes=strapUpper();
 if(!releaseReferences)releaseReferences=meshes.map(m=>({m,g:m.geometry,material:m.material,maps:Object.fromEntries(['map','normalMap','roughnessMap'].map(k=>[k,m.material[k]]))}));
 return {sameGeometry:releaseReferences.every(r=>r.m.geometry===r.g),sameMaterials:releaseReferences.every(r=>r.m.material===r.material),sameMaps:releaseReferences.every(r=>Object.entries(r.maps).every(([k,v])=>r.material[k]===v)),triangles:meshes.reduce((n,m)=>n+m.geometry.index.count/3,0),hybrid:hybridCaseSnapshot(),maps:meshes.map(m=>({name:m.name,maps:Object.fromEntries(['map','normalMap','roughnessMap'].map(k=>[k,m.material[k]?{uuid:m.material[k].uuid,width:m.material[k].image?.width,height:m.material[k].image?.height,compressed:!!m.material[k].isCompressedTexture}:null]))}))};
};
window.__releaseResize=(width,height)=>{
 const stage=$('stage');stage.style.width=width+'px';stage.style.height=height+'px';stage.style.minHeight=height+'px';stage.style.maxHeight='none';resize();budgetQaApply();composer.render();renderer.getContext().finish();
 return {stage:{width,height},transmission:{...backendIdentity.transmission},actualTarget:structuredClone(window.__qaTransmissionTarget),beauty:{width:renderer.domElement.width,height:renderer.domElement.height}};
};
window.__releaseQualityStableMaps=()=>{
 const before=__releaseInvariant();
 if(!before.sameGeometry||!before.sameMaterials)throw Error('Quality switch changed native geometry/material identity');
 for(const r of releaseReferences)r.maps=Object.fromEntries(['map','normalMap','roughnessMap'].map(k=>[k,r.material[k]]));
 return {before,stable:__releaseInvariant(),scope:'After all quality changes and resize checks; progressive normal-map upgrades may replace texture objects, never geometry/materials. Subsequent controls must preserve these stable map objects.'};
};
// Supplemental coverage uses existing named views and the supported inspection event.
window.__releaseSupportedView=(mode,name,transparentBackplate=false)=>{
 if(!['face'].includes(name)||!document.querySelector(`[data-view="${name}"]`))throw Error('Unsupported supplemental view '+name);
 budgetPose=null;__strapWhole();camera.up.set(0,1,0);camera.fov=32;camera.zoom=1;
 const stage=$('stage');stage.style.width='800px';stage.style.height='600px';stage.style.minHeight='600px';stage.style.maxHeight='none';
 stopTour();interiorView=false;isolated=null;$('movement-only').checked=false;visibility();
 document.dispatchEvent(new CustomEvent('atelier:inspection',{detail:{key:'transparentBackplate',value:transparentBackplate}}));
 applyClockPose(clock.seek(0));renderingQuality(mode);resize();view(name,false);
 budgetPose={position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov};budgetQaApply();
 const direction=camera.position.clone().sub(controls.target).normalize().toArray();
 const rearCrystal=exterior.find(m=>m.userData.assemblyId==='REAR-CRYSTAL');
 const optical=m=>m?{name:m.name,visible:m.visible,material:m.material.name,transmission:m.material.transmission??null,opacity:m.material.opacity,transparent:m.material.transparent}:null;
 return {intendedView:name,actualView:currentView,quality,transparentBackplateRequested:transparentBackplate,inspectionDisplay:{...inspectionDisplay},stage:stage.getBoundingClientRect().toJSON(),camera:{position:camera.position.toArray(),target:controls.target.toArray(),up:camera.up.toArray(),fov:camera.fov,direction},backplate:optical(backplate?.mesh),rearCrystal:optical(rearCrystal),lightingShot:lighting.shot,source:'Existing view(name,false) and atelier:inspection event; no invented view ID.'};
};
window.__releaseRestoreBackplate=()=>document.dispatchEvent(new CustomEvent('atelier:inspection',{detail:{key:'transparentBackplate',value:false}}));
// QA-only startup drain after ordinary default-entry proof, at explicitly selected Efficient.
window.__releaseDrain=()=>{composer.render();renderer.getContext().finish();return {quality,viewport:{width:renderer.domElement.width,height:renderer.domElement.height},transmission:backendIdentity.transmission,scope:'Software queue drain only; not a speed/FPS measurement.'};};
// Optional scoped rear inspection, unused by front/live capture gates.
window.__releaseRearHideStrap=(enabled=true)=>{
 if(currentView!=='back')throw Error('Hide strap diagnostic requires supported Reverse view first');
 document.dispatchEvent(new CustomEvent('atelier:inspection',{detail:{key:'hideStrap',value:enabled}}));
 if(inspectionDisplay.hideStrap!==enabled)throw Error('Supported rear hide-strap control did not apply');
 return {view:currentView,inspectionDisplay:{...inspectionDisplay},strap:strapInspectionSnapshot(model),source:'Supported atelier:inspection hideStrap event; no manual mesh visibility override.'};
};

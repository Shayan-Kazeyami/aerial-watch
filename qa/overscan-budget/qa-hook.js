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
window.__budgetConfigure=(mode,view)=>{
 const stage=$('stage');stage.style.width='1100px';stage.style.height='740px';stage.style.minHeight='740px';stage.style.maxHeight='none';
 __strapWhole();renderingQuality(mode);resize();
 if(view==='front'){camera.position.set(0,-9,90);controls.target.set(0,0,0);camera.fov=35;}
 if(view==='oblique'){camera.position.set(45,-60,35);controls.target.set(0,0,0);camera.fov=30;}
 camera.lookAt(controls.target);camera.updateMatrixWorld(true);camera.updateProjectionMatrix();
 // Same rendering state for both variants; do not turn off effects to hide differences.
 return {quality,stage:stage.getBoundingClientRect().toJSON(),camera:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov};
};
window.__budgetCapture=()=>{
 const costs=[];for(let n=0;n<3;n++){const t=performance.now();composer.render();renderer.getContext().finish();costs.push(performance.now()-t);}
 return {...__strapQaCapture(),transmission:backendIdentity.transmission,overscan:backendIdentity.overscan,actualTarget:window.__qaTransmissionTarget,cpuBlockingMS:costs,scope:'SwiftShader blocking submission timing only; not hardware GPU timing or device FPS.'};
};

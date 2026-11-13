// QA-only: appended inside assembly-review.js module; no rendering/geometry changes.
window.watchGeometryInventory=()=>{
 const geometryIds=new Map(), materialIds=new Map(), rows=[];
 const id=(map,value)=>{if(!map.has(value))map.set(value,map.size+1);return map.get(value)};
 const path=o=>{const a=[];for(let p=o;p;p=p.parent)a.unshift(p.name||p.type);return a.join(' / ')};
 scene.traverse(o=>{
  if(!o.isMesh||!o.geometry)return;
  const g=o.geometry,total=g.index?.count??g.attributes.position?.count??0;
  let visible=true;for(let p=o;p;p=p.parent)visible=visible&&p.visible;
  const materials=Array.isArray(o.material)?o.material:[o.material];
  const instances=o.isInstancedMesh?o.count:(g.isInstancedBufferGeometry?g.instanceCount:1);
  const start=Math.max(0,g.drawRange.start),end=Math.min(total,Number.isFinite(g.drawRange.count)?start+g.drawRange.count:total);
  const groups=Array.isArray(o.material)?g.groups:[{start:0,count:total,materialIndex:0}];
  const ranges=groups.map(gr=>{const m=materials[gr.materialIndex||0];return {start:gr.start,count:gr.count,material:gr.materialIndex||0,visible:!!m&&m.visible!==false,triangles:Math.max(0,Math.floor((Math.min(end,gr.start+gr.count)-Math.max(start,gr.start))/3))}});
  const drawn=ranges.filter(r=>r.visible&&r.triangles>0);
  rows.push({name:o.name||'(unnamed)',path:path(o),objectId:o.id,geometryId:id(geometryIds,g),materialIds:materials.map(m=>id(materialIds,m)),triangles:Math.floor(total/3),vertices:g.attributes.position?.count??0,instances:Number.isFinite(instances)?instances:null,instanceExpandedTriangles:Number.isFinite(instances)?Math.floor(total/3)*instances:null,effectiveVisible:visible,ownVisible:o.visible,visibleRangeTriangles:visible&&Number.isFinite(instances)?drawn.reduce((s,r)=>s+r.triangles,0)*instances:0,baseMaterialDrawsBeforeCulling:visible?drawn.length:0,materialNames:materials.map(m=>m?.name||''),materialTypes:materials.map(m=>m?.type||''),transparent:materials.some(m=>m?.transparent),transmission:materials.map(m=>m?.transmission||0),castShadow:o.castShadow,receiveShadow:o.receiveShadow,frustumCulled:o.frustumCulled,layers:o.layers.mask,lodAncestor:(()=>{for(let p=o.parent;p;p=p.parent)if(p.isLOD)return p.name||p.type;return null})(),groups:ranges,drawRange:{start,end},userData:Object.fromEntries(Object.entries(o.userData||{}).filter(([k,v])=>v===null||["string","number","boolean"].includes(typeof v)))});
 });
 rows.sort((a,b)=>b.instanceExpandedTriangles-a.instanceExpandedTriangles||a.name.localeCompare(b.name));
 const unique=[...geometryIds.keys()];
 return {schemaVersion:1,url:location.href,time:new Date().toISOString(),quality,backend:backendIdentity,explosion:explosion?.snapshot(),rendererInfo:{render:{...renderer.info.render},memory:{...renderer.info.memory},autoReset:renderer.info.autoReset},rows,totals:{meshObjects:rows.length,visibleObjects:rows.filter(r=>r.effectiveVisible).length,uniqueGeometries:unique.length,uniqueGeometryTriangles:unique.reduce((s,g)=>s+(g.index?.count??g.attributes.position?.count??0)/3,0),instanceExpandedResidentTriangles:rows.reduce((s,r)=>s+(r.instanceExpandedTriangles||0),0),visibleRangeTrianglesBeforeCulling:rows.reduce((s,r)=>s+r.visibleRangeTriangles,0),baseMaterialDrawsBeforeCulling:rows.reduce((s,r)=>s+r.baseMaterialDrawsBeforeCulling,0)},limitations:['Triangles, not original authoring quads/ngons. Hidden resident replacements included explicitly.','VisibleRangeTriangles respects ancestors, material visibility, drawRange and groups but not camera frustum, layers, occlusion or clipping.','Base material draws excludes shadow/transmission/postprocessing passes. Renderer info describes last actual submitted composed frame, not instantaneous FPS.','Instanced draw counts do not multiply by instance count; triangle work does.','Unique geometry totals deduplicate geometry objects, not coincident vertices across independent buffers.']};
};

window.__crownQA=()=>({state:crownInteraction.snapshot(),hotspot:crownHotspot.snapshot(),hidden:document.hidden,focus:document.hasFocus(),viewport:screenVisibility.visible,failed,loading});

const mobileAudit={poseCalls:0,poseMs:0};const originalApplyClockPose=applyClockPose;applyClockPose=function(...args){const t=performance.now();try{return originalApplyClockPose(...args)}finally{mobileAudit.poseCalls++;mobileAudit.poseMs+=performance.now()-t}};
window.mobileAuditSnapshot=()=>({...__crownQA(),...mobileAudit,settingSeconds,explosion:explosion.snapshot(),crown:crownVisual?.active,canvas:[renderer.domElement.width,renderer.domElement.height],timeOrigin:performance.timeOrigin});
window.mobileAuditFrames=(n=4)=>new Promise(resolve=>{function tick(){if(--n<=0)resolve(mobileAuditSnapshot());else requestAnimationFrame(tick)}requestAnimationFrame(tick)});
window.crownPoseParity=async()=>{
 async function capture(){model.updateMatrixWorld(true);const matrices=[],geometry=[];const seen=new Set();model.traverse(o=>{if(!o.isMesh)return;matrices.push([o.name,...o.matrixWorld.elements]);const a=o.geometry?.attributes.position;if(a&&!seen.has(a)){seen.add(a);geometry.push(a)}});const hashes=await Promise.all(geometry.map(async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new Uint8Array(a.array.buffer,a.array.byteOffset,a.array.byteLength)))).map(x=>x.toString(16).padStart(2,'0')).join('')));return{matrices,hashes,crown:crownInteraction.snapshot(),winding:winding.snapshot(),settingSeconds};}
 const results=[];
 for(const pulled of[false,true]){
  async function run(immediate){resetMotion();setCrownPulled(pulled);crownVisual.finish();for(const d of[2,2,2,-2,-2,12,-12,3.5]){if(immediate)crownInteraction.turn(d,{immediate:true});else{crownInteraction.cancel();crownInteraction.turn(d);crownInteraction.finish()}}return capture()}
  const original=await run(false),candidate=await run(true);let maxMatrixDifference=0;for(let i=0;i<original.matrices.length;i++)for(let j=1;j<17;j++)maxMatrixDifference=Math.max(maxMatrixDifference,Math.abs(original.matrices[i][j]-candidate.matrices[i][j]));
  results.push({pulled,maxMatrixDifference,positionsExact:JSON.stringify(original.hashes)===JSON.stringify(candidate.hashes),crownExact:JSON.stringify(original.crown)===JSON.stringify(candidate.crown),windingExact:JSON.stringify(original.winding)===JSON.stringify(candidate.winding),settingExact:original.settingSeconds===candidate.settingSeconds,meshCount:original.matrices.length,geometryCount:original.hashes.length});
 }
 resetMotion();return results;
};
// Find an actual direct-mesh touch surface, excluding the DOM dot hitbox.
window.crownMeshPoint=()=>{
 const mesh=exterior.find(m=>m.userData.assemblyId==='CROWN');if(!mesh)return null;
 model.updateWorldMatrix(true,true);camera.updateMatrixWorld();
 const box=new THREE.Box3().setFromObject(mesh),r=renderer.domElement.getBoundingClientRect(),dot=document.querySelector('.crown-hotspot').getBoundingClientRect(),pts=[];
 for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z]){const p=new THREE.Vector3(x,y,z).project(camera);pts.push({x:r.left+(p.x+1)*r.width/2,y:r.top+(1-p.y)*r.height/2})}
 const bounds={left:Math.min(...pts.map(p=>p.x)),right:Math.max(...pts.map(p=>p.x)),top:Math.min(...pts.map(p=>p.y)),bottom:Math.max(...pts.map(p=>p.y))};
 for(let y=Math.ceil(bounds.top);y<bounds.bottom;y+=2)for(let x=Math.ceil(bounds.left);x<bounds.right;x+=2){if(x>=dot.left-2&&x<=dot.right+2&&y>=dot.top-2&&y<=dot.bottom+2)continue;if(document.elementFromPoint(x,y)!==renderer.domElement)continue;if(hitCrown({clientX:x,clientY:y}))return{x,y,bounds,dot:dot.toJSON()};}return null;
};
window.prepareCrownMeshTouch=()=>{cancelCrownGesture();resetMotion();view('crown',false);cameraTween=null;controls.update();dirty=true;};
const unifiedSnapshot=window.mobileAuditSnapshot;
window.mobileAuditSnapshot=()=>({...unifiedSnapshot(),camera:{p:camera.position.toArray(),q:camera.quaternion.toArray(),t:controls.target.toArray(),zoom:camera.zoom},orbitEnabled:controls.enabled});
window.crownQAReset=()=>resetMotion();

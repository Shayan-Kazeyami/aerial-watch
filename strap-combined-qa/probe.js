// QA only. Appended inside the actual viewer module; no render or geometry mutation.
window.leatherQASnapshot=()=>{
 model.updateMatrixWorld(true);
 const rows=(leatherDetails?.meshes||[]).map(o=>({name:o.name,material:o.material?.name,vertices:o.geometry.attributes.position.count,triangles:(o.geometry.index?.count||o.geometry.attributes.position.count)/3,matrix:o.matrixWorld.toArray(),maps:['map','normalMap','roughnessMap'].map(k=>({name:k,ready:!!o.material?.[k],width:o.material?.[k]?.image?.width??o.material?.[k]?.source?.data?.width??null})),visible:o.visible}));
 return {proof:leatherGeometryProof,rows,loading,failed,explosion:explosion.snapshot(),canvas:[renderer.domElement.width,renderer.domElement.height],timeOrigin:performance.timeOrigin};
};
window.leatherQAFrames=(n=4)=>new Promise(resolve=>{function tick(){if(--n<=0)resolve(leatherQASnapshot());else requestAnimationFrame(tick)}requestAnimationFrame(tick)});
window.leatherQAPose=(amount,pulled)=>{resetMotion();setCrownPulled(pulled);crownVisual.finish();explosion.setAmount(amount,{instant:true});dirty=true;};
window.leatherQAContactData=()=>{
 model.updateMatrixWorld(true);const result=[];
 for(const o of exterior){let visible=true;for(let p=o;p;p=p.parent)visible=visible&&p.visible;if(!visible||!o.geometry)continue;const id=o.userData.assemblyId||o.userData.replacesAssemblyId||o.name;if(!/CASE|LUG|SPRINGBAR|BUCKLE|KEEPER|TANG/.test(id))continue;const a=o.geometry.attributes.position;result.push({name:o.name,id,matrix:o.matrixWorld.toArray(),position:Array.from(a.array),index:o.geometry.index?Array.from(o.geometry.index.array):null});}
 return {hardware:result,leather:leatherQASnapshot().rows};
};

// Isolated QA instrumentation, no changes to renderer logic or object geometry.
const springQAUploads=new Map(),springQABound=new Map();
const springQAGL=renderer.getContext(),springQABind=springQAGL.bindBuffer.bind(springQAGL),springQAData=springQAGL.bufferData.bind(springQAGL);
springQAGL.bindBuffer=function(target,buffer){springQABound.set(target,buffer);return springQABind(target,buffer)};
springQAGL.bufferData=function(target,data,...args){if(ArrayBuffer.isView(data))springQAUploads.set(springQABound.get(target),{array:data,bytes:data.byteLength});return springQAData(target,data,...args)};
window.springQAPose=(amount,pulled)=>{resetMotion();setCrownPulled(pulled);crownVisual.finish();explosion.setAmount(amount,{instant:true});dirty=true;};
window.springQAFrames=(n=6)=>new Promise(resolve=>{function tick(){if(--n<=0)resolve();else requestAnimationFrame(tick)}requestAnimationFrame(tick)});
const springQAArray=a=>a.isInterleavedBufferAttribute?a.data.array:a.array;
const springQAHash=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a.buffer.slice(a.byteOffset,a.byteOffset+a.byteLength)))).map(x=>x.toString(16).padStart(2,'0')).join('');
window.springQASnapshot=async(pattern="^KEEPER")=>{
 model.updateMatrixWorld(true);const objects=exterior.filter(o=>new RegExp(pattern).test(o.userData.assemblyId||'')).sort((a,b)=>a.name.localeCompare(b.name));if(objects.some(o=>!o))throw Error('springbar missing');const used=new Set(),rows=[];
 for(const o of objects){const attrs={};for(const key of ['position','normal','uv']){const a=o.geometry.attributes[key];if(!a){attrs[key]=null;continue;}const ar=springQAArray(a);attrs[key]={count:a.count,itemSize:a.itemSize,bytes:ar.byteLength,hash:await springQAHash(ar)};if(key!=='uv')for(const [glBuffer,info]of springQAUploads)if(info.array===ar)used.add(glBuffer)}const wp=[],wn=[],nm=new THREE.Matrix3().getNormalMatrix(o.matrixWorld);for(let i=0;i<o.geometry.attributes.position.count;i++){wp.push(...new THREE.Vector3().fromBufferAttribute(o.geometry.attributes.position,i).applyMatrix4(o.matrixWorld).toArray());wn.push(...new THREE.Vector3().fromBufferAttribute(o.geometry.attributes.normal,i).applyNormalMatrix(nm).toArray());}rows.push({worldPositions:wp,worldNormals:wn,name:o.name,matrix:o.matrixWorld.toArray(),attrs,triangles:o.geometry.index.count/3,indexHash:await springQAHash(o.geometry.index.array)});}
 return {rows,sharedGeometry:objects[0].geometry===objects[1].geometry,assetDelivery:window.springQAAssetDelivery,sharedPositionAttribute:objects[0].geometry.attributes.position===objects[1].geometry.attributes.position,sharedNormalAttribute:objects[0].geometry.attributes.normal===objects[1].geometry.attributes.normal,distinctUVAttribute:objects[0].geometry.attributes.uv!==objects[1].geometry.attributes.uv,uploadedPositionNormalBuffers:used.size,uploadedPositionNormalBytes:[...used].reduce((sum,x)=>sum+springQAUploads.get(x).bytes,0),canvas:[renderer.domElement.width,renderer.domElement.height],timeOrigin:performance.timeOrigin,loading,failed};
};
let combinedVisualLights=false,combinedWireMaterials=new Map(),combinedDisposal=null;
window.combinedVisual=(view)=>{
 resetMotion();cameraTween=null;controls.enableDamping=false;controls.minDistance=.01;controls.maxDistance=1000;
 for(const [m,value]of combinedWireMaterials)m.wireframe=value;combinedWireMaterials.clear();
 let selected=[];if(view.startsWith('keeper'))selected=exterior.filter(o=>/^KEEPER/.test(o.userData.assemblyId||''));
 else selected=(leatherDetails?.meshes||[]).filter(o=>/upper/i.test(o.name));
 if(!selected.length)throw Error('No selected visual objects for '+view);
 const visible=new Set(selected);scene.traverse(o=>{if(o.isMesh)o.visible=visible.has(o)});for(const o of selected)for(let a=o;a;a=a.parent)a.visible=true;
 if(!combinedVisualLights){const hemi=new THREE.HemisphereLight(0xe9f3ff,0x87786b,3.2);scene.add(hemi);for(const [color,intensity,pos]of [[0xffedd7,3.4,[.2,-1,1]],[0xdfeaff,2.4,[-.7,.3,.6]]]){const l=new THREE.DirectionalLight(color,intensity);l.position.fromArray(pos).multiplyScalar(100);scene.add(l)}combinedVisualLights=true;}
 model.updateMatrixWorld(true);const outer=selected.find(o=>o.material?.name.startsWith('leather /'))||selected[0];const box=new THREE.Box3();for(const o of selected)box.union(new THREE.Box3().setFromObject(o));let target=box.getCenter(new THREE.Vector3()),direction=new THREE.Vector3(.12,.28,-1).transformDirection(outer.matrixWorld),distance=box.getSize(new THREE.Vector3()).length()*1.85;
 if(view.includes('macro')){target.set(-8.628563,-23.382097,-31.224955).applyMatrix4(outer.matrixWorld);direction.set(.03638512,.00341668,-.78478926).transformDirection(outer.matrixWorld);distance=.75;}
 if(view.startsWith('keeper')){target.set(0,-22.776734352111824,-39.33527946472167);direction.set(3.1726176317411965,-49.21521461662178,-22.150267292790186).sub(target);distance=direction.length();direction.normalize();}
 if(view.endsWith('wire'))for(const o of selected)for(const m of Array.isArray(o.material)?o.material:[o.material]){if(!combinedWireMaterials.has(m))combinedWireMaterials.set(m,m.wireframe);m.wireframe=true;}
 controls.target.copy(target);camera.position.copy(target).addScaledVector(direction,distance);camera.near=.001;camera.far=2000;camera.updateProjectionMatrix();camera.lookAt(target);controls.update();dirty=true;
 return {view,objects:selected.map(o=>({name:o.name,visible:o.visible,triangles:o.geometry.index?.count/3})),camera:camera.position.toArray(),target:target.toArray(),lighting:'Identical QA hemisphere and directional fill; original loaded materials except explicit wire views',ao:'off on both variants',diagnosticWire:view.endsWith('wire')};
};
window.combinedArmDisposal=()=>{
 const objects=exterior.filter(o=>/^KEEPER/.test(o.userData.assemblyId||'')),geometries=[...new Set(objects.map(o=>o.geometry))],arrays=new Set(objects.flatMap(o=>['position','normal'].map(k=>springQAArray(o.geometry.attributes[k])))),buffers=new Set([...springQAUploads].filter(([gl,info])=>arrays.has(info.array)).map(([gl])=>gl));
 const events=new Map(geometries.map(g=>[g,0])),deleted=new Map([...buffers].map(b=>[b,0]));for(const g of geometries)g.addEventListener('dispose',()=>events.set(g,events.get(g)+1));const original=springQAGL.deleteBuffer.bind(springQAGL);springQAGL.deleteBuffer=function(buffer){if(deleted.has(buffer))deleted.set(buffer,deleted.get(buffer)+1);return original(buffer)};
 combinedDisposal={geometries,events,deleted};return {uniqueKeeperGeometries:geometries.length,positionNormalBuffers:buffers.size};
};
window.combinedTeardown=()=>{lifecycle.hide({persisted:false});lifecycle.hide({persisted:false});return {lifecycleDisposed:lifecycle.disposed,geometryEvents:[...combinedDisposal.events.values()],bufferDeletes:[...combinedDisposal.deleted.values()]};};

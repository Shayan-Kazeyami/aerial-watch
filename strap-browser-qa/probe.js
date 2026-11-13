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
window.leatherQAFocus=(macro=false)=>{
 resetMotion();cameraTween=null;const mesh=leatherDetails.meshes.find(o=>/upper/i.test(o.name)&&o.material?.name.startsWith('leather /'));if(!mesh)throw Error('Upper outer skin not found');mesh.updateWorldMatrix(true,false);
 const box=new THREE.Box3().setFromObject(mesh),target=box.getCenter(new THREE.Vector3());let direction=new THREE.Vector3(-.5,.35,1).normalize(),distance=box.getSize(new THREE.Vector3()).length()*1.1;
 if(macro){target.set(-8.628563,-23.382097,-31.224955).applyMatrix4(mesh.matrixWorld);direction.set(.03638512,.00341668,-.78478926).transformDirection(mesh.matrixWorld);distance=1.8;}
 controls.minDistance=.1;controls.maxDistance=1000;controls.target.copy(target);camera.position.copy(target).addScaledVector(direction,distance);camera.near=.01;camera.updateProjectionMatrix();camera.lookAt(target);controls.update();dirty=true;
};

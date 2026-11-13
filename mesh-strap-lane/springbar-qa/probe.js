// Isolated QA instrumentation, no changes to renderer logic or object geometry.
const springQAUploads=new Map(),springQABound=new Map();
const springQAGL=renderer.getContext(),springQABind=springQAGL.bindBuffer.bind(springQAGL),springQAData=springQAGL.bufferData.bind(springQAGL);
springQAGL.bindBuffer=function(target,buffer){springQABound.set(target,buffer);return springQABind(target,buffer)};
springQAGL.bufferData=function(target,data,...args){if(ArrayBuffer.isView(data))springQAUploads.set(springQABound.get(target),{array:data,bytes:data.byteLength});return springQAData(target,data,...args)};
window.springQAPose=(amount,pulled)=>{resetMotion();setCrownPulled(pulled);crownVisual.finish();explosion.setAmount(amount,{instant:true});dirty=true;};
window.springQAFrames=(n=6)=>new Promise(resolve=>{function tick(){if(--n<=0)resolve();else requestAnimationFrame(tick)}requestAnimationFrame(tick)});
const springQAArray=a=>a.isInterleavedBufferAttribute?a.data.array:a.array;
const springQAHash=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a.buffer.slice(a.byteOffset,a.byteOffset+a.byteLength)))).map(x=>x.toString(16).padStart(2,'0')).join('');
window.springQASnapshot=async()=>{
 model.updateMatrixWorld(true);const objects=['SPRINGBAR-UPPER','SPRINGBAR-LOWER'].map(id=>exterior.find(o=>o.userData.assemblyId===id));if(objects.some(o=>!o))throw Error('springbar missing');const used=new Set(),rows=[];
 for(const o of objects){const attrs={};for(const key of ['position','normal','uv']){const a=o.geometry.attributes[key],ar=springQAArray(a);attrs[key]={count:a.count,itemSize:a.itemSize,bytes:ar.byteLength,hash:await springQAHash(ar)};if(key!=='uv')for(const [glBuffer,info]of springQAUploads)if(info.array===ar)used.add(glBuffer)}rows.push({name:o.name,matrix:o.matrixWorld.toArray(),attrs,triangles:o.geometry.index.count/3,indexHash:await springQAHash(o.geometry.index.array)});}
 return {rows,assetDelivery:window.springQAAssetDelivery,sharedPositionAttribute:objects[0].geometry.attributes.position===objects[1].geometry.attributes.position,sharedNormalAttribute:objects[0].geometry.attributes.normal===objects[1].geometry.attributes.normal,distinctUVAttribute:objects[0].geometry.attributes.uv!==objects[1].geometry.attributes.uv,uploadedPositionNormalBuffers:used.size,uploadedPositionNormalBytes:[...used].reduce((sum,x)=>sum+springQAUploads.get(x).bytes,0),canvas:[renderer.domElement.width,renderer.domElement.height],timeOrigin:performance.timeOrigin,loading,failed};
};
window.springQAFocus=()=>{resetMotion();cameraTween=null;const o=exterior.find(o=>o.userData.assemblyId==='SPRINGBAR-UPPER');model.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(o),target=box.getCenter(new THREE.Vector3());controls.target.copy(target);camera.position.copy(target).add(new THREE.Vector3(2,-22,15));controls.minDistance=.1;camera.near=.01;camera.updateProjectionMatrix();camera.lookAt(target);controls.update();dirty=true;};

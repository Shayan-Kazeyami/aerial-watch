window.graphiteQa={
 status(){const mesh=openFrontFrame?.group.children.find(m=>m.name==='Graphite chapter / integrated twelve signature');return {ready:!!mesh&&!loading&&!failed&&proposalReady,premiumRequested,premiumActive:premiumActive(),frameVisible:openFrontFrame?.group.visible,meshVisible:mesh?.visible,vertices:mesh?.geometry.attributes.position.count}},
 async setup(data){
  const status=this.status();if(!status.ready||status.premiumRequested||status.premiumActive||!status.frameVisible)throw Error('Not authentic nonpremium visible frame: '+JSON.stringify(status));
  this.mesh=openFrontFrame.group.children.find(m=>m.name==='Graphite chapter / integrated twelve signature');this.original=this.mesh.geometry;this.other=[];scene.traverse(m=>{if(m.isMesh&&m!==this.mesh)this.other.push([m,m.geometry])});
  this.sourceGuards={};for(const attr of ['position','normal','uv']){const src=this.original.attributes[attr].array,exp=data.source[attr].data;const encoded=data.source[attr].rawBase64;const raw=encoded?Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)):null;const actual=new Uint8Array(src.buffer,src.byteOffset,src.byteLength);let max=0,numericMismatch=0,bitMismatch=0,first=[];for(let i=0;i<Math.min(src.length,exp.length);i++){max=Math.max(max,Math.abs(src[i]-exp[i]));if(src[i]!==exp[i]){numericMismatch++;if(first.length<3)first.push([i,src[i],exp[i]])}}if(raw)for(let i=0;i<actual.length;i++)if(actual[i]!==raw[i])bitMismatch++;this.sourceGuards[attr]={length:src.length,expected:exp.length,maxAbsDelta:max,numericMismatch,bitMismatch,first};}if(Object.values(this.sourceGuards).some(g=>g.length!==g.expected||g.numericMismatch||g.bitMismatch))throw Error('Source geometry guard mismatch: '+JSON.stringify(this.sourceGuards));
  this.candidate=new THREE.BufferGeometry();for(const attr of ['position','normal','uv'])this.candidate.setAttribute(attr,new THREE.BufferAttribute(new Float32Array(Uint8Array.from(atob(data.candidate[attr].rawBase64),c=>c.charCodeAt(0)).buffer),data.candidate[attr].itemSize));this.candidate.computeBoundingSphere();this.candidate.computeBoundingBox();
  this.sourceData=data.source;this.candidateData=data.candidate;this.sourceMeta={name:this.mesh.name,userData:JSON.stringify(this.mesh.userData),parent:this.mesh.parent,material:this.mesh.material};stopTour();cameraTween=null;controls.enableDamping=false;clock.setRunning('mechanism',false);clock.setRunning('hands',false);clock.seek(0,{track:'mechanism'});clock.seek(0,{track:'hands'});applyClockPose(clock.snapshot());return {status,sourceGuards:this.sourceGuards,sourceVertices:this.original.attributes.position.count,candidateVertices:this.candidate.attributes.position.count,otherMeshCount:this.other.length};
 },
 capture({candidate,view,finish}){
  if(finish!==undefined){$('finish').checked=finish;updateMaterials();visibility();}this.mesh.geometry=candidate?this.candidate:this.original;registerExplosionParts();explosion.setAmount(view==='exploded'?1:0,{instant:true});scene.updateMatrixWorld(true);
  if(!openFrontFrame.group.visible||premiumActive()||premiumRequested)throw Error('Authentic frame visibility changed');
  cameraTween=null;controls.enabled=false;camera.up.set(0,0,-1);camera.zoom=1;
  if(view==='macro'){
   const center=openFrontFrame.group.localToWorld(new THREE.Vector3(0,13.15,3.5));controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(0,15,.001));camera.zoom=3;camera.lookAt(center);
  }else{
   const center=new THREE.Box3().setFromObject(this.mesh).getCenter(new THREE.Vector3());controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(0,85,view==='exploded'?8:.001));camera.lookAt(center);
  }
  camera.updateProjectionMatrix();controls.update();scene.updateMatrixWorld(true);applyClockPose(clock.snapshot());renderer.info.reset();
  for(let i=0;i<3;i++){mechanismBatch.build(source);try{mechanismBatch.beforeRender();composer.render()}finally{mechanismBatch.afterRender()}}
  if(this.mesh.name!==this.sourceMeta.name||JSON.stringify(this.mesh.userData)!==this.sourceMeta.userData||this.mesh.parent!==this.sourceMeta.parent)throw Error('Target identity changed');
  if(this.other.some(([m,g])=>m.geometry!==g))throw Error('Other mesh geometry identity changed');
  const a=this.mesh.geometry.attributes;const bounds=new THREE.Box3().setFromObject(this.mesh);const pixelsPerMmMax=this.projectionBound();
  return {state:{candidate,view,finish},authentic:this.status(),target:{name:this.mesh.name,userData:this.mesh.userData,world:this.mesh.matrixWorld.elements.slice(),materialName:this.mesh.material.name,position:a.position.count,normal:a.normal.count,uv:a.uv.count,bounds:[bounds.min.toArray(),bounds.max.toArray()]},camera:{position:camera.position.toArray(),target:controls.target.toArray(),zoom:camera.zoom,fov:camera.fov,near:camera.near,far:camera.far},render:{...renderer.info.render},projectionDiagnostic:pixelsPerMmMax,png:renderer.domElement.toDataURL('image/png')};
 },
 projectionBound(){
  const size=new THREE.Vector2();renderer.getDrawingBufferSize(size);const matrix=this.mesh.matrixWorld;let maxScale=0;
  for(const y of [0,12,13,14.6])for(const x of [-14.6,0,14.6]){
   const p=new THREE.Vector3(x,y,.25).applyMatrix4(matrix);const a=p.clone().project(camera);for(const axis of [new THREE.Vector3(.0001,0,0),new THREE.Vector3(0,.0001,0),new THREE.Vector3(0,0,.0001)]){const b=p.clone().add(axis).project(camera);const scale=Math.hypot((a.x-b.x)*size.x/2,(a.y-b.y)*size.y/2)/.0001;maxScale=Math.max(maxScale,scale);}}
  return {sampledProjectionScalePxPerMm:maxScale,sampledShapeErrorBoundPx:maxScale*.000489402,scope:'Sampled projection Jacobian times sampled surface distance bound; NOT continuous silhouette certification.'};
 },
 finish(){this.mesh.geometry=this.original;this.candidate.dispose();controls.enabled=true;dirty=true;return this.status()}
};

const sourceNormalState=source.map(m=>({mesh:m,geometry:m.geometry,attribute:m.geometry.attributes.normal,array:m.geometry.attributes.normal?.array,values:m.geometry.attributes.normal?.array.slice()}));
window.matrixCacheQA={
 freeze(){for(const id of ['animate','animate-movement']){const e=$(id);e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}stopTour();cameraTween=null;dirty=true;},
 async dynamic(){const result=[];for(let i=0;i<12;i++){const r=await this.sample({cache:true,explode:i/11,finish:i%2===0,pose:i*.731,frames:3});delete r.png;if(!r.normalSourcesUnchanged||r.maxCorrectedMatrixError>2e-6)throw Error('dynamic composition mismatch');result.push(r)}return result},
 async sample({cache=true,explode=0,finish=true,pose=0,frames=2}){
  window.__matrixCacheEnabled=cache;$('finish').checked=finish;updateMaterials();visibility();renderingQuality('efficient');registerExplosionParts();explosion.setAmount(explode,{instant:true});
  clock.seek(pose,{track:'mechanism'});clock.seek(pose,{track:'hands'});applyClockPose(clock.snapshot());
  registerExplosionParts();if(explosion.active)explosion.update(0);
  const writes=window.__matrixWrites||0;let cpu=0;
  for(let i=0;i<frames;i++){
   const depth=updateInspectionDepth(camera,controls.target,depthBounds,ao);renderer.info.reset();const start=performance.now();
   mechanismBatch.build(source);try{mechanismBatch.beforeRender();composer.render();}finally{mechanismBatch.afterRender()}cpu+=performance.now()-start;
  }
  const state=mechanismBatch.snapshot(),render={...renderer.info.render};
  let checked=0;const actual=new THREE.Matrix4();for(const b of scene.children.filter(n=>n.isBatchedMesh))for(let i=0;i<b.instanceCount;i++){if(!b.getVisibleAt(i))continue;b.getMatrixAt(i,actual);checked++;}
  let maxCorrectedMatrixError=0;
  for(const e of state.entries){const mesh=source.find(m=>m.userData.sourceIndex===e.sourceIndex),row=window.__canonicalRows.find(r=>r.sourceIndex===e.sourceIndex);if(!e.lastInstanceVisible)continue;const batch=scene.children.find(b=>b.isBatchedMesh&&b.material===mesh.material),actual=new THREE.Matrix4();batch.getMatrixAt(e.instanceId,actual);const expected=new THREE.Matrix4().multiplyMatrices(mesh.matrixWorld,new THREE.Matrix4().fromArray(row.matrix));maxCorrectedMatrixError=Math.max(maxCorrectedMatrixError,...actual.elements.map((v,i)=>Math.abs(v-expected.elements[i])));}
  const normalSourcesUnchanged=sourceNormalState.every(s=>s.mesh.geometry===s.geometry&&s.geometry.attributes.normal===s.attribute&&(!s.array||s.array.every((v,i)=>v===s.values[i])));
  const png=renderer.domElement.toDataURL('image/png');dirty=false;return {normalSourcesUnchanged,maxCorrectedMatrixError,png,cache,explode,finish,pose,frames,writes:(window.__matrixWrites||0)-writes,cpuSubmissionMs:cpu/frames,state,render,checked,view:assemblyInspect()};
 }
};

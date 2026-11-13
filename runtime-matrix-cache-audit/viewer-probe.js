window.matrixCacheQA={
 freeze(){for(const id of ['animate','animate-movement']){const e=$(id);e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}stopTour();cameraTween=null;dirty=true;},
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
  const png=renderer.domElement.toDataURL('image/png');dirty=false;return {png,cache,explode,finish,pose,frames,writes:(window.__matrixWrites||0)-writes,cpuSubmissionMs:cpu/frames,state,render,checked,view:assemblyInspect()};
 }
};

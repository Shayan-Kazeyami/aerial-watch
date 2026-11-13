// QA-only module instrumentation. No source asset or rendering-quality changes.
window.normalQA={
 async auditCapture(){
  const before=currentCaptureDetail(),called={offline:0,fallback:0,provenance:0};
  const offline=frameVideo.start,fallback=recorder.start,encoder=globalThis.VideoEncoder,resolve=captureProvenance.resolve;
  try{
   frameVideo.start=async()=>{called.offline++;throw Error('QA capture intercepted');};recorder.start=async()=>{called.fallback++;throw Error('QA capture intercepted');};
   globalThis.VideoEncoder=function(){};await $('record-scene').onclick();globalThis.VideoEncoder=undefined;await $('record-scene').onclick();
   captureProvenance.resolve=async()=>{called.provenance++;throw Error('QA PNG intercepted');};await $('capture-scene').onclick();
   const wanted=before.ready?1:0;if(called.offline!==wanted||called.fallback!==wanted||called.provenance!==wanted)throw Error('Capture readiness mismatch '+JSON.stringify({before,called}));
   return {before,called,handlerGuards:true,actualEncodingTested:false};
  }finally{frameVideo.start=offline;recorder.start=fallback;globalThis.VideoEncoder=encoder;captureProvenance.resolve=resolve;}
 },
 snapshot(){return {detail:currentCaptureDetail(),state:progressiveNormalState,metrics:progressiveNormalMetrics,filtering:leatherDetails?.filtering,firstInteractiveMs:captureConfiguration().navigationTiming.firstInteractiveMs,startup:startupDiagnostics.snapshot(),crown:crownInteraction.snapshot(),hotspot:crownHotspot.snapshot(),failed,loading,quality,now:performance.now(),camera:{position:camera.position.toArray(),target:controls.target.toArray(),zoom:camera.zoom},render:{...renderer.info.render},memory:{...renderer.info.memory}};},
 async freeze(saved){resetMotion();stopTour();cameraTween=null;if(saved){camera.position.fromArray(saved.position);controls.target.fromArray(saved.target);camera.zoom=saved.zoom;camera.updateProjectionMatrix();controls.update();}dirty=true;const before=renderer.info.render.frame;await new Promise(resolve=>{function tick(){if(renderer.info.render.frame>before)resolve();else requestAnimationFrame(tick)}requestAnimationFrame(tick)});return this.snapshot();},
 frames(n=4){return new Promise(resolve=>{const tick=()=>--n<=0?resolve(this.snapshot()):requestAnimationFrame(tick);requestAnimationFrame(tick)})}
};

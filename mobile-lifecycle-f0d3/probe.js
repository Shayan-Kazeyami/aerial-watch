
window.__mobileLifecycle={
 snapshot(){const c=renderer.domElement,r=c.getBoundingClientRect(),s=$('stage').getBoundingClientRect();return {url:location.href,timeOrigin:performance.timeOrigin,buffer:[c.width,c.height],canvasCSS:[r.width,r.height],stage:[s.width,s.height],camera:{p:camera.position.toArray(),q:camera.quaternion.toArray(),target:controls.target.toArray(),zoom:camera.zoom},cameraTween:!!cameraTween,explosion:explosion.snapshot(),context:contextLost,loading,failed,backend:backendIdentity,crown:crownInteraction.snapshot(),hotspot:crownHotspot.snapshot(),clock:clock.snapshot(),qa:window.__lifecycleTrace};},
 pause(){for(const id of ['animate','animate-movement']){const e=$(id);if(e.checked){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}}stopTour();},
 capture(){renderer.info.reset();mechanismBatch?.beforeRender();try{composer.render();return {png:renderer.domElement.toDataURL('image/png'),render:{...renderer.info.render},state:this.snapshot()};}finally{mechanismBatch?.afterRender();}}
};

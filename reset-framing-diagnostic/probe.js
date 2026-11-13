
window.__resetDiag={
 pause(){for(const id of ['animate','animate-movement']){const e=$(id);if(e.checked){e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}));}}stopTour();},
 snapshot(){const r=$('stage').getBoundingClientRect(),points=watchHeadFramingPoints(model),calc=n=>perspectiveFrame(points,{position:camera.position,target:controls.target,up:camera.up,fov:camera.fov,aspect:r.width/r.height,near:n,fill:.94});return {url:location.href,timeOrigin:performance.timeOrigin,view:currentView,buffer:[renderer.domElement.width,renderer.domElement.height],stage:[r.width,r.height],camera:{p:camera.position.toArray(),q:camera.quaternion.toArray(),target:controls.target.toArray(),zoom:camera.zoom,near:camera.near,far:camera.far,fov:camera.fov,aspect:camera.aspect},tween:!!cameraTween,loading,failed,explosion:explosion.snapshot(),framingPoints:points.map(p=>p.toArray()),predictedAtCurrentNear:calc(camera.near),predictedAtFixedNear:calc(.1)};},
 capture(){mechanismBatch?.beforeRender();try{composer.render();return renderer.domElement.toDataURL('image/png');}finally{mechanismBatch?.afterRender();}}
};

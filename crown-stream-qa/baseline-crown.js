import {Quaternion,Vector3} from './vendor/three.module.js';

// One stroke timeline drives the exterior crown, winding train and setting hands.
// Only displayed increments are committed; changing mode/canceling drops pending
// input rather than silently applying it through the newly selected clutch.
export function createCrownInteraction({onChange=()=>{},onSetTime=()=>{},onPull=()=>{},onTurn=()=>{},secondsPerDegree=10,duration=0}={}){
  if(!Number.isFinite(secondsPerDegree)||secondsPerDegree<=0)throw new TypeError('Invalid crown setting ratio.');
  if(!Number.isFinite(duration)||duration<0)throw new TypeError('Invalid crown transition duration.');
  let pulled=false,degrees=0,disposed=false,from=0,target=0,elapsed=duration;
  const snapshot=()=>({pulled,degrees,mode:pulled?'setting':'winding'});
  const publish=()=>{const state=snapshot();onChange(state);return state;};
  const cancel=()=>{from=target=degrees;elapsed=duration;return snapshot();};
  const commit=value=>{const delta=value-degrees;degrees=value;if(delta){onTurn(delta,snapshot());if(pulled)onSetTime(delta*secondsPerDegree);}return publish();};
  return {snapshot,get active(){return !disposed&&elapsed<duration;},
    restore(state={pulled:false,degrees:0}){if(disposed)return snapshot();if(typeof state.pulled!=='boolean'||!Number.isFinite(state.degrees)||Math.abs(state.degrees)>3600000)throw new TypeError('Invalid saved crown state.');
      const changed=pulled!==state.pulled;pulled=state.pulled;degrees=state.degrees;cancel();if(changed)onPull(pulled);return publish();},
    setPulled(value){if(disposed)return snapshot();const next=!!value;if(next!==pulled){cancel();pulled=next;onPull(pulled);}return publish();},
    turn(delta){if(disposed)return snapshot();if(!Number.isFinite(delta)||!Number.isFinite(target+delta))throw new TypeError('Crown turn must be finite.');
      if(!delta)return snapshot();
      // Reverse immediately from the pose on screen, not an unrendered endpoint.
      if((target-degrees)*delta<0)target=degrees;
      from=degrees;target+=delta;elapsed=0;
      if(duration===0)return commit(target);
      return snapshot();},
    update(delta){if(!Number.isFinite(delta)||delta<0)throw new TypeError('Invalid crown frame delta.');if(disposed||elapsed>=duration)return false;
      elapsed=Math.min(duration,elapsed+delta);const t=elapsed/duration,k=t*t*(3-2*t);commit(from+(target-from)*k);return true;},
    finish(){if(disposed)return snapshot();elapsed=duration;return commit(target);},
    cancel(){if(disposed)return snapshot();cancel();return publish();},
    setDuration(value){if(!Number.isFinite(value)||value<0)throw new TypeError('Invalid crown transition duration.');if(disposed)return snapshot();const endpoint=target;duration=value;elapsed=duration;return commit(endpoint);},
    reset(){if(disposed)return snapshot();cancel();if(pulled){pulled=false;onPull(false);}degrees=0;cancel();return publish();},
    dispose(){cancel();disposed=true;},
  };
}


// Presentation interpolation only; mechanical state stays authoritative.
export function createCrownTween({duration=.24}={}){
 if(!Number.isFinite(duration)||duration<0)throw new TypeError('Invalid crown transition duration.');
 let current={pull:0,degrees:0},from={...current},target={...current},elapsed=duration,initialized=false;
 const snapshot=()=>({...current});
 return {snapshot,get active(){return elapsed<duration;},
  target(state,{instant=false}={}){if(typeof state.pulled!=='boolean'||!Number.isFinite(state.degrees))throw new TypeError('Invalid crown visual state.');const next={pull:state.pulled?1:0,degrees:state.degrees};
   if(!initialized||instant||duration===0){current={...next};target={...next};elapsed=duration;initialized=true;return snapshot();}
   if(next.pull!==target.pull||next.degrees!==target.degrees){from={...current};target=next;elapsed=0;}return snapshot();},
  update(delta){if(!Number.isFinite(delta)||delta<0)throw new TypeError('Invalid crown frame delta.');if(elapsed>=duration)return false;elapsed=Math.min(duration,elapsed+delta);const t=elapsed/duration,k=t*t*(3-2*t);current={pull:from.pull+(target.pull-from.pull)*k,degrees:from.degrees+(target.degrees-from.degrees)*k};return true;},
  finish(){current={...target};elapsed=duration;return snapshot();}
 };
}

// Display-only compact fit: actual unchanged CAD remains available on disable.
export const COMPACT_CROWN_LAYOUT=Object.freeze({inward:1.70,fixedInterfaceX:19.9,sourceStemEndX:24.93000030517578,
  displayStemEndX:23.23000030517578,sourceTubeEndX:22.400000122375985,displayTubeEndX:20.700000122375985});
function compactOuterGeometry(mesh,endX,targetX) {
  mesh.updateWorldMatrix(true,false);const geometry=mesh.geometry.clone(),points=geometry.attributes.position;
  const inverse=mesh.matrixWorld.clone().invert(),point=new Vector3(),fixed=COMPACT_CROWN_LAYOUT.fixedInterfaceX;
  for(let i=0;i<points.count;i++) {
    point.fromBufferAttribute(points,i).applyMatrix4(mesh.matrixWorld);
    if(point.x<=fixed)continue;
    point.x=fixed+(point.x-fixed)*(targetX-fixed)/(endX-fixed);
    point.applyMatrix4(inverse);points.setXYZ(i,point.x,point.y,point.z);
  }
  points.needsUpdate=true;geometry.computeVertexNormals();geometry.computeBoundingBox();geometry.computeBoundingSphere();return geometry;
}
export function createCrownVisual(mesh,{pullDistance=.95,compact=false,stem,tube,duration=0,pullDuration=duration}={}){
  if(compact&&(!stem||!tube))throw new TypeError('Compact crown requires its source stem and crown tube.');
  const position=mesh.position.clone(),quaternion=mesh.quaternion.clone(),axis=new Vector3(1,0,0),turn=new Quaternion();let disposed=false,enabled=compact,lastState={pulled:false,degrees:0};
  // Winding/setting own stem rotation; this helper owns only its displayed axial
  // travel. Capture the seated local coordinate, never accumulate a correction
  // onto the mechanical endpoint (which is reapplied on every clock pose).
  const stemRestX=stem?.position.x;
  const variants=[];
  if(compact)for(const [part,end,target] of [[stem,COMPACT_CROWN_LAYOUT.sourceStemEndX,COMPACT_CROWN_LAYOUT.displayStemEndX],
    [tube,COMPACT_CROWN_LAYOUT.sourceTubeEndX,COMPACT_CROWN_LAYOUT.displayTubeEndX]]) {
    if(part)variants.push({mesh:part,original:part.geometry,compact:compactOuterGeometry(part,end,target)});
  }
  const tween=createCrownTween({duration});
  let pullTween=createCrownTween({duration:pullDuration}),awaitingPullFrame=false;
  // Axial travel is independent of the shared mechanical rotation phase.
  // Degree updates must neither ease twice nor restart a pull transition.
  const render=()=>{const {degrees}=tween.snapshot(),{pull}=pullTween.snapshot();
    for(const part of variants)part.mesh.geometry=enabled?part.compact:part.original;
    if(stem){stem.position.x=stemRestX+pull*pullDistance;stem.updateMatrixWorld(true);}
    mesh.position.copy(position);mesh.position.x+=pull*pullDistance-(enabled?COMPACT_CROWN_LAYOUT.inward:0);
    mesh.quaternion.copy(quaternion).multiply(turn.setFromAxisAngle(axis,degrees*Math.PI/180));mesh.updateMatrixWorld(true);};
  const apply=state=>{if(disposed)return;const pullChanged=state.pulled!==lastState.pulled;lastState={pulled:state.pulled,degrees:state.degrees};tween.target({pulled:false,degrees:lastState.degrees});pullTween.target({pulled:lastState.pulled,degrees:0});if(pullChanged&&pullTween.active)awaitingPullFrame=true;render();};
  return {apply,get active(){return !disposed&&(tween.active||pullTween.active);},get pullActive(){return !disposed&&pullTween.active;},
    update(delta){if(disposed)return false;const rotationChanged=tween.update(delta);
      // A frame delta may predate the user's click or contain a renderer stall.
      // Start axial presentation on its first submitted frame and retain at least
      // two intermediate poses. Only this cosmetic travel stretches at low FPS;
      // the watch clock, shared rotation strokes and gear ratios are untouched.
      const pullDelta=awaitingPullFrame?0:Math.min(delta,pullDuration/3);awaitingPullFrame=false;
      const pullChanged=pullTween.update(pullDelta),changed=rotationChanged||pullChanged;if(changed)render();return changed;},
    finish(){if(!disposed){tween.finish();pullTween.finish();awaitingPullFrame=false;render();}},
    setPullDuration(value){const next=createCrownTween({duration:value});if(disposed)return;next.target({pulled:lastState.pulled,degrees:0});pullTween=next;pullDuration=value;awaitingPullFrame=false;render();},
    setEnabled(value){enabled=compact&&!!value;apply(lastState);},
    dispose(){if(disposed)return;disposed=true;for(const part of variants){part.mesh.geometry=part.original;part.compact.dispose();}if(stem){stem.position.x=stemRestX;stem.updateMatrixWorld(true);}mesh.position.copy(position);mesh.quaternion.copy(quaternion);mesh.updateMatrixWorld(true);},
  };
}

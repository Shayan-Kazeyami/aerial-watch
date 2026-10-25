import {Quaternion,Vector3} from './vendor/three.module.js';

// UI state only. Seated turns are a visual winding gesture; no stored-energy,
// force or torque model is implied. Pulling/pushing never changes watch time.
export function createCrownInteraction({onChange=()=>{},onSetTime=()=>{},onPull=()=>{}}={}){
  let pulled=false,degrees=0,disposed=false;
  const snapshot=()=>({pulled,degrees,mode:pulled?'setting':'winding'});
  const publish=()=>{const state=snapshot();onChange(state);return state;};
  return {snapshot,
    restore(state={pulled:false,degrees:0}){if(disposed)return snapshot();if(typeof state.pulled!=='boolean'||!Number.isFinite(state.degrees)||Math.abs(state.degrees)>3600000)throw new TypeError('Invalid saved crown state.');
      const changed=pulled!==state.pulled;pulled=state.pulled;degrees=state.degrees;if(changed)onPull(pulled);return publish();},
    setPulled(value){if(disposed)return snapshot();const next=!!value;if(next!==pulled){pulled=next;onPull(pulled);}return publish();},
    turn(delta){if(disposed)return snapshot();if(!Number.isFinite(delta))throw new TypeError('Crown turn must be finite.');
      degrees+=delta;if(pulled)onSetTime(delta*10);return publish();},
    reset(){if(disposed)return snapshot();if(pulled){pulled=false;onPull(false);}degrees=0;return publish();},
    dispose(){disposed=true;},
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
export function createCrownVisual(mesh,{pullDistance=.95,compact=false,stem,tube}={}){
  if(compact&&(!stem||!tube))throw new TypeError('Compact crown requires its source stem and crown tube.');
  const position=mesh.position.clone(),quaternion=mesh.quaternion.clone(),axis=new Vector3(1,0,0),turn=new Quaternion();let disposed=false,enabled=compact,lastState={pulled:false,degrees:0};
  const variants=[];
  if(compact)for(const [part,end,target] of [[stem,COMPACT_CROWN_LAYOUT.sourceStemEndX,COMPACT_CROWN_LAYOUT.displayStemEndX],
    [tube,COMPACT_CROWN_LAYOUT.sourceTubeEndX,COMPACT_CROWN_LAYOUT.displayTubeEndX]]) {
    if(part)variants.push({mesh:part,original:part.geometry,compact:compactOuterGeometry(part,end,target)});
  }
  const apply=({pulled,degrees})=>{if(disposed)return;lastState={pulled,degrees};
      for(const part of variants)part.mesh.geometry=enabled?part.compact:part.original;
      mesh.position.copy(position);mesh.position.x+=(pulled?pullDistance:0)-(enabled?COMPACT_CROWN_LAYOUT.inward:0);
      mesh.quaternion.copy(quaternion).multiply(turn.setFromAxisAngle(axis,degrees*Math.PI/180));mesh.updateMatrixWorld(true);};
  return {apply,
    setEnabled(value){enabled=compact&&!!value;apply(lastState);},
    dispose(){if(disposed)return;disposed=true;for(const part of variants){part.mesh.geometry=part.original;part.compact.dispose();}mesh.position.copy(position);mesh.quaternion.copy(quaternion);mesh.updateMatrixWorld(true);},
  };
}

import {Quaternion,Vector3} from './vendor/three.module.js';
const tau=2*Math.PI,axis=new Vector3(0,1,0),rates=new Map([[139,-1/3600],[144,.375/3600],[145,.375/3600],[146,-1/43200],[150,1/19200],[151,1/19200],[152,-1/42240],[147,1/86400],[153,1/86400],[154,1/86400]]);
// The circular139/140 friction interface permits manual139 displacement while
//140 and its toothed109 driver retain their running pose. See R09 setting audit.
export function createAssemblySetting(motion){
  const fail=m=>{throw Error(`Assembly setting: ${m}`);};if(!Array.isArray(motion?.entries))fail('motion entries required');
  const entries=[...rates].map(([id,rate])=>{const e=motion.entries.find(e=>e.mesh.userData.sourceIndex===id);if(!e||e.kind!=='wheel'||Math.abs(e.rate-rate)>1e-15||!e.pivot?.isVector3||!e.basePosition?.isVector3||!e.baseQuaternion?.isQuaternion||![e.phase,...e.pivot.toArray(),...e.basePosition.toArray(),...e.baseQuaternion.toArray()].every(Number.isFinite))fail(`unsupported source${id}`);return{entry:e,position:e.mesh.position.clone(),quaternion:e.mesh.quaternion.clone()};});let disposed=false;
  const live=()=>{if(disposed)fail('helper disposed');};
  function apply(settingSeconds,commonTrainTime){live();if(!Number.isFinite(settingSeconds)||!Number.isFinite(commonTrainTime)||Math.abs(settingSeconds)>1e12||Math.abs(commonTrainTime)>1e12)fail('finite bounded seconds required');const rotation=new Quaternion();for(const{entry:e}of entries){const angle=e.phase+tau*(((commonTrainTime*e.rate)%1)+((settingSeconds*e.rate)%1));rotation.setFromAxisAngle(axis,angle);e.mesh.position.copy(e.basePosition).sub(e.pivot).applyQuaternion(rotation).add(e.pivot);e.mesh.quaternion.copy(rotation).multiply(e.baseQuaternion);}return{settingSeconds,commonTrainTime};}
  function reset(){live();for(const e of entries){e.entry.mesh.position.copy(e.position);e.entry.mesh.quaternion.copy(e.quaternion);}}
  return{apply,reset,dispose(){if(disposed)return;reset();disposed=true;},indices:[...rates.keys()]};
}

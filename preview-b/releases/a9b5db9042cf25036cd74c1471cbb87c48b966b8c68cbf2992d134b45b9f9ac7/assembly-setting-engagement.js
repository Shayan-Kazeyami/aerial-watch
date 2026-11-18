import {Quaternion,Vector3,BufferGeometry,BufferAttribute} from './vendor/three.module.js';
import {settingCarrierR09Data} from './assembly-setting-carrier-r09-data.js';
import {settingEngagementData as calibration} from './assembly-setting-engagement-data.js';
const DEG=Math.PI/180,TAU=2*Math.PI,X=new Vector3(1,0,0),Y=new Vector3(0,1,0);
const manifest=new Map([[51,['OM10-00242',7342]],[52,['OM10-00225',3862]],[56,['OM10-00232',2338]],[57,['OM10-00222',1514]],[58,['OM10-00238',1118]],[59,['OM10-00234',900]],[60,['OM10-00236',948]],[61,['OM10-00237',1160]],[62,['OM10-00231',1300]],[63,['OM10-00229',8664]],[64,['OM10-00233',2378]],[65,['OM10-00230',6050]],[67,['OM10-00228',4458]]]);
const wrap30=value=>((value+15)%30+30)%30-15;
// Reversible, source-derived display endpoints. Lead-in indexes the free crown
// within one input-tooth pitch while the hand clock remains unchanged.
export function createAssemblySettingEngagement(sourceMeshes,motion,winding,{data=calibration,sourceSha256}={}) {
  const fail=message=>{throw Error(`Assembly setting engagement: ${message}`);};
  if(sourceSha256!==undefined&&sourceSha256!==calibration.sourceSha256)fail('source hash mismatch');
  if(JSON.stringify(data)!==JSON.stringify(calibration)||data.version!==1)fail('unsupported calibration');
  if(!Array.isArray(sourceMeshes)||sourceMeshes.length!==166||!Array.isArray(motion?.entries)||!winding?.entries)fail('native sources and motion/winding owners required');
  const byId=new Map(sourceMeshes.map(mesh=>[mesh?.userData?.sourceIndex,mesh]));if(byId.size!==166)fail('source identities must be unique');
  const records=new Map();
  for(const[id,[name,count]]of manifest){
    const mesh=byId.get(id),owner=winding.entries.get(id),position=owner?.position||mesh?.position,quaternion=owner?.quaternion||mesh?.quaternion;
    if(mesh?.userData?.partNumber!==name||mesh.geometry?.attributes?.position?.count!==count||!position?.isVector3||!quaternion?.isQuaternion||![...position.toArray(),...quaternion.toArray()].every(Number.isFinite)||!mesh.scale.equals(new Vector3(1,1,1)))fail(`source${id} calibration mismatch`);
    records.set(id,{mesh,position:position.clone(),quaternion:quaternion.clone(),restorePosition:mesh.position.clone(),restoreQuaternion:mesh.quaternion.clone(),restoreGeometry:mesh.geometry});
  }
  const minute=motion.entries.find(entry=>entry.mesh===byId.get(145));
  if(!minute||minute.kind!=='wheel'||Math.abs(minute.rate-1/9600)>1e-15)fail('calibrated minute-wheel owner required');
  const original59=winding.entries.get(59)?.originalGeometry,original61=records.get(61).mesh.geometry;
  if(!original59?.isBufferGeometry)fail('winding canonical spring59 geometry API required');
  const original56=records.get(56).mesh.geometry,private56Seated=original56.clone(),private56Pulled=original56.clone(),private59=original59.clone(),private61=original61.clone();if(settingCarrierR09Data.sourceSha256!==data.sourceSha256||settingCarrierR09Data.sourceIndex!==62)fail('carrier proposal mismatch');const private62=new BufferGeometry();private62.setAttribute('position',new BufferAttribute(new Float32Array(settingCarrierR09Data.positions),3));private62.setAttribute('normal',new BufferAttribute(new Float32Array(settingCarrierR09Data.normals),3));private62.setIndex(new BufferAttribute(new Uint32Array(settingCarrierR09Data.indices),1));private62.computeBoundingBox();private62.computeBoundingSphere();
  const deform=(id,original,derived,mutate)=>{
    const r=records.get(id),source=original.attributes.position,target=derived.attributes.position,p=new Vector3(),inverse=r.quaternion.clone().invert();
    for(let i=0;i<source.count;i++){p.fromBufferAttribute(source,i).applyQuaternion(r.quaternion).add(r.position);mutate(p);p.sub(r.position).applyQuaternion(inverse);target.setXYZ(i,p.x,p.y,p.z);}
    target.needsUpdate=true;derived.computeVertexNormals();derived.computeBoundingBox();derived.computeBoundingSphere();
  };
  const detentWeight=p=>{const a=Math.max(0,Math.min(1,(p.z+4.75)/.95)),b=Math.max(0,Math.min(1,(p.x-11.4)/1.1));return a*a*(3-2*a)*b*b*(3-2*b);};deform(56,original56,private56Seated,p=>{p.z+=data.detent56SeatedTip*detentWeight(p);});deform(56,original56,private56Pulled,p=>{p.z+=data.detent56PulledTip*detentWeight(p);});
  const rows=data.spring59Rows,f=Math.max(0,Math.min(rows.length-1,(rows[0][0]-data.slidingShift)/(rows[0][0]-rows.at(-1)[0])*(rows.length-1))),i=Math.floor(f),spring59Tip=Math.min(rows[i][1],rows[Math.min(i+1,rows.length-1)][1]);
  deform(59,original59,private59,p=>{const u=Math.max(0,Math.min(1,(p.z+5.15)/2.1));p.x+=spring59Tip*u*u*(3-2*u);});
  deform(61,original61,private61,p=>{const u=Math.max(0,Math.min(1,(13-p.x)/3.5));p.z+=data.spring61Tip*u*u*(3-2*u);});
  const carrierPivot=new Vector3(...data.carrierPivot),carrierTarget=new Vector3(...data.target),compoundPivot=records.get(63).position.clone();let disposed=false;
  const live=()=>{if(disposed)fail('helper disposed');};
  const pose=(id,angle,axis,pivot)=>{const r=records.get(id),q=new Quaternion().setFromAxisAngle(axis,angle%TAU);r.mesh.position.copy(r.position).sub(pivot).applyQuaternion(q).add(pivot);r.mesh.quaternion.copy(q).multiply(r.quaternion);};
  const restoreUnshared=()=>{for(const id of[57,60,61,62,63,64,65,67]){const r=records.get(id);r.mesh.position.copy(r.position);r.mesh.quaternion.copy(r.quaternion);}records.get(61).mesh.geometry=original61;};
  function apply({pulled=false,settingSeconds=0,commonTrainTime=0,inputDegrees=0}={}) {
    live();if(typeof pulled!=='boolean'||![settingSeconds,commonTrainTime,inputDegrees].every(value=>Number.isFinite(value)&&Math.abs(value)<=1e12))fail('finite bounded clocks and input degrees required');
    if(!pulled){restoreUnshared();records.get(56).mesh.geometry=private56Seated;records.get(62).mesh.geometry=private62;return{ready:false,leadInStemDegrees:0,source52Pull:0};}
    // Reduce each operand before combining to avoid cancellation of large clocks.
    const leadInStemDegrees=wrap30(data.leadConstantRadians/DEG-.15*((commonTrainTime%200)+(settingSeconds%200))-(inputDegrees%30));
    const stem=(inputDegrees%360+leadInStemDegrees)*DEG,gear67=data.facePhase-.8*(inputDegrees%450+leadInStemDegrees)*DEG,compound=data.carrierAngle+data.compoundCorrection+.6*(inputDegrees%600+leadInStemDegrees)*DEG;
    pose(52,stem,X,records.get(52).position);records.get(52).mesh.position.x+=data.stemPull;
    pose(51,stem,X,records.get(51).position);records.get(51).mesh.position.x+=data.slidingShift;
    pose(57,data.tiretteAngle,Y,new Vector3(...data.tirettePivot));
    pose(58,data.forkAngle,Y,new Vector3(...data.forkPivot));pose(60,data.lever60Angle,Y,new Vector3(...data.lever60Pivot));
    records.get(56).mesh.geometry=private56Pulled;records.get(62).mesh.geometry=private62;records.get(59).mesh.geometry=private59;records.get(61).mesh.geometry=private61;
    pose(62,data.carrierAngle,Y,carrierPivot);pose(67,gear67,Y,carrierPivot);
    const q=new Quaternion().setFromAxisAngle(Y,compound%TAU);
    for(const id of[63,64,65]){const r=records.get(id);r.mesh.position.copy(r.position).sub(compoundPivot).applyQuaternion(q).add(carrierTarget);r.mesh.quaternion.copy(q).multiply(r.quaternion);}
    return{ready:true,leadInStemDegrees,source52Pull:data.stemPull,slidingShift:data.slidingShift,compoundRadians:compound,gear67Radians:gear67,spring59Tip};
  }
  function reset(){live();for(const r of records.values()){r.mesh.position.copy(r.restorePosition);r.mesh.quaternion.copy(r.restoreQuaternion);r.mesh.geometry=r.restoreGeometry;}}
  return{apply,reset,dispose(){if(disposed)return;reset();private59.dispose();private61.dispose();private56Seated.dispose();private56Pulled.dispose();private62.dispose();disposed=true;},calibration:data,records,limits:{leadDegrees:15,scope:data.scope}};
}



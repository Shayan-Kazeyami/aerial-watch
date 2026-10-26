import {Quaternion,Vector3} from './vendor/three.module.js';
import {escapementData} from './assembly-escapement-data.js';
import {contactR09Data} from './assembly-contact-r09-data.js';

const TAU=2*Math.PI,DEG=Math.PI/180,AXIS=new Vector3(0,1,0);
const SOURCE_SHA='40aadf5b8e6ed73fa0553b46873f68438d023674035b0bffb04afba569f31e99';
const fail=message=>{throw new Error(`Assembly escapement: ${message}`);};
const near=(a,b)=>Number.isFinite(a)&&Math.abs(a-b)<1e-10;
function rational(value){
  let x=Math.abs(value),h0=0,h1=1,k0=1,k1=0;
  for(let i=0;i<24;i++){
    const a=Math.floor(x),h=a*h1+h0,k=a*k1+k0;
    if(k>1e9)break;
    if(Math.abs(h/k-Math.abs(value))<1e-15)return [Math.sign(value)*h,k];
    [h0,h1,k0,k1]=[h1,h,k1,k];x=1/(x-a);
  }
  fail('unsupported wheel rate');
}

// Reversible visual reconstruction, not a loaded-contact or force solver.
// Construction only validates/copies data. The caller retains motion ownership.
export function createAssemblyEscapement(motion,{data=escapementData,contactData=contactR09Data,sourceSha256}={}){
  if(!motion||typeof motion.apply!=='function'||typeof motion.reset!=='function'||!Array.isArray(motion.entries))fail('motion API required');
  if(sourceSha256!==undefined&&sourceSha256!==SOURCE_SHA)fail('source hash mismatch');
  if(!data||data.version!==1||data.sourceSha256!==SOURCE_SHA||data.balanceHz!==3.5||data.amplitudeDegrees!==210||data.periodWheelDegrees!==18||data.insetDegrees!==.02||!Array.isArray(data.banks)||data.banks.length!==2||data.banks[0]!==-6.5||data.banks[1]!==6)fail('unsupported path calibration');
  if(!Array.isArray(data.entries)||data.entries.length!==35||data.entries.length!==motion.entries.length||!Array.isArray(data.path)||data.path.length!==253)fail('malformed path or entry manifest');
  // Only this reviewed revision is supported. Overrides permit integrity tests,
  // not silently substituting a different, unvalidated geometric trajectory.
  if(JSON.stringify(data.entries)!==JSON.stringify(escapementData.entries)||JSON.stringify(data.path)!==JSON.stringify(escapementData.path))fail('unreviewed path or manifest');
  const records=[],byEntry=new Map(),ids=new Set();
  for(let i=0;i<motion.entries.length;i++){
    const e=motion.entries[i],row=data.entries[i],id=e?.mesh?.userData?.sourceIndex;
    if(!Array.isArray(row)||row.length!==7||id!==row[0]||ids.has(id)||e.kind!==row[1]||(e.rate??null)!==row[2]||!near(e.phase,row[3])||!e.pivot?.isVector3||!e.basePosition?.isVector3||!e.baseQuaternion?.isQuaternion||!e.mesh.position?.isVector3||!e.mesh.quaternion?.isQuaternion)fail('entry calibration mismatch');
    if(![...e.pivot.toArray(),...e.basePosition.toArray(),...e.baseQuaternion.toArray()].every(Number.isFinite)||!e.pivot.toArray().every((n,j)=>near(n,row[4+j])))fail('invalid native pivot or transform');
    ids.add(id);
    const record={entry:e,kind:e.kind,rate:e.rate,phase:e.phase,pivot:e.pivot.clone(),position:e.basePosition.clone(),quaternion:e.baseQuaternion.clone(),ratio:e.kind==='wheel'?rational(e.rate*2/7):null};
    records.push(record);byEntry.set(e,record);
  }
  if(![99,98,111,112,113,114,115,133,134,135,136,137,138].every(id=>ids.has(id)))fail('missing source component');
  const escape=records.find(r=>r.entry.mesh.userData.sourceIndex===99);
  if(escape.kind!=='wheel'||escape.rate!==.175||!near(escape.phase,-.09648975529443908))fail('escape calibration mismatch');
  const points=data.path.map(p=>{if(!Array.isArray(p)||p.length!==2||!p.every(Number.isFinite)||p[0]<-6.5||p[0]>6)fail('malformed path node');return {alpha:p[0],theta:p[1]};});
  const turnIndex=points.findIndex(p=>p.alpha===6),closureCorrectionDegrees=points[0].theta+18-points.at(-1).theta;
  if(turnIndex<=0||turnIndex>=points.length-1||points[0].alpha!==-6.5||points.at(-1).alpha!==-6.5||Math.abs(closureCorrectionDegrees)>1e-5)fail('invalid cycle endpoints');
  points.at(-1).theta+=closureCorrectionDegrees;
  if(!contactData||JSON.stringify(contactData)!==JSON.stringify(contactR09Data))fail('unreviewed contact corridor');
  const tracks=contactData.tracks.map((track,half)=>{
    const direction=half===0?-1:1;
    return track.map((p,i)=>{
      if(!Array.isArray(p)||p.length!==3||!p.every(Number.isFinite)||p[0]<-6.5||p[0]>6||Math.abs(p[2])>210)fail('malformed contact node');
      if(i&&(p[2]-track[i-1][2])*direction<=0)fail('nonmonotonic balance corridor');
      return {alpha:p[0],theta:p[1],beta:p[2]};
    });
  });
  if(tracks[0][0].theta!==points[0].theta||tracks[0][0].alpha!==-6.5||tracks[0].at(-1).alpha!==6||tracks[1][0].alpha!==6||tracks[1].at(-1).alpha!==-6.5)fail('contact endpoint mismatch');
  tracks[1].at(-1).theta+=closureCorrectionDegrees;
  // Capture the original implementations before callers wire their own API.
  const baselineApply=motion.apply.bind(motion),baselineReset=motion.reset.bind(motion),rotation=new Quaternion();
  let disposed=false;
  const assertLive=()=>{if(disposed)fail('helper disposed');};
  function configuration(beta,half){
    const track=tracks[half],direction=half===0?-1:1;
    if((beta-track[0].beta)*direction<=0)return {...track[0],beta};
    if((beta-track.at(-1).beta)*direction>=0)return {...track.at(-1),beta};
    let lo=0,hi=track.length-1;
    while(hi-lo>1){const mid=(lo+hi)>>1;if((beta-track[mid].beta)*direction>0)lo=mid;else hi=mid;}
    const a=track[lo],b=track[hi],f=(beta-a.beta)/(b.beta-a.beta);
    return {alpha:a.alpha+(b.alpha-a.alpha)*f,theta:a.theta+(b.theta-a.theta)*f,beta};
  }
  function sample(seconds){
    assertLive();if(!Number.isFinite(seconds))fail('finite seconds required');
    const cycles=seconds*3.5,cycle=Math.floor(cycles);
    if(!Number.isSafeInteger(cycle))fail('time exceeds safe cycle range');
    const fraction=cycles-cycle,beta=210*Math.cos(TAU*fraction),half=fraction<.5?0:1,p=configuration(beta,half),localTrainTime=(p.theta*DEG-escape.phase)/(TAU*escape.rate);
    return {...p,half,cycle,fraction,localTrainTime,trainTime:cycle*2/7+localTrainTime,escapeDegrees:p.theta+cycle*18};
  }
  function angleFor(entry,state){
    assertLive();const r=byEntry.get(entry);
    if(!r||!state||!Number.isSafeInteger(state.cycle)||![state.alpha,state.beta,state.localTrainTime].every(Number.isFinite)||state.alpha<-6.5||state.alpha>6||Math.abs(state.beta)>210)fail('invalid entry or sampled state');
    if(r.kind==='pallet')return state.alpha*DEG;
    if(r.kind==='balance')return state.beta*DEG;
    if(r.kind==='spring')fail('spring uses baseline deformation');
    const [n,d]=r.ratio,cycleTurns=Number((BigInt(state.cycle)*BigInt(n))%BigInt(d))/d;
    return r.phase+TAU*(cycleTurns+state.localTrainTime*r.rate);
  }
  function apply(seconds){
    const state=sample(seconds);
    baselineApply(0,state.fraction/3.5+1/14);
    for(const r of records){
      if(r.kind==='spring')continue;
      rotation.setFromAxisAngle(AXIS,angleFor(r.entry,state));
      r.entry.mesh.position.copy(r.position).sub(r.pivot).applyQuaternion(rotation).add(r.pivot);
      r.entry.mesh.quaternion.copy(r.quaternion).premultiply(rotation);
    }
    return state;
  }
  function reset(){assertLive();baselineReset();}
  function dispose(){if(disposed)return;baselineReset();disposed=true;}
  return {apply,reset,sample,angleFor,dispose,sourceSha256:SOURCE_SHA,closureCorrectionDegrees,limits:contactR09Data.limits};
}

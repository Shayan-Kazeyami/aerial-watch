import {Quaternion,Vector3} from './vendor/three.module.js';

import {calendarCalibration} from './assembly-calendar-data.js';
const tau=2*Math.PI,axis=new Vector3(0,1,0),turn=new Quaternion();
// Native section-derived visual indexing. Spring displacement is kinematic,
// not a stress/energy solution. The original source meshes remain recoverable.
export function sampleCalendarTime(seconds){
 if(!Number.isFinite(seconds))throw Error("Calendar requires finite common train time");
 const phase=seconds*tau/86400+calendarCalibration.driverPhase,day=Math.floor(phase/tau),p=phase-day*tau;
 const rows=calendarCalibration.rows,f=p/tau*(rows.length-1),i=Math.min(rows.length-2,Math.floor(f)),u=f-i,a=rows[i],b=rows[i+1];
 const fraction=(a[0]*(1-u)+b[0]*u)/calendarCalibration.pitch;
 return {day,fraction,dateAngle:((day%31)+fraction)*calendarCalibration.pitch,jumperAngle:a[1]*(1-u)+b[1]*u,driverPhase:p};
}
export function createAssemblyCalendar(sourceMeshes){
 const byIndex=new Map(sourceMeshes.map(m=>[m.userData.sourceIndex,m]));
 const own=[149,156,148,159].map(i=>{const mesh=byIndex.get(i);if(!mesh)throw Error(`Calendar source ${i} missing`);return {mesh,index:i,position:mesh.position.clone(),quaternion:mesh.quaternion.clone(),geometry:mesh.geometry};});
 const pivot=new Vector3(calendarCalibration.jumperPivot[0],0,calendarCalibration.jumperPivot[1]);
 const springs=own.filter(e=>e.index===148||e.index===159).map(e=>{const a=e.geometry.attributes.position,p=new Vector3(),vertices=[];for(let i=0;i<a.count;i++){p.fromBufferAttribute(a,i).applyQuaternion(e.quaternion).add(e.position);const u=Math.max(0,Math.min(1,(p.z-3)/4.8));vertices.push({p:p.clone(),weight:u*u*(3-2*u)});}return {...e,vertices,privateGeometry:null};});
 const pose=(e,angle,p)=>{turn.setFromAxisAngle(axis,angle);e.mesh.position.copy(e.position).sub(p).applyQuaternion(turn).add(p);e.mesh.quaternion.copy(e.quaternion).premultiply(turn);};
 let lastLift=NaN;
 return {sourceIndices:[149,156,148,159],calibration:calendarCalibration,
 apply(seconds){const state=sampleCalendarTime(seconds);pose(own[0],state.dateAngle,new Vector3(0,own[0].position.y,0));pose(own[1],state.jumperAngle,pivot);if(state.jumperAngle!==lastLift){for(const e of springs){e.privateGeometry??=e.geometry.clone();e.mesh.geometry=e.privateGeometry;const a=e.privateGeometry.attributes.position,inverse=e.quaternion.clone().invert();turn.setFromAxisAngle(axis,state.jumperAngle);for(let i=0;i<e.vertices.length;i++){const {p,weight}=e.vertices[i],q=p.clone().sub(pivot).applyQuaternion(turn).add(pivot).lerp(p,1-weight).sub(e.position).applyQuaternion(inverse);a.setXYZ(i,q.x,q.y,q.z);}a.needsUpdate=true;e.privateGeometry.computeVertexNormals();e.privateGeometry.computeBoundingBox();e.privateGeometry.computeBoundingSphere();}lastLift=state.jumperAngle;}return state;},
 reset(){for(const e of own){e.mesh.position.copy(e.position);e.mesh.quaternion.copy(e.quaternion);e.mesh.geometry=e.geometry;}lastLift=NaN;},
 dispose(){this.reset();for(const e of springs)e.privateGeometry?.dispose();}
 };
}


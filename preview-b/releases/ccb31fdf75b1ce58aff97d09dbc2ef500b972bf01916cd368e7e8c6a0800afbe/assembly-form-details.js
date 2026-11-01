import * as THREE from './vendor/three.module.js';

// Native Z is assembly-space +Y after the CAD/glTF conversion. Keep the real
// source object: calendar motion, selection, visibility and source IDs stay put.
export function inspectCalendarCaps(mesh) {
  mesh.updateWorldMatrix(true,false);
  const g=mesh.geometry,p=g.attributes.position,index=g.index;
  const selected=[],parent=new Map(),a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),normal=new THREE.Vector3();
  const key=v=>[v.x,v.y,v.z].map(n=>Math.round(n*1e5)).join(',');
  const find=k=>{if(!parent.has(k))parent.set(k,k);let r=k;while(parent.get(r)!==r)r=parent.get(r);while(parent.get(k)!==k){const n=parent.get(k);parent.set(k,r);k=n;}return r;};
  const read=(n,v)=>v.fromBufferAttribute(p,index?index.getX(n):n).applyMatrix4(mesh.matrix);
  for(let n=0;n<(index?.count??p.count);n+=3){read(n,a);read(n+1,b);read(n+2,c);
    normal.subVectors(b,a).cross(new THREE.Vector3().subVectors(c,a)).normalize();
    if([a,b,c].every(v=>Math.abs(v.y-2.12)<1e-5)&&normal.y>.999){selected.push(n);const keys=[key(a),key(b),key(c)];for(const k of keys)find(k);for(const k of keys.slice(1))parent.set(find(k),find(keys[0]));}
  }
  return {triangleOffsets:selected,components:new Set([...parent.keys()].map(find)).size,plane:2.12,axis:'+Y'};
}

export function createFormDetails({calendar,caseMesh,candidateScene}) {
  if(calendar?.userData.sourceIndex!==149||caseMesh?.userData.assemblyId!=='CASE')throw new Error('Form details require actual source149 and CASE.');
  const audit=inspectCalendarCaps(calendar);
  if(audit.components!==53)throw new Error(`Expected 53 raised digit islands; found ${audit.components}.`);
  const cases=[];candidateScene.traverse(m=>{if(m.isMesh&&m.userData.replacesAssemblyId==='CASE')cases.push(m);});
  if(cases.length!==1)throw new Error('Expected one authored CASE replacement.');
  const originalCalendar=calendar.geometry,originalCase=caseMesh.geometry;
  let calendarGeometry,caseGeometry,ink,enabled=false,disposed=false;
  try {
    calendarGeometry=originalCalendar.clone();calendarGeometry.clearGroups();
    // Two contiguous index ranges avoid one draw call per numeral island.
    // Reorder only the private index; source coordinates and winding stay exact.
    const caps=new Set(audit.triangleOffsets),count=calendarGeometry.index?.count??calendarGeometry.attributes.position.count;
    const order=[];
    for(const cap of [false,true])for(let n=0;n<count;n+=3)if(caps.has(n)===cap)
      for(let j=0;j<3;j++)order.push(originalCalendar.index?originalCalendar.index.getX(n+j):n+j);
    calendarGeometry.setIndex(order);
    const backgroundCount=count-audit.triangleOffsets.length*3;
    calendarGeometry.addGroup(0,backgroundCount,0);
    calendarGeometry.addGroup(backgroundCount,count-backgroundCount,1);
    cases[0].updateWorldMatrix(true,false);caseMesh.updateWorldMatrix(true,false);
    caseGeometry=cases[0].geometry.clone().applyMatrix4(new THREE.Matrix4().copy(caseMesh.matrix).invert().multiply(cases[0].matrix));
    ink=new THREE.MeshStandardMaterial({color:0xe3dfcf,metalness:.05,roughness:.62});ink.name='Raised calendar numeral ivory';
  }catch(error){calendarGeometry?.dispose();caseGeometry?.dispose();ink?.dispose();throw error;}
  return {
    audit:{...audit,triangleOffsets:undefined,capTriangles:audit.triangleOffsets.length},
    get enabled(){return enabled;},
    setEnabled(value){if(disposed)return;enabled=!!value;calendar.geometry=enabled?calendarGeometry:originalCalendar;caseMesh.geometry=enabled?caseGeometry:originalCase;},
    calendarMaterial(base){if(!enabled)return base;if(Array.isArray(base))throw new Error('Calendar base must be a single material.');return [base,ink];},
    dispose(){if(disposed)return;calendar.geometry=originalCalendar;caseMesh.geometry=originalCase;enabled=false;disposed=true;calendarGeometry.dispose();caseGeometry.dispose();ink.dispose();},
  };
}


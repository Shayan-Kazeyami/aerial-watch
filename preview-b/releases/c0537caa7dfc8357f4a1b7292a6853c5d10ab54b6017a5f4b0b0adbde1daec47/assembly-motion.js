import { Quaternion, Vector3 } from './vendor/three.module.js';

const wheelGroups = [
  {name:'OM10-00148',anchor:'OM10-00149',wheel:'OM10-00150',rate:-1/3600},
  {name:'OM10-00160',anchor:'OM10-00161',wheel:'OM10-00162',rate:7.5/3600},
  {name:'OM10-00163',anchor:'OM10-00164',wheel:'OM10-00165',rate:-1/60},
  {name:'OM10-00145',anchor:'OM10-00146',wheel:'OM00-00101',rate:.175},
  {name:'OM10-00154',anchor:'OM10-00152',wheel:'OM10-00156',rate:3/3600},
  {name:'OM10-00126',anchor:'OM10-00127',wheel:'OM10-00128',rate:-1/3600,plainAxis:true},
  {name:'OM10-00157',anchor:'OM10-00158',wheel:'OM10-00159',rate:.375/3600,plainAxis:true},
  {name:'OM10-00216',anchor:'OM10-00215',wheel:'OM10-00213',rate:1/19200,boreAxis:true},
];
const balanceParts = ['OM10-00112','OM10-00113','OM10-00110','OM10-00111','OM10-00116'];
const axis = new Vector3(0,1,0), tau = 2*Math.PI;
const beatHz = 7, releaseFraction = .24, balanceAmplitude = 210*Math.PI/180;
const smoothstep = value => { const x = Math.max(0,Math.min(1,value)); return x*x*(3-2*x); };

function releaseState(seconds) {
  const beats = seconds*beatHz+releaseFraction/2, beat = Math.floor(beats);
  return {beat,progress:smoothstep((beats-beat)/releaseFraction)};
}

// Seven releases/second, with a finite impulse followed by a locked interval.
// The source pose is the middle of an impulse. Subtract that half beat so t=0
// reproduces it exactly; negative time and arbitrary seeks remain deterministic.
export function sampleMechanicalTime(seconds) {
  if (!Number.isFinite(seconds)) throw new Error('Assembly motion: animation time must be finite seconds.');
  const {beat,progress} = releaseState(seconds);
  return (beat+progress-.5)/beatHz;
}

// Kinematic reconstruction, not a contact/dynamics simulation. The native escape
// mesh has 20 tooth tips, 18 degrees apart: its documented .175 rev/s means a
// 9-degree half-tooth advance at each of the balance's seven beats/second.
// All train wheels share those impulse/lock intervals. Balance amplitude and the
// pallet's +/-6 degree bank angles are illustrative, not calibrated CAD limits.
// Source CAD (x,y,z) exports as glTF (-z,y,x); the local rotation axis stays +Y.
// The assembly's +90deg X mount makes -Y clockwise from its front, matching its hands.
// This reverses the legacy movement viewer's mount convention without changing ratios.
export function createAssemblyMotion(sourceMeshes, metadata) {
  const invalid = message => { throw new Error(`Assembly motion: ${message}`); };
  if (!metadata?.hierarchy || !Array.isArray(metadata.parts)) invalid('movement hierarchy and part metadata are required.');
  if (!Array.isArray(sourceMeshes) || sourceMeshes.length !== metadata.meshCount) invalid('source mesh count does not match movement metadata.');
  const byIndex = new Map(), byPart = new Map(), partMetadata = new Map(metadata.parts.map(part => [part.id,part]));
  for (const mesh of sourceMeshes) {
    const {sourceIndex,partNumber} = mesh.userData || {}, part = partMetadata.get(sourceIndex);
    if (!Number.isInteger(sourceIndex) || byIndex.has(sourceIndex)) invalid(`duplicate or invalid source index ${sourceIndex}.`);
    if (!part || part.name !== partNumber) invalid(`source ${sourceIndex} part number does not match movement metadata.`);
    if (!Array.isArray(part.center) || part.center.length !== 3 || !part.center.every(Number.isFinite)) invalid(`source ${sourceIndex} has no valid CAD centre.`);
    const [x,y,z] = part.center;
    if (mesh.position.distanceTo(new Vector3(-z,y,x)) > .0001) invalid(`source ${sourceIndex} position does not match the native glTF coordinate mapping.`);
    byIndex.set(sourceIndex,mesh);
    if (!byPart.has(partNumber)) byPart.set(partNumber,[]);
    byPart.get(partNumber).push(mesh);
  }
  const nodes = [];
  function visit(node) {
    if (!node || !Array.isArray(node.children) || !Array.isArray(node.meshes)) invalid('movement hierarchy is malformed.');
    nodes.push(node); node.children.forEach(visit);
  }
  visit(metadata.hierarchy);
  const findGroup = name => {
    const matches = nodes.filter(node => node.name === name);
    if (matches.length !== 1) invalid(`expected one movement hierarchy group ${name}.`);
    return matches[0];
  };
  const findPart = name => {
    const matches = byPart.get(name) || [];
    if (matches.length !== 1) invalid(`expected one movement anchor/component ${name}.`);
    return matches[0];
  };
  const entries = [], used = new Set();
  const axes = new Map();
  function fitCircle(rim) {
    const mean = rim.reduce((sum,p) => ({x:sum.x+p.x,z:sum.z+p.z,r:sum.r+p.x*p.x+p.z*p.z}),{x:0,z:0,r:0});
    mean.x/=rim.length; mean.z/=rim.length; mean.r/=rim.length;
    let xx=0,zz=0,xz=0,xr=0,zr=0;
    for (const p of rim) {
      const x=p.x-mean.x,z=p.z-mean.z,r=p.x*p.x+p.z*p.z-mean.r;
      xx+=x*x;zz+=z*z;xz+=x*z;xr+=x*r;zr+=z*r;
    }
    const determinant=xx*zz-xz*xz;
    if (rim.length<12 || determinant<1e-12) invalid('native circular axis fit is unstable.');
    const x=(xr*zz-zr*xz)/(2*determinant),z=(zr*xx-xr*xz)/(2*determinant);
    const radii=rim.map(p=>Math.hypot(p.x-x,p.z-z)),radius=radii.reduce((a,b)=>a+b)/radii.length;
    return {x,z,radius,residual:Math.max(...radii.map(r=>Math.abs(r-radius)))};
  }
  function boreAxis(mesh) {
    const position=mesh.geometry.getAttribute('position'),rim=[],point=new Vector3();
    // Calendar hubs share a 1.46 mm circular shaft/bore section. Fitting that
    // circle avoids the off-centre bounds of odd-toothed wheels and their finger.
    for(let i=0;i<position.count;i++) {
      point.fromBufferAttribute(position,i).applyQuaternion(mesh.quaternion).add(mesh.position);
      if(Math.abs(point.y-1.46)<1e-5&&Math.hypot(point.x-mesh.position.x,point.z-mesh.position.z)<.5) rim.push({x:point.x,z:point.z});
    }
    const circle=fitCircle(rim);
    if(circle.residual>1e-5) invalid(`source ${mesh.userData.sourceIndex} has an ambiguous calendar hub axis.`);
    return {pivot:new Vector3(circle.x,mesh.position.y,circle.z),residual:circle.residual};
  }
  function bearingAxis(anchor) {
    if (axes.has(anchor)) return axes.get(anchor);
    const candidates = sourceMeshes.filter(mesh => /Pierre/.test(partMetadata.get(mesh.userData.sourceIndex).description || ''))
      .map(mesh => ({mesh,distance:Math.hypot(mesh.position.x-anchor.position.x,mesh.position.z-anchor.position.z)}))
      .sort((a,b) => a.distance-b.distance);
    if (!candidates.length || candidates[0].distance>.03) invalid(`no native jewel bearing found for ${anchor.userData.partNumber}.`);
    const bearing = candidates[0].mesh, position = bearing.geometry.getAttribute('position'), points = [];
    const local = new Vector3();
    let maximum = 0;
    for (let i=0;i<position.count;i++) {
      local.fromBufferAttribute(position,i).applyQuaternion(bearing.quaternion);
      const radius = Math.hypot(local.x,local.z);
      maximum = Math.max(maximum,radius); points.push({x:local.x,z:local.z,radius});
    }
    // A first fit removes tessellated bounding-box bias; a second isolates the
    // outer circular rim from its nearby chamfer. Pinion 96's box centre is
    // displaced by .01629 mm, so a bounding-box pivot would make its shaft orbit.
    let rim=points.filter(point => maximum-point.radius<.001), centre=fitCircle(rim);
    maximum=Math.max(...rim.map(point => Math.hypot(point.x-centre.x,point.z-centre.z)));
    rim=rim.filter(point => maximum-Math.hypot(point.x-centre.x,point.z-centre.z)<.00005);
    centre=fitCircle(rim);
    const radii=rim.map(point => Math.hypot(point.x-centre.x,point.z-centre.z)), radius=radii.reduce((a,b) => a+b)/radii.length;
    const residual=Math.max(...radii.map(value => Math.abs(value-radius)));
    if (residual>.0001) invalid(`native jewel ${bearing.userData.sourceIndex} circular fit is ambiguous.`);
    const result={pivot:new Vector3(bearing.position.x+centre.x,anchor.position.y,bearing.position.z+centre.z),bearingIndex:bearing.userData.sourceIndex,radius,residual};
    axes.set(anchor,result); return result;
  }
  function add(mesh,kind,anchor,rate,plainAxis = false) {
    if (!mesh || used.has(mesh)) invalid('movement hierarchy contains missing or repeated animated meshes.');
    if (mesh.parent !== anchor.parent) invalid('animated components and their anchors must share native glTF coordinates.');
    used.add(mesh);
    const bearing=plainAxis === true ? {pivot:anchor.position,residual:0} : plainAxis || bearingAxis(anchor);
    entries.push({mesh,kind,pivot:bearing.pivot.clone(),bearingIndex:bearing.bearingIndex,axisFitResidual:bearing.residual,basePosition:mesh.position.clone(),baseQuaternion:mesh.quaternion.clone(),phase:0,...(rate === undefined ? {} : {rate})});
  }
  for (const group of wheelGroups) {
    const node = findGroup(group.name), anchor = findPart(group.anchor), wheel = findPart(group.wheel);
    if (node.meshes.length !== 2 || !node.meshes.includes(anchor.userData.sourceIndex) || !node.meshes.includes(wheel.userData.sourceIndex)) invalid(`wheel hierarchy group ${group.name} does not match its two source components.`);
    const axisReference=group.boreAxis ? boreAxis(anchor) : group.plainAxis;
    for (const index of node.meshes) add(byIndex.get(index),'wheel',anchor,group.rate,axisReference);
  }
  // The drum turns around the held arbor; the ratchet, arbor and winding train
  // remain locked while the watch runs. Its lid belongs to the rotating drum.
  const barrelLid=findPart('OM10-00119');
  add(findPart('OM10-00121'),'wheel',barrelLid,16/107/3600);
  add(barrelLid,'wheel',barrelLid,16/107/3600);
  const hour=findPart('OM10-00206');
  add(hour,'wheel',hour,-1/43200,true);
  add(findPart('OM10-00195'),'wheel',findPart('OM10-00220'),0,true);
  const dateIdler=findPart('OM10-00212'),dateDriver=findPart('OM10-00207'),dateAxis=boreAxis(dateDriver);
  add(dateIdler,'wheel',dateIdler,-1/42240,boreAxis(dateIdler));
  for(const index of findGroup('OM10-00208').meshes) add(byIndex.get(index),'wheel',dateDriver,1/86400,dateAxis);
  add(findPart('OM10-00142'),'wheel',dateDriver,1/86400,dateAxis);

  // STEP assemblies supply placement, but their arbitrary tooth phases are not
  // a meshing constraint. Measure the native tooth tips and index each rigid
  // wheel/pinion pair once. N*a + M*b then stays constant for every impulse.
  const gearEntries=new Map(entries.map(entry=>[entry.mesh.userData.sourceIndex,entry]));
  const gears=new Map();
  function gear(index,teeth,pivotIndex) {
    const mesh=byIndex.get(index), entry=gearEntries.get(index), pivot=entry?.pivot || byIndex.get(pivotIndex).position;
    const position=mesh.geometry.getAttribute('position'), points=[], local=new Vector3();
    let maximum=0;
    for(let i=0;i<position.count;i++) {
      local.fromBufferAttribute(position,i).applyQuaternion(mesh.quaternion).add(mesh.position).sub(pivot);
      const radius=Math.hypot(local.x,local.z);
      maximum=Math.max(maximum,radius); points.push({radius,angle:Math.atan2(local.z,local.x)});
    }
    const angles=[...new Set(points.filter(p=>maximum-p.radius<.015).map(p=>p.angle.toFixed(7)))].map(Number);
    const phase=Math.atan2(angles.reduce((sum,a)=>sum+Math.sin(teeth*a),0),angles.reduce((sum,a)=>sum+Math.cos(teeth*a),0))/teeth;
    gears.set(index,{index,teeth,pivot,phase,entry});
  }
  for(const [index,teeth,pivotIndex] of [[85,63,86],[75,31],[81,107],[92,16],[93,75],[94,10],
    [95,72],[96,9],[97,84],[98,8],[108,25],[109,20],[140,60],[139,18],[145,48],[144,12],[146,54],
    [150,10],[151,24],[152,22],[153,45]]) gear(index,teeth,pivotIndex);
  const rigidPairs=[[81,82],[92,93],[94,95],[96,97],[98,99],[108,109],[139,140],[144,145],[150,151],[153,154,147]];
  const contacts=[];
  for(const [driver,driven] of [[85,75],[81,92],[93,94],[95,96],[97,98],[93,108],[109,140],[139,145],[144,146],
    [146,151],[150,152],[152,153]]) {
    const a=gears.get(driver),b=gears.get(driven),line=Math.atan2(b.pivot.z-a.pivot.z,b.pivot.x-a.pivot.x);
    const sum=a.teeth*(line-a.phase+(a.entry?.phase || 0))+b.teeth*(line+Math.PI-b.phase);
    const correction=Math.atan2(Math.sin(Math.PI-sum),Math.cos(Math.PI-sum))/b.teeth;
    for(const index of rigidPairs.find(pair=>pair.includes(driven)) || [driven]) gearEntries.get(index).phase=correction;
    const rateA=a.entry?.rate || 0,rateB=b.entry.rate;
    if(Math.abs(a.teeth*rateA+b.teeth*rateB)>1e-10) invalid(`tooth ratio mismatch between sources ${driver} and ${driven}.`);
    contacts.push({driver,driven,driverTeeth:a.teeth,drivenTeeth:b.teeth,phase:correction});
  }
  const balance = findGroup('OM10-00108'), anchor = findPart('OM10-00112');
  for (const name of balanceParts) {
    const mesh = findPart(name);
    if (!balance.meshes.includes(mesh.userData.sourceIndex)) invalid(`balance hierarchy does not contain ${name}.`);
    add(mesh,'balance',anchor);
  }
  const pallet = findGroup('OM10-00103'), palletAnchor = findPart('OM10-00107');
  for (const index of pallet.meshes) add(byIndex.get(index),'pallet',palletAnchor);
  if (pallet.meshes.length !== 5) invalid('pallet hierarchy must contain its five source components.');
  const spring = findPart('OM10-00115');
  if (!balance.meshes.includes(spring.userData.sourceIndex)) invalid('balance hierarchy does not contain its hairspring.');
  add(spring,'spring',anchor);
  const springEntry = entries.at(-1), originalSpringGeometry = spring.geometry;
  const springPosition = originalSpringGeometry.getAttribute('position');
  if (!springPosition) invalid('hairspring geometry must contain positions.');
  // The supplied spiral's outer end is clocked24.56deg away from its actual
  // stud. Keeping that end motionless preserved a visible1mm disconnection.
  // Identify its small planar end cap, then align only the outer winding to
  // the retained stud. The inner end stays in its original collet slot.
  const springNormals=originalSpringGeometry.getAttribute('normal'),endNormals=new Map();
  if(!springNormals)invalid('hairspring attachment requires native surface normals.');
  for(let i=0;i<springPosition.count;i++){
    const normal=new Vector3().fromBufferAttribute(springNormals,i).applyQuaternion(springEntry.baseQuaternion);
    if(Math.abs(normal.y)>.01)continue;
    const key=normal.toArray().map(v=>v.toFixed(4)).join(',');
    if(!endNormals.has(key))endNormals.set(key,[]);endNormals.get(key).push(i);
  }
  const caps=[];
  for(const [key,indices]of endNormals){
    if(indices.length<4)continue;
    const vertices=indices.map(i=>new Vector3().fromBufferAttribute(springPosition,i).applyQuaternion(springEntry.baseQuaternion).add(springEntry.basePosition));
    const center=vertices.reduce((sum,p)=>sum.add(p),new Vector3()).divideScalar(vertices.length),radial=center.clone().sub(springEntry.pivot);radial.y=0;
    const width=2*Math.max(...vertices.map(p=>Math.hypot(p.x-center.x,p.z-center.z)));
    if(width<.15&&Math.abs(new Vector3(...key.split(',').map(Number)).dot(radial.clone().normalize()))<.5)caps.push({indices,center,radius:radial.length()});
  }
  if(caps.length!==2)invalid('expected two identifiable native hairspring attachment end caps.');
  caps.sort((a,b)=>a.radius-b.radius);const [innerCap,outerCap]=caps,stud=findPart('OM00-00130');
  const terminalTarget=stud.position.clone();terminalTarget.y=outerCap.center.y;
  const originalTerminal=outerCap.center.clone().sub(springEntry.pivot),targetTerminal=terminalTarget.clone().sub(springEntry.pivot);
  const terminalPhase=Math.atan2(originalTerminal.z*targetTerminal.x-originalTerminal.x*targetTerminal.z,originalTerminal.x*targetTerminal.x+originalTerminal.z*targetTerminal.z);
  const terminalRadiusScale=Math.hypot(targetTerminal.x,targetTerminal.z)/outerCap.radius;
  if(Math.abs(terminalPhase)>.8||Math.abs(terminalRadiusScale-1)>.01)invalid('hairspring stud alignment exceeds the native terminal envelope.');
  const springAttachments={studSourceIndex:stud.userData.sourceIndex,innerCapIndices:[...innerCap.indices],outerCapIndices:[...outerCap.indices],terminalPhase,terminalTarget:terminalTarget.toArray()};
  // The source spiral winds from about .65 to 3.11 mm around the staff. Keep its
  // entire outer terminal (>=2.85 mm) fixed and its inner collet attachment rigid.
  // A radial twist with a small pitch correction gives breathing, while retaining
  // every original triangle. This approximates spring shape, not elastic stress.
  const springVertices = [], point = new Vector3(), inverseSpringRotation = springEntry.baseQuaternion.clone().invert();
  for (let i=0;i<springPosition.count;i++) {
    point.fromBufferAttribute(springPosition,i).applyQuaternion(springEntry.baseQuaternion).add(springEntry.basePosition).sub(springEntry.pivot);
    const radius = Math.hypot(point.x,point.z), u = Math.max(0,Math.min(1,(radius-.75)/2.1));
    springVertices.push({x:point.x,y:point.y,z:point.z,weight:1-smoothstep(u),derivative:u>0&&u<1 ? -6*u*(1-u)/2.1 : 0});
  }
  let springGeometry;
  function deformSpring(angle) {
    springGeometry ??= originalSpringGeometry.clone();
    spring.geometry = springGeometry;
    const position = springGeometry.getAttribute('position');
    for (let i=0;i<springVertices.length;i++) {
      const vertex = springVertices[i];
      const twist = angle*vertex.weight+terminalPhase*(1-vertex.weight), cosine = Math.cos(twist), sine = Math.sin(twist);
      // The source coil has positive dr/d(phi), approximately .03 mm/radian.
      // Correct radius for the change in winding density to make the coil breathe.
      const radialScale = (1+(terminalRadiusScale-1)*(1-vertex.weight))/(1-(angle-terminalPhase)*vertex.derivative*.03);
      point.set((vertex.x*cosine+vertex.z*sine)*radialScale,vertex.y,(-vertex.x*sine+vertex.z*cosine)*radialScale)
        .add(springEntry.pivot).sub(springEntry.basePosition).applyQuaternion(inverseSpringRotation);
      position.setXYZ(i,point.x,point.y,point.z);
    }
    position.needsUpdate = true;
    springGeometry.computeVertexNormals();
    springGeometry.computeBoundingBox();
    springGeometry.computeBoundingSphere();
  }
  const turn = new Quaternion();
  return {
    count:entries.filter(entry=>entry.kind!=='wheel'||entry.rate!==0).length,
    poseCount:entries.length,
    entries,
    contacts,
    springAttachments,
    timing:{balanceHz:3.5,beatHz,escapeTeeth:20,releaseFraction},
    apply(trainSeconds,balanceSeconds = trainSeconds) {
      if (!Number.isFinite(trainSeconds) || !Number.isFinite(balanceSeconds)) invalid('animation time must be finite seconds.');
      const trainTime = sampleMechanicalTime(trainSeconds), balanceAngle = Math.sin(balanceSeconds*tau*3.5)*balanceAmplitude;
      const release = releaseState(balanceSeconds);
      const palletAngle = (release.beat%2 === 0 ? 1 : -1)*(2*release.progress-1)*6*Math.PI/180;
      for (const entry of entries) {
        if (entry.kind === 'spring') { deformSpring(balanceAngle); continue; }
        const angle = entry.kind === 'balance' ? balanceAngle : entry.kind === 'pallet' ? palletAngle : entry.phase+trainTime*tau*entry.rate;
        turn.setFromAxisAngle(axis,angle);
        entry.mesh.position.copy(entry.basePosition).sub(entry.pivot).applyQuaternion(turn).add(entry.pivot);
        // Rotate in the common parent frame, including any authored local orientation.
        entry.mesh.quaternion.copy(entry.baseQuaternion).premultiply(turn);
      }
    },
    reset() {
      for (const entry of entries) {
        entry.mesh.position.copy(entry.basePosition);
        entry.mesh.quaternion.copy(entry.baseQuaternion);
      }
      spring.geometry = originalSpringGeometry;
    },
  };
}

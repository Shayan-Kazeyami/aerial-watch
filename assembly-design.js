import * as THREE from './vendor/three.module.js';

export const QUALITY_HAND_STACK=Object.freeze({hour:[3.86,4.02],seconds:[3.64,3.80],minute:[4.39,4.55],secondsSleeveTop:3.68,sourceSleeveTop:4,sleeveFixedBelow:2.94});
function ring(outer,inner,bottom,depth){
  const s=new THREE.Shape();s.absarc(0,0,outer,0,Math.PI*2,false);
  const h=new THREE.Path();h.absarc(0,0,inner,0,Math.PI*2,true);s.holes.push(h);
  const g=new THREE.ExtrudeGeometry(s,{depth,bevelEnabled:false,curveSegments:64});g.translate(0,0,bottom);return g;
}
export function createFacetedHand(length,width,bottom,top,start=1.03){
  const p=[[-width*.36,start],[-width/2,Math.max(start+.3,length*.30)],[-width*.28,length*.76],[0,length],[width*.28,length*.76],[width/2,Math.max(start+.3,length*.30)],[width*.36,start]];
  const flat=p.map(v=>new THREE.Vector2(...v)),triangles=THREE.ShapeUtils.triangulateShape(flat,[]),data=[];
  const add=(a,b,c)=>data.push(...a,...b,...c),edgeZ=bottom+(top-bottom)*.35,peak=[0,(length+start)*.5,top];
  for(let i=0;i<p.length;i++){
    const j=(i+1)%p.length,a=[...p[i],edgeZ],b=[...p[j],edgeZ],c=[...p[i],bottom],d=[...p[j],bottom];
    add(a,peak,b);add(a,b,d);add(a,d,c);
  }
  for(const t of triangles)add([...p[t[2]],bottom],[...p[t[1]],bottom],[...p[t[0]],bottom]);
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(data,3));g.computeVertexNormals();return g;
}

// Display-only authored hands and a coherent R02 small-seconds stack. Its
// sleeve ends below the hour blade's entire swept plane; lifting seconds above
// the hour blade would leave that sleeve in the hour hand's path once per turn.
// Original objects remain in the authoritative assembly and keep their poses.
export function createQualityDesign(source,exterior){
  const group=new THREE.Group();group.name='Aerial quality / hand craft';
  const originals=exterior.filter(m=>['HOUR','MINUTE','SECONDS','SECONDS-STAFF'].includes(m.userData.assemblyId));
  const geometries=[],materials=[],meshes=[],pairs=[];
  const blue=new THREE.MeshPhysicalMaterial({color:0x174b82,metalness:1,roughness:.19,clearcoat:.12});
  const steel=new THREE.MeshPhysicalMaterial({color:0xc4ced5,metalness:1,roughness:.17});
  const clay=new THREE.MeshStandardMaterial({color:0x93989b,roughness:.7});materials.push(blue,steel,clay);
  function mesh(name,g,material,parent,finishKind='blued'){
    const m=new THREE.Mesh(g,material);m.name=name;m.castShadow=true;m.receiveShadow=true;
    m.userData={designPart:'QUALITY-HAND',designRevision:'Aerial Quality 01',finishKind};parent.add(m);geometries.push(g);meshes.push(m);return m;
  }
  for(const [id,length,width,bottom,top,radius,hole,hubBottom,hubTop] of [
    ['HOUR',10.6,1.18,3.86,4.02,1.26,.67,3.58,4.08],
    ['MINUTE',14.15,.78,4.39,4.55,1.02,.45,4.22,4.62],
    ['SECONDS',3.32,.24,3.64,3.80,.36,.215,3.59,3.83],
  ]){
    const original=originals.find(m=>m.userData.assemblyId===id);if(!original)continue;
    const wrapper=new THREE.Group();wrapper.position.copy(original.position);wrapper.quaternion.copy(original.quaternion);group.add(wrapper);
    const native=new THREE.Group();native.rotation.x=-Math.PI/2;wrapper.add(native);
    const start=id==='SECONDS'?.28:id==='MINUTE'?.82:1.03;
    mesh(`${id} / faceted blue blade`,createFacetedHand(length,width,bottom,top,start),blue,native);
    mesh(`${id} / bored integral hub`,ring(radius,hole,hubBottom,hubTop-hubBottom),blue,native);
    if(id!=='SECONDS')mesh(`${id} / polished arbor collar`,ring(hole+.10,hole,hubTop,.025),steel,native,'polished');
    pairs.push({original,wrapper});
  }
  const sleeve=originals.find(m=>m.userData.assemblyId==='SECONDS-STAFF');
  if(sleeve){
    const g=sleeve.geometry.clone(),p=g.attributes.position;
    const fixed=QUALITY_HAND_STACK.sleeveFixedBelow,ratio=(QUALITY_HAND_STACK.secondsSleeveTop-fixed)/(QUALITY_HAND_STACK.sourceSleeveTop-fixed);
    for(let i=0;i<p.count;i++)if(p.getY(i)>fixed)p.setY(i,fixed+(p.getY(i)-fixed)*ratio);
    p.needsUpdate=true;g.computeBoundingBox();g.computeBoundingSphere();
    g.computeVertexNormals();
    const m=mesh('Seconds sleeve / coherent R02 low stack',g,steel,group,'polished');m.position.copy(sleeve.position);m.quaternion.copy(sleeve.quaternion);
  }
  let enabled=false,finished=true,disposed=false;
  return {group,meshes,originals,count:meshes.length,
    setEnabled(value){enabled=!!value;group.visible=enabled;if(enabled)originals.forEach(m=>m.visible=false);},
    setFinish(value){finished=!!value;for(const m of meshes)m.material=finished?(m.userData.finishKind==='polished'?steel:blue):clay;},
    syncMotion(){for(const {original,wrapper}of pairs){wrapper.position.copy(original.position);wrapper.quaternion.copy(original.quaternion);}},
    dispose(){if(disposed)return;disposed=true;geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());group.removeFromParent();},
  };
}

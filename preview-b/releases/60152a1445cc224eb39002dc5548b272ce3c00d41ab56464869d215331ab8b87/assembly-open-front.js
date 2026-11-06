import * as THREE from './vendor/three.module.js';

// All authored solids are native watch XY with axial Z, in millimetres.
// The original movement supplies the central hand bearings; no dial spokes do.
export const OPEN_FRONT_LAYOUT=Object.freeze({outerRadius:16.44,innerRadius:14.6,bottom:3.25,top:3.5,
  spokeAngles:Object.freeze([]),ribs:Object.freeze([]),
  seconds:Object.freeze({x:-7.99882782395965,y:-.0162913693679177,inner:3.58,outer:4.18,
    mountingRadius:3.88,postRadius:.15,postBottom:2.19,postTop:3.27,postAngles:Object.freeze([350,110,250])}),
  signature:Object.freeze({x:0,y:13.45,calibreY:12.70})});

export function annularShape(outer,inner){
  const shape=new THREE.Shape();shape.absarc(0,0,outer,0,Math.PI*2,false);
  const hole=new THREE.Path();hole.absarc(0,0,inner,0,Math.PI*2,true);shape.holes.push(hole);return shape;
}
export function perimeterChapterShape(){
  const shape=new THREE.Shape();shape.absarc(0,0,16.44,0,Math.PI*2,false);
  // One continuous inner boundary incorporates the branding at12 into the rim.
  // A shallow scallop replaces the separate rectangular plaque/bridge.
  const points=[];
  for(let i=0;i<768;i++){
    const a=-i*Math.PI*2/768,x=Math.cos(a)*14.6;let y=Math.sin(a)*14.6;
    if(y>0)y=Math.min(y,12.15+.075*x*x);
    points.push(new THREE.Vector2(x,y));
  }
  shape.holes.push(new THREE.Path(points));return shape;
}
export function extrudedDesign(shape,depth=.25,bevel=.022){
  return new THREE.ExtrudeGeometry(shape,{depth,bevelEnabled:bevel>0,bevelSize:bevel,bevelThickness:bevel,bevelSegments:3,curveSegments:128});
}
// Enclosing -90deg X maps native (x,y,z) to glTF (x,z,-y).
export function createOpenFrontFrame(){
  const group=new THREE.Group();group.name='Aerial quality / perimeter-supported open front';group.rotation.x=-Math.PI/2;
  const graphite=new THREE.MeshPhysicalMaterial({color:0x282c2c,metalness:.76,roughness:.36});
  const clay=new THREE.MeshStandardMaterial({color:0x93989b,roughness:.7});
  const geometries=[];
  const add=(name,geometry,x,y,z,role)=>{
    const mesh=new THREE.Mesh(geometry,graphite);mesh.name=name;mesh.position.set(x,y,z);
    mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData={designPart:'QUALITY-FRAME',finishKind:'graphite',finishFaceAxis:[0,0,1],componentRole:role,designRevision:'Aerial Quality 01 / perimeter frame R03'};
    geometries.push(geometry);group.add(mesh);return mesh;
  };
  add('Graphite chapter / integrated twelve signature',extrudedDesign(perimeterChapterShape()),0,0,3.25,'Perimeter-supported chapter; original outer dial-carrier seat retained');
  const s=OPEN_FRONT_LAYOUT.seconds;
  add('Seconds / independent graphite chapter',extrudedDesign(annularShape(s.outer,s.inner)),s.x,s.y,3.25,'Separate small-seconds annulus supported from below; no centre ties');
  for(const angle of s.postAngles){
    const a=angle*Math.PI/180,x=s.x+s.mountingRadius*Math.cos(a),y=s.y+s.mountingRadius*Math.sin(a);
    const geometry=new THREE.CylinderGeometry(s.postRadius,s.postRadius,s.postTop-s.postBottom,48);
    geometry.rotateX(Math.PI/2);
    const mesh=add(`Seconds / axial mounting foot ${angle}`,geometry,x,y,(s.postTop+s.postBottom)/2,'Axial mounting proposal onto static retained plate surface at Z2.20');
    mesh.userData.mountingProposal={landingZ:2.20,postRadius:s.postRadius,angleDegrees:angle,fitStatus:'Nominal visual seat only; attachment and bearing-load review remain open'};
  }
  let disposed=false;
  return {group,count:group.children.length,setFinish(enabled){for(const mesh of group.children)mesh.material=enabled?graphite:clay;},dispose(){if(disposed)return;disposed=true;geometries.forEach(g=>g.dispose());[graphite,clay].forEach(m=>m.dispose());group.removeFromParent();}};
}

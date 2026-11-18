import * as THREE from './vendor/three.module.js';

export const FINISH_REVIEW_SAMPLES=Object.freeze([
  {kind:'satin',label:'Satin steel',note:'Directional caps · polished cut walls'},
  {kind:'polished',label:'Polished steel',note:'Tight reflected card · restrained grain'},
  {kind:'brass',label:'Warm brass',note:'Circular finish · warm wheel alloy'},
  {kind:'blued',label:'Blued steel',note:'Blue metal · faceted hand reference'},
  {kind:'ruby',label:'Ruby',note:'Opaque coloured dielectric approximation'},
  {kind:'leather',label:'Charcoal leather',note:'Matte pores · two filtered noise scales'},
].map(Object.freeze));

export const FINISH_REVIEW_CONTRACT=Object.freeze({
  version:1,units:'millimetres',couponWidth:12,couponHeight:8,couponDepth:.8,
  bevel:.06,grainAxis:Object.freeze([0,1,0]),faceAxis:Object.freeze([0,0,1]),
  heroHeight:36,macroHeight:13,exposure:1.08,environmentIntensity:.85,
});

export function createFinishReviewCoupon(){
  const width=FINISH_REVIEW_CONTRACT.couponWidth,height=FINISH_REVIEW_CONTRACT.couponHeight,radius=1;
  const x=-width/2,y=-height/2,shape=new THREE.Shape();
  shape.moveTo(x+radius,y);shape.lineTo(x+width-radius,y);shape.quadraticCurveTo(x+width,y,x+width,y+radius);
  shape.lineTo(x+width,y+height-radius);shape.quadraticCurveTo(x+width,y+height,x+width-radius,y+height);
  shape.lineTo(x+radius,y+height);shape.quadraticCurveTo(x,y+height,x,y+height-radius);
  shape.lineTo(x,y+radius);shape.quadraticCurveTo(x,y,x+radius,y);
  const geometry=new THREE.ExtrudeGeometry(shape,{depth:FINISH_REVIEW_CONTRACT.couponDepth,bevelEnabled:true,
    bevelThickness:FINISH_REVIEW_CONTRACT.bevel,bevelSize:FINISH_REVIEW_CONTRACT.bevel,bevelSegments:3,curveSegments:20,steps:1});
  geometry.translate(0,0,-FINISH_REVIEW_CONTRACT.couponDepth/2);geometry.computeBoundingBox();
  return geometry;
}

export function createFinishReviewSamples(library){
  const geometry=createFinishReviewCoupon(),group=new THREE.Group(),meshes=[];
  for(let i=0;i<FINISH_REVIEW_SAMPLES.length;i++){
    const sample=FINISH_REVIEW_SAMPLES[i],mesh=new THREE.Mesh(geometry);
    mesh.name=sample.label;mesh.userData={finishKind:sample.kind,grainAxis:[...FINISH_REVIEW_CONTRACT.grainAxis],finishFaceAxis:[...FINISH_REVIEW_CONTRACT.faceAxis]};
    mesh.material=library.apply(mesh);mesh.position.set((i%3-1)*17,i<3?7.8:-7.8,0);
    mesh.rotation.x=-.20;mesh.rotation.y=.14;mesh.castShadow=true;mesh.receiveShadow=true;
    group.add(mesh);meshes.push(mesh);
  }
  return {group,meshes,dispose(){geometry.dispose();group.removeFromParent();}};
}

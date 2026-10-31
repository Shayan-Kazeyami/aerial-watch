import * as THREE from 'three';
// All dimensions are visual-prototype millimetres. The original movement is not altered.
export const AERIAL_SPEC={caseDiameter:40.5,caseInnerDiameter:33.8,caseFront:5.75,caseBack:-5.6,strapWidth:20,stemAxis:[1,0,0],sourceToWatchAxes:['-Z','-X','Y'],smallSeconds:[-8,-.0163],status:'VISUAL PROTOTYPE — NOT MANUFACTURING CAD'};
const TAU=Math.PI*2;
export function createAerial({textures={}}={}){
 const root=new THREE.Group();root.name='AERIAL_EXTERIOR';const components=[];
 const steel=new THREE.MeshStandardMaterial({color:0xbab9b3,metalness:1,roughness:.32,roughnessMap:textures.steel||null});
 const polished=new THREE.MeshStandardMaterial({color:0xe0e0dc,metalness:1,roughness:.105});
 const silver=new THREE.MeshStandardMaterial({color:0xb7b8b1,metalness:.98,roughness:.29,roughnessMap:textures.steel||null});
 const graphite=new THREE.MeshStandardMaterial({color:0x555652,metalness:.78,roughness:.34});
 const blue=new THREE.MeshStandardMaterial({color:0x0b86be,metalness:.95,roughness:.22});
 const leather=new THREE.MeshStandardMaterial({color:textures.color?0xffffff:0x292b29,metalness:0,roughness:.94,map:textures.color||null,normalMap:textures.normal||null,roughnessMap:textures.roughness||null,normalScale:new THREE.Vector2(1.1,1.1)});
 const lining=new THREE.MeshStandardMaterial({color:0x8b7f6b,roughness:.9,normalMap:textures.normal||null,normalScale:new THREE.Vector2(.06,.06)});
 const leatherEdge=new THREE.MeshStandardMaterial({color:0x242521,roughness:.8});
 const stitch=new THREE.MeshStandardMaterial({color:0x77705f,roughness:.9});
 const crystal=new THREE.MeshPhysicalMaterial({color:0xffffff,metalness:0,roughness:.025,transmission:1,thickness:.38,ior:1.46,transparent:true,opacity:.14,depthWrite:false,side:THREE.FrontSide});
 function component(id,name,desc,explode){const group=new THREE.Group();group.name=id;group.userData={exterior:true,id,label:name,description:desc,explode,basePosition:[0,0,0],baseQuaternion:[0,0,0,1]};root.add(group);components.push(group);return group;}
 function mesh(parent,geometry,material,name){const m=new THREE.Mesh(geometry,material);m.name=name;parent.add(m);return m;}
 function lathe(parent,profile,material,name,start=0,sweep=TAU){const g=new THREE.LatheGeometry(profile.map(([r,z])=>new THREE.Vector2(r,z)),128,start,sweep);g.rotateX(Math.PI/2);return mesh(parent,g,material,name);}
 function ring(parent,inner,outer,z,depth,material,name){return lathe(parent,[[inner,z],[outer,z],[outer,z+depth],[inner,z+depth],[inner,z]],material,name);}
 function cylinder(parent,r,length,material,name,x=0,y=0,z=0,axis='z'){const g=new THREE.CylinderGeometry(r,r,length,48);if(axis==='z')g.rotateX(Math.PI/2);if(axis==='x')g.rotateZ(-Math.PI/2);const m=mesh(parent,g,material,name);m.position.set(x,y,z);return m;}
 function tube(parent,points,r,material,name){return mesh(parent,new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),Math.max(12,points.length*6),r,8,false),material,name);}
 const body=component('AER-CASE','Case & lugs','Original 40.5 mm case concept with a 33.8 mm internal opening and a stem clearance slot.',[0,0,0]);
 lathe(body,[[16.9,-4.7],[19.35,-4.7],[20.1,-4],[20.25,-3],[20.25,-1],[16.9,-1],[16.9,-4.7]],steel,'Lower case wall');
 lathe(body,[[16.9,-1],[20.25,-1],[20.25,1],[16.9,1],[16.9,-1]],steel,'Case stem clearance',Math.PI/2+.075,TAU-.15);
 lathe(body,[[16.9,1],[20.25,1],[20.25,2.7],[19.95,3.55],[18.9,3.8],[16.9,3.8],[16.9,1]],steel,'Upper case shoulder');
 for(const side of [-1,1])for(const end of [-1,1]){
  const curve=new THREE.CatmullRomCurve3([new THREE.Vector3(side*12.05,end*14.2,.75),new THREE.Vector3(side*12.35,end*17,.3),new THREE.Vector3(side*11.9,end*20.9,-.45),new THREE.Vector3(side*11.35,end*24.65,-1.25)]),pos=[],uv=[],ind=[];
  const profile=[[-.5,-.33],[-.34,-.5],[.34,-.5],[.5,-.33],[.5,.33],[.34,.5],[-.34,.5],[-.5,.33]],steps=36;
  for(let j=0;j<=steps;j++){const t=j/steps,c=curve.getPoint(t),w=3.45-1.2*t,h=4.4-1.6*t;for(let k=0;k<8;k++){pos.push(c.x+profile[k][0]*w,c.y,c.z+profile[k][1]*h);uv.push(k/8,t);}}
  for(let k=0;k<8;k++)for(let j=0;j<steps;j++){const a=j*8+k,b=j*8+(k+1)%8,c=a+8,d=b+8;if(end===1)ind.push(a,c,b,b,c,d);else ind.push(a,b,c,b,d,c);}
  const capStart=ind.length;for(const endpoint of [0,steps]){const c=curve.getPoint(endpoint/steps),center=pos.length/3;pos.push(c.x,c.y,c.z);uv.push(.5,.5);for(let k=0;k<8;k++){const a=endpoint*8+k,b=endpoint*8+(k+1)%8;if((endpoint===0)===(end===1))ind.push(center,a,b);else ind.push(center,b,a);}}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ind);for(let k=0;k<8;k++)g.addGroup(k*steps*6,steps*6,[1,0,1,0,1,0,1,0][k]);g.addGroup(capStart,ind.length-capStart,0);g.computeVertexNormals();mesh(body,g,[steel,polished],'Flowing tapered lug '+side+' '+end);
 }
 const bezel=component('AER-BEZEL','Polished bezel','Narrow stepped bezel; front opening diameter 37.2 mm.',[0,0,12]);
 lathe(bezel,[[18.65,3.65],[19.65,3.65],[20.04,3.95],[20.12,4.35],[20.08,4.75],[19.94,5.15],[19.67,5.45],[19.3,5.59],[19.15,5.61],[18.75,5.54],[18.65,5.35],[18.65,3.65]],polished,'Soft polished bezel');
 const front=component('AER-CRYSTAL','Front crystal','Transparent concept crystal above the hands; optical material is illustrative.',[0,0,29]);
 lathe(front,[[0,5.38],[18.72,5.38],[18.72,5.53],[18.3,5.66],[12,5.73],[0,5.75],[0,5.38]],crystal,'Front crystal');
 const chapter=component('AER-CHAPTER','Chapter ring & markers','Smoky chapter ring with applied batons and fine minute marks.',[0,0,19]);
 lathe(chapter,[[16.05,3.6],[18.4,3.6],[18.4,4.3],[16.05,4.3],[16.05,3.6]],graphite,'Chapter ring');
 for(let i=0;i<60;i++){const a=i*TAU/60,length=i%5===0?1.52:.45,width=i%5===0?.39:.095;const g=new THREE.BoxGeometry(width,length,i%5===0?.25:.06);const m=mesh(chapter,g,i%5===0?silver:steel,'Minute mark '+i);m.position.set(Math.sin(a)*(17.92-length/2),Math.cos(a)*(17.92-length/2),4.43);m.rotation.z=-a;}
 const frame=component('AER-FRAME','Open dial framework','Silver presentation framework adapted to the actual central spindle and seconds axis; support engineering remains conceptual.',[0,0,22]);
 ring(frame,1.55,1.95,4.12,.22,silver,'Central hand collar');
 function machinedBridge(points,width,name){const curve=new THREE.CatmullRomCurve3(points.map(([x,y])=>new THREE.Vector3(x,y,0))),left=[],right=[];for(let i=0;i<=40;i++){const t=i/40,p=curve.getPoint(t),v=curve.getTangent(t),n=new THREE.Vector2(-v.y,v.x).normalize().multiplyScalar(width/2);left.push(new THREE.Vector2(p.x+n.x,p.y+n.y));right.push(new THREE.Vector2(p.x-n.x,p.y-n.y));}const outline=[...left,...right.reverse()],shape=new THREE.Shape(outline);shape.closePath();const g=new THREE.ExtrudeGeometry(shape,{depth:.22,steps:1,bevelEnabled:true,bevelSize:.06,bevelThickness:.045,bevelSegments:2});g.translate(0,0,4.13);mesh(frame,g,silver,name);}
 ring(frame,15.1,16.05,4.05,.25,silver,'Open framework perimeter');
 const bridges=[[[[-7.7,13.2],[-5.4,11.4],[-3.5,8.05],[-1,4.6],[-.7,1.8]],1.05,'Upper balance-side bridge'],[[[8.9,12.3],[6.3,10.8],[4.5,7.5],[3.6,3.7],[1.7,.7]],1.12,'Upper right curved bridge'],[[[10.7,-10.7],[7.4,-9.1],[3.8,-6.65],[1.1,-4],[-.3,-1.8]],1.12,'Lower barrel-side bridge'],[[[-10.6,-11.0],[-9.3,-7.3],[-8.1,-4.45],[-9.1,-2.5]],.95,'Seconds-side bridge'],[[[-12.5,8.7],[-9.4,9.6],[-6.5,9.9],[-3.5,8.05]],.86,'Balance cross member']];
 bridges.push(
 [[[-3.5,8.05],[-1.1,10.0],[1.9,9.7],[4.5,7.5]],.83,'Upper arched cross bridge'],
 [[[-8.1,-4.45],[-5.7,-6.55],[-1.5,-7.7],[3.8,-6.65]],.85,'Lower curved cross bridge'],
 [[[4.5,7.5],[9.9,6.3],[11.3,2.5],[10.5,-2.6],[7.7,-5.4],[3.8,-6.65]],.9,'Train-side open web']);
 for(const [points,width,name]of bridges)machinedBridge(points,width,name);
 for(const [x,y]of [[-3.5,8.05],[3.8,-6.65],[-8.1,-4.45],[4.5,7.5]]){const collar=ring(frame,.48,1.03,4.13,.25,silver,'Framework counterbore');collar.position.set(x,y,0);
  cylinder(frame,.39,.13,polished,'Framework concept screw',x,y,4.4);
  const slot=mesh(frame,new THREE.BoxGeometry(.52,.075,.015),graphite,'Framework screw slot');slot.position.set(x,y,4.472);slot.rotation.z=.5+x*.15;}
 const seconds=component('AER-SECONDS','Small seconds ring','Small seconds at the actual OM10 seconds axis, 8 mm left of the central spindle.',[0,0,23]);
 const sx=-8,sy=-.0163;
 const secondsRing=ring(seconds,3.3,3.95,4.28,.2,graphite,'Open small seconds ring');secondsRing.position.set(sx,sy,0);
 for(let i=0;i<60;i++){const a=i*TAU/60,l=i%5===0?.42:.2;const m=mesh(seconds,new THREE.BoxGeometry(i%5===0?.11:.055,l,.04),silver,'Seconds index '+i);m.position.set(sx+Math.sin(a)*(3.72-l/2),sy+Math.cos(a)*(3.72-l/2),4.52);m.rotation.z=-a;}
 const secondsHand=component('AER-SECONDS-HAND','Seconds hand','Blue hand located on the original seconds spindle; 1 revolution/minute in the motion study.',[0,0,26]);
 const smallPivot=new THREE.Group();smallPivot.name='Aerial seconds pivot';smallPivot.position.set(sx,sy,4.72);secondsHand.add(smallPivot);const sh=mesh(smallPivot,new THREE.BoxGeometry(.16,3.1,.1),blue,'Seconds blade');sh.position.y=1.08;cylinder(smallPivot,.29,.13,polished,'Seconds cap');
 function hand(parent,length,width,z,name){const shape=new THREE.Shape();shape.moveTo(-width*.48,-1.7);shape.lineTo(-width*.65,1);shape.lineTo(-width*.4,length*.72);shape.lineTo(0,length);shape.lineTo(width*.4,length*.72);shape.lineTo(width*.65,1);shape.lineTo(width*.48,-1.7);shape.closePath();const g=new THREE.ExtrudeGeometry(shape,{depth:.11,bevelEnabled:true,bevelSize:.06,bevelThickness:.035,bevelSegments:1});const pivot=new THREE.Group();pivot.name=name+' pivot';pivot.position.z=z;parent.add(pivot);mesh(pivot,g,blue,name);return pivot;}
 const hour=component('AER-HOUR','Hour hand','Faceted blue hour hand; spindle location follows the actual CAD.',[0,0,25]);const hourPivot=hand(hour,9.4,.68,4.64,'Hour hand');hourPivot.rotation.z=THREE.MathUtils.degToRad(55);
 const minute=component('AER-MINUTE','Minute hand','Faceted blue minute hand, layered above the hour hand.',[0,0,27]);const minutePivot=hand(minute,13.7,.43,5.0,'Minute hand');minutePivot.rotation.z=THREE.MathUtils.degToRad(-60);cylinder(minutePivot,.73,.24,blue,'Central cap',0,0,.14);cylinder(minutePivot,.28,.27,polished,'Central pin',0,0,.17);
 const crown=component('AER-CROWN','Crown','Fluted crown aligned to the original winding-stem axis. Source stem remains untrimmed.',[13,0,0]);
 cylinder(crown,1.05,2.7,polished,'Crown neck',21.6,0,0,'x');
 {const pos=[],uv=[],ind=[],steps=18,slices=192;for(let j=0;j<=steps;j++){const t=j/steps,x=22.75+t*2.75,round=.14*Math.sin(Math.PI*t),radius=2.04+round;for(let k=0;k<=slices;k++){const a=k*TAU/slices,r=radius+.055*Math.cos(a*36)*Math.sin(Math.PI*t);pos.push(x,Math.sin(a)*r,Math.cos(a)*r);uv.push(k/slices,t);}}for(let j=0;j<steps;j++)for(let k=0;k<slices;k++){const a=j*(slices+1)+k,b=a+slices+1;ind.push(a,b,a+1,a+1,b,b+1);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ind);g.computeVertexNormals();mesh(crown,g,steel,'Rounded fluted crown');cylinder(crown,2.02,.15,polished,'Crown cap',25.53,0,0,'x');}
 const back=component('AER-BACK','Exhibition caseback','Separate caseback ring with a transparent central window.',[0,0,-18]);
 lathe(back,[[16.1,-5.6],[18.9,-5.6],[19.5,-5.2],[19.5,-4.7],[16.1,-4.7],[16.1,-5.6]],steel,'Caseback ring');
 for(let i=0;i<6;i++){const a=i*TAU/6;const m=cylinder(back,.55,.15,polished,'Caseback fastener '+i,Math.sin(a)*17.7,Math.cos(a)*17.7,-5.65);const slot=mesh(back,new THREE.BoxGeometry(.7,.1,.04),graphite,'Fastener slot '+i);slot.position.copy(m.position);slot.position.z-=.09;slot.rotation.z=a;}
 const backGlass=component('AER-BACK-CRYSTAL','Back crystal','Transparent exhibition window; source rear-side geometry stays intact.',[0,0,-25]);cylinder(backGlass,16.3,.3,crystal,'Back crystal',0,0,-5.27);
 const spacer=component('AER-SPACER','Movement retaining ring','Concept retaining ring with a 32.9 mm opening around the measured main plate.',[0,0,-9]);ring(spacer,16.45,16.75,-3.0,3.8,graphite,'Retaining ring');
 const Ry=30.8,Rz=25.8,theta0=Math.asin(21.2/Ry),baseCos=Math.cos(theta0);
 function strapPoint(theta,x,depth=0){const n=new THREE.Vector3(0,Rz*Math.sin(theta),Ry*Math.cos(theta)).normalize();return new THREE.Vector3(x,Ry*Math.sin(theta),Rz*(Math.cos(theta)-baseCos)-.7).addScaledVector(n,depth);}
 function strapGeometry(start,end){const pos=[],uv=[],ind=[],segs=128,cols=20,forward=end>start;for(let surface=0;surface<2;surface++)for(let j=0;j<=segs;j++){const t=j/segs,theta=start+(end-start)*t,half=10-1.55*t;for(let k=0;k<=cols;k++){const u=k/cols,x=(u*2-1)*half,dome=Math.sin(u*Math.PI)*.42,p=strapPoint(theta,x,surface?-1:1+dome);pos.push(p.x,p.y,p.z);uv.push(u*.55,t*2.35);}}const row=cols+1,layer=(segs+1)*row;const groups=[];for(let s=0;s<2;s++){const begin=ind.length;for(let j=0;j<segs;j++)for(let k=0;k<cols;k++){const a=s*layer+j*row+k,b=a+row;const outward=(s===0)===forward;if(outward)ind.push(a,a+1,b,b,a+1,b+1);else ind.push(a,b,a+1,b,b+1,a+1);}groups.push([begin,ind.length-begin,s]);}const edgeStart=ind.length;for(let j=0;j<segs;j++)for(const k of [0,cols]){const a=j*row+k,b=a+row;if((k===0)===forward)ind.push(a,b,a+layer,a+layer,b,b+layer);else ind.push(a,a+layer,b,a+layer,b+layer,b);}for(const j of [0,segs])for(let k=0;k<cols;k++){const a=j*row+k;if((j===0)===forward)ind.push(a,a+layer,a+1,a+1,a+layer,a+1+layer);else ind.push(a,a+1,a+layer,a+1,a+1+layer,a+layer);}groups.push([edgeStart,ind.length-edgeStart,2]);const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ind);for(const [start,count,material]of groups)g.addGroup(start,count,material);g.computeVertexNormals();return g;}
 for(const [id,label,start,end,side]of [['AER-STRAP-TOP','Upper leather strap',theta0,3.40,1],['AER-STRAP-BOTTOM','Lower leather strap',-theta0,-2.85,-1]]){const group=component(id,label,'Padded pebbled charcoal leather, tan inner lining, 20 mm at the lugs, tapering toward the clasp.',[0,side*18,-5]);mesh(group,strapGeometry(start,end),[leather,lining,leatherEdge],label);for(const edge of [-1,1])for(let i=1;i<81;i++){const t=i/83,ta=start+(end-start)*t,tb=start+(end-start)*(t+.005),width=10-1.55*t;const a=strapPoint(ta,edge*(width-.85),1.12),b=strapPoint(tb,edge*(width-.85),1.12);tube(group,[a.toArray(),b.toArray()],.055,stitch,'Leather stitch '+edge+' '+i);}if(side===1)for(let i=0;i<6;i++){const theta=2.72+i*.083,p=strapPoint(theta,0,1.43),m=mesh(group,new THREE.CylinderGeometry(.43,.43,.04,20),leatherEdge,'Strap adjustment hole '+i);m.position.copy(p);m.rotation.x=Math.PI/2-theta;}}
 const buckle=component('AER-BUCKLE','Buckle & keepers','Steel tang buckle and two leather keepers; visual strap fitting is conceptual.',[0,-21,-12]);
 const bt=-2.85,bc=strapPoint(bt,0,1.1),buckleGroup=new THREE.Group();buckleGroup.position.copy(bc);buckleGroup.rotation.x=-bt;buckle.add(buckleGroup);
 tube(buckleGroup,[[-9.7,-4,0],[-10.5,-3,0],[-10.5,3,0],[-9.7,4,0],[9.7,4,0],[10.5,3,0],[10.5,-3,0],[9.7,-4,0],[-9.7,-4,0]],.6,polished,'Buckle frame');tube(buckleGroup,[[0,4,.1],[0,-3.8,.4]],.3,polished,'Buckle tang');
 for(const th of [-2.48,-2.62]){const p=strapPoint(th,0,1.6),g=new THREE.BoxGeometry(20.2,2,1.7),m=mesh(buckle,g,leather,'Leather keeper');m.position.copy(p);m.rotation.x=-th;}
 const springbars=component('AER-SPRINGBARS','Spring bars','Separate strap attachment bars between the lugs.',[0,0,-7]);for(const y of [-22.4,22.4])cylinder(springbars,.55,21,steel,'Spring bar '+y,0,y,-1.1,'x');
 root.userData={design:'Aerial / concept 04',spec:AERIAL_SPEC};
 return {root,components,hands:{hour:hourPivot,minute:minutePivot,seconds:smallPivot},materials:{steel,polished,silver,graphite,blue,leather,crystal}};
}




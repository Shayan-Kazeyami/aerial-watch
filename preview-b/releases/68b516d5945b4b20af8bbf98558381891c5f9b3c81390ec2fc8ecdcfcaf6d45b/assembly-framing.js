import {Vector3} from './vendor/three.module.js';
import {assemblyExplosionOffset} from './assembly-explode.js';

// Current local geometry bounds, not source assets or world-aligned surrogate boxes.
// Endpoint union contains every intermediate linear explosion position as well.
export function visibleFramingPoints(root,{envelope=false,amount=0}={}) {
 const points=[];root.updateWorldMatrix(true,true);
 const origin=new Vector3().applyMatrix4(root.matrixWorld);
 const normal=new Vector3(0,1,0).applyMatrix4(root.matrixWorld).sub(origin);
 root.traverseVisible(mesh=>{
  if(!mesh.isMesh||!mesh.geometry)return;
  const materials=Array.isArray(mesh.material)?mesh.material:[mesh.material];
  if(!materials.some(material=>material&&material.visible!==false))return;
  const geometry=mesh.geometry;if(!geometry.boundingBox)geometry.computeBoundingBox();
  const box=geometry.boundingBox;if(!box||box.isEmpty())return;
  const offset=envelope?assemblyExplosionOffset(mesh):0;
  for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]) {
   const point=new Vector3(x,y,z).applyMatrix4(mesh.matrixWorld);
   if(envelope){point.addScaledVector(normal,-offset*amount);points.push(point,point.clone().addScaledVector(normal,offset));}
   else points.push(point);
  }
 });
 return points;
}

// Pure camera calculation: caller applies result only on explicit framing/resize.
export function perspectiveFrame(points,{position,target,up, fov,aspect,near=.1,fill=.90}) {
 if(!points.length||!(aspect>0))return null;
 const direction=position.clone().sub(target).normalize();
 const right=new Vector3().crossVectors(up,direction).normalize();
 const vertical=new Vector3().crossVectors(direction,right).normalize();
 let xmin=Infinity,xmax=-Infinity,ymin=Infinity,ymax=-Infinity;
 for(const point of points){const relative=point.clone().sub(target),x=relative.dot(right),y=relative.dot(vertical);xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);}
 const center=target.clone().addScaledVector(right,(xmin+xmax)/2).addScaledVector(vertical,(ymin+ymax)/2);
 const tangent=Math.tan(fov*Math.PI/360);let distance=near*2;
 for(const point of points){const relative=point.clone().sub(center),depth=relative.dot(direction);distance=Math.max(distance,depth+Math.max(Math.abs(relative.dot(right))/(tangent*aspect*fill),Math.abs(relative.dot(vertical))/(tangent*fill),near*2));}
 return {target:center,position:center.clone().addScaledVector(direction,distance),distance};
}

// Panel-only stage height changes must never overwrite a user/imported camera.
export function isPanelOnlyResize(previous,next,atelier=false) {
 return !!(atelier&&previous&&(previous.panelOpen||next.panelOpen)&&
  previous.viewportWidth===next.viewportWidth&&previous.viewportHeight===next.viewportHeight&&
  Math.abs(previous.width-next.width)<.5);
}

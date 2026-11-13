import {Vector3} from './vendor/three.module.js';
import {assemblyExplosionLayer} from './assembly-explode.js';
import {perspectiveFrame} from './assembly-framing.js';
export const MECHANICAL_FOCUS_IDS=Object.freeze(['plate','keyless','train','bridges','balance','calendar']);
const valid=id=>MECHANICAL_FOCUS_IDS.includes(id);
function effectiveVisible(mesh){for(let p=mesh;p;p=p.parent)if(!p.visible)return false;const materials=Array.isArray(mesh.material)?mesh.material:[mesh.material];return materials.some(m=>m&&m.visible!==false);}
// Temporary presentation only. Caller stops camera animation/controls damping
// before focus, and cancels before any other visibility/scene-ownership update.
export function createLayerFocus({root,camera,controls,getAspect=()=>camera.aspect,getFrameOptions=()=>({aspect:getAspect(),fill:.65})}={}){
 if(!root||!camera?.isPerspectiveCamera||!controls?.target)throw TypeError('Root, perspective camera and controls target required');
 let saved=null,selected=null,disposed=false;
 function capture(){
  const flags=new Map(),eligible=new Set();root.traverse(mesh=>{if(mesh.isMesh){flags.set(mesh,mesh.visible);if(effectiveVisible(mesh))eligible.add(mesh);}});
  return {flags,eligible,position:camera.position.clone(),quaternion:camera.quaternion.clone(),up:camera.up.clone(),zoom:camera.zoom,minDistance:controls.minDistance,target:controls.target.clone()};
 }
 function candidates(id,baseline){return [...baseline.eligible].filter(mesh=>assemblyExplosionLayer(mesh)?.id===id);}
 function frame(members,baseline){
  root.updateWorldMatrix(true,true);const points=[];
  for(const mesh of members){const g=mesh.geometry;if(!g)continue;if(!g.boundingBox)g.computeBoundingBox();const box=g.boundingBox;if(!box||box.isEmpty())continue;
   for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])points.push(new Vector3(x,y,z).applyMatrix4(mesh.matrixWorld));
  }
  const {aspect=camera.aspect,fill=.65,rect}=getFrameOptions();if(!Number.isFinite(aspect)||aspect<=0||!Number.isFinite(fill)||fill<=0||fill>1)return null;
  const area=rect===undefined?{left:0,top:0,right:1,bottom:1}:rect;
  if(!area||!['left','top','right','bottom'].every(k=>Number.isFinite(area[k]))||area.left<0||area.top<0||area.right>1||area.bottom>1||area.left>=area.right||area.top>=area.bottom)return null;
  const width=area.right-area.left,height=area.bottom-area.top,tangent=Math.tan(camera.fov*Math.PI/360);
  const effectiveFov=2*Math.atan(tangent*height)*180/Math.PI;
  const fitted=perspectiveFrame(points,{position:baseline.position,target:baseline.target,up:baseline.up,fov:rect===undefined?camera.fov:effectiveFov,aspect:aspect*width/height,near:camera.near,fill});
  if(!fitted)return null;
  const cx=area.left+area.right-1,cy=1-area.top-area.bottom;
  if(cx!==0||cy!==0){
   const direction=fitted.position.clone().sub(fitted.target).normalize(),right=new Vector3().crossVectors(baseline.up,direction).normalize(),up=new Vector3().crossVectors(direction,right).normalize();
   // A center-plane shift alone can clip points nearer the camera. Solve the
   // off-axis perspective inequalities at every actual 3D corner as well.
   let distance=fitted.distance;
   for(const point of points){const relative=point.clone().sub(fitted.target),z=relative.dot(direction);
    for(const [x,center,half,tan]of [[relative.dot(right),cx,width*fill,tangent*aspect],[relative.dot(up),cy,height*fill,tangent]]){
     const lo=center-half,hi=center+half;
     distance=Math.max(distance,(x/tan+hi*z)/half,(-x/tan-lo*z)/half);
    }
   }
   const shift=right.multiplyScalar(-cx*distance*tangent*aspect).addScaledVector(up,-cy*distance*tangent);
   fitted.target.add(shift);fitted.position.copy(fitted.target).addScaledVector(direction,distance);fitted.distance=distance;
  }
  if(![...fitted.position.toArray(),...fitted.target.toArray(),fitted.distance].every(Number.isFinite))return null;
  return fitted;
 }
 function restore(restoreCamera){
  if(!saved)return false;
  for(const [mesh,visible]of saved.flags)mesh.visible=visible;
  controls.minDistance=saved.minDistance;
  if(restoreCamera){camera.position.copy(saved.position);camera.quaternion.copy(saved.quaternion);camera.up.copy(saved.up);camera.zoom=saved.zoom;controls.target.copy(saved.target);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);}
  saved=null;selected=null;return true;
 }
 return {
  focus(id){
   if(disposed||!valid(id))return false;
   const baseline=saved||capture(),members=candidates(id,baseline);if(!members.length)return false;
   const fitted=frame(members,baseline);if(!fitted)return false;
   const membership=new Set(members);saved=baseline;
   for(const [mesh,visible]of saved.flags)mesh.visible=visible&&membership.has(mesh);
   controls.minDistance=.25;camera.up.copy(saved.up);camera.position.copy(fitted.position);controls.target.copy(fitted.target);camera.zoom=1;camera.lookAt(controls.target);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);selected=id;return true;
  },
  reapplyVisibility(){
   if(disposed||!saved||!selected)return false;
   const membership=new Set(candidates(selected,saved));
   for(const [mesh,visible]of saved.flags)mesh.visible=visible&&membership.has(mesh);
   return true;
  },
  reframe(){
   if(disposed||!saved||!selected)return false;
   const fitted=frame(candidates(selected,saved),saved);if(!fitted)return false;
   camera.up.copy(saved.up);camera.position.copy(fitted.position);controls.target.copy(fitted.target);camera.zoom=1;camera.lookAt(controls.target);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);return true;
  },
  restore({camera:restoreCamera=true}={}){return disposed?false:restore(restoreCamera);},
  members(id){if(disposed||!valid(id))return [];return candidates(id,saved||capture());},
  snapshot(){return {active:!!saved,selected,disposed,members:selected?candidates(selected,saved).map(mesh=>mesh.uuid):[]};},
  overview(){return disposed?false:restore(true);},
  cancel({restoreCamera=false}={}){return disposed?false:restore(restoreCamera);},
  dispose(){if(disposed)return;restore(false);disposed=true;},
 };
}

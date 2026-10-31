import {Group, Matrix4, Vector3} from './vendor/three.module.js';

/** Display-only construction layers, in glTF watch-space millimetres (+Y front).
 * The complete supplied movement remains one coherent, stationary assembly.
 */
export function assemblyExplosionOffset(object) {
  const data=object.userData||{};
  if(data.sourceIndex!==undefined||data.replacementForSourceIndex!==undefined)return 0;
  if(data.premiumFacePart)return 8;
  let id=data.replacesAssemblyId||data.assemblyId;
  if(!id&&data.designPart==='QUALITY-HAND')id=/^(HOUR|MINUTE|SECONDS)\b/i.exec(object.name)?.[1]?.toUpperCase();
  for(let parent=object.parent;!id&&parent;parent=parent.parent)id=parent.userData?.replacesAssemblyId||parent.userData?.assemblyId;
  if(id==='HOUR')return 12;
  if(id==='MINUTE')return 14;
  if(id==='SECONDS'||id==='SECONDS-STAFF')return 10;
  if(id==='FRONT-CRYSTAL')return 22;
  if(id==='BEZEL')return 18;
  if(id==='REAR-CRYSTAL')return -16;
  if(id==='CASEBACK'||/^BACK-SCREW-/.test(id||''))return -12;
  if(['DIAL','CHAPTER','DIAL-CARRIER'].includes(id)||data.designPart==='QUALITY-FRAME')return 8;
  return 0; // Case, crown, lugs, straps and buckle stay assembled together.
}

/**
 * Register attached leaf meshes, including invisible authored variants, after
 * loading. Pass root: the glTF assembly-space mount whose local +Y is the watch
 * normal (including its +PI/2 world rotation). Without root, +Y is world-space.
 * Offsets follow root scaling. Parent transforms may differ arbitrarily.
 * Call update(deltaSeconds) every frame, even after the tween finishes, so offsets
 * follow camera-independent root/parent movement. active means not reassembled
 * (including a pending tween); animating indicates a running transition only.
 * Pause illustrative mechanics while active. No mesh matrix/pose/geometry is
 * modified. Zero removes temporary wrappers and restores original child order.
 * Register late arrivals with register([...]); duplicate registration is harmless.
 * Dispose before disposing the model. Do not reparent registered meshes while
 * exploded; reset({instant:true}) first. No GPU resources are allocated here.
 */
export function createAssemblyExplosion({root=null,duration=.55}={}) {
  if(!Number.isFinite(duration)||duration<0)throw new TypeError('Invalid explosion duration.');
  const records=new Map(),inverse=new Matrix4(),worldOffset=new Vector3(),origin=new Vector3();
  let amount=0,target=0,from=0,elapsed=duration,disposed=false;
  function unwrap(record) {
    const {object,wrapper,parent}=record;
    if(!wrapper)return;
    const index=parent.children.indexOf(wrapper);
    // Do not resurrect an object explicitly removed by its owner.
    if(object.parent===wrapper){parent.add(object);if(index>=0){parent.children.splice(parent.children.indexOf(object),1);parent.children.splice(index,0,object);}}
    wrapper.removeFromParent();record.wrapper=null;
  }
  function render() {
    if(amount===0){for(const record of records.values())unwrap(record);return;}
    if(root)root.updateWorldMatrix(true,false);
    for(const record of records.values()) {
      const {object,offset}=record;
      if(offset===0)continue;
      if(!record.wrapper) {
        if(!object.parent)continue;
        const parent=object.parent,index=parent.children.indexOf(object),wrapper=new Group();
        wrapper.name='Exploded construction layer';wrapper.userData.assemblyExplosion=true;
        parent.add(wrapper);wrapper.add(object);
        parent.children.splice(parent.children.indexOf(wrapper),1);parent.children.splice(index,0,wrapper);
        record.parent=parent;record.wrapper=wrapper;
      }
      const {parent,wrapper}=record;
      parent.updateWorldMatrix(true,false);
      worldOffset.set(0,offset*amount,0);
      if(root){origin.set(0,0,0).applyMatrix4(root.matrixWorld);worldOffset.applyMatrix4(root.matrixWorld).sub(origin);}
      // Difference of points transforms a vector without normalizing its length;
      // unlike transformDirection this preserves nonuniform parent/root scales.
      if(parent.matrixWorld.determinant()===0){wrapper.position.set(0,0,0);}
      else {
        inverse.copy(parent.matrixWorld).invert();origin.set(0,0,0).applyMatrix4(inverse);
        wrapper.position.copy(worldOffset).applyMatrix4(inverse).sub(origin);
        if(!wrapper.position.toArray().every(Number.isFinite))wrapper.position.set(0,0,0);
      }
      wrapper.updateMatrix();
    }
  }
  const api={
    get amount(){return amount;},get target(){return target;},
    get active(){return !disposed&&(amount!==0||target!==0);},
    get animating(){return !disposed&&amount!==target;},
    register(objects){
      if(disposed)return api;
      for(const object of objects){if(!object?.isObject3D)throw new TypeError('Expected assembly objects.');if(!records.has(object))records.set(object,{object,offset:assemblyExplosionOffset(object),wrapper:null,parent:null});}
      render();return api;
    },
    setAmount(value,{instant=false}={}){
      if(!Number.isFinite(value))throw new TypeError('Invalid explosion amount.');
      if(disposed)return api;
      const next=Math.max(0,Math.min(1,value));
      if(instant||duration===0){amount=target=from=next;elapsed=duration;render();}
      else if(next!==target){from=amount;target=next;elapsed=0;}
      return api;
    },
    update(delta){
      if(!Number.isFinite(delta)||delta<0)throw new TypeError('Invalid explosion frame delta.');
      if(disposed)return false;
      const changed=amount!==target;
      if(changed){elapsed=Math.min(duration,elapsed+delta);const t=elapsed/duration,k=t*t*(3-2*t);amount=elapsed===duration?target:from+(target-from)*k;}
      render();return changed;
    },
    reset({instant=false}={}){return api.setAmount(0,{instant});},
    dispose(){if(disposed)return;amount=target=from=0;render();records.clear();disposed=true;},
  };
  return api;
}

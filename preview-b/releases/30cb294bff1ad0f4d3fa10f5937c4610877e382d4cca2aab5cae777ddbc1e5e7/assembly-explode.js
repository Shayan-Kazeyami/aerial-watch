import {Group, Matrix4, Vector3} from './vendor/three.module.js';

/** Display-only construction layers in glTF millimetres (+Y front).
 * Source IDs are the immutable 166-part OM10-A assembly, not spatial guesses.
 * Bearings, screws and shafts travel with their named subassembly. Gear pairs,
 * the barrel spring and the balance/hairspring retain their exact local poses.
 * This is an explanatory exploded view, not a physical disassembly simulation.
 */
export const EXPLOSION_LAYERS=Object.freeze({
  plate:Object.freeze({id:'plate',label:'Mainplate & supports',offset:8}),
  keyless:Object.freeze({id:'keyless',label:'Winding & setting',offset:-14}),
  train:Object.freeze({id:'train',label:'Barrel, gear train & escapement',offset:-6}),
  bridges:Object.freeze({id:'bridges',label:'Train & barrel bridges',offset:-29}),
  balance:Object.freeze({id:'balance',label:'Balance & hairspring',offset:-21}),
  calendar:Object.freeze({id:'calendar',label:'Motion works & calendar',offset:16}),
  dial:Object.freeze({id:'dial',label:'Dial & chapter ring',offset:24}),
  seconds:Object.freeze({id:'seconds',label:'Seconds hand',offset:28}),
  hour:Object.freeze({id:'hour',label:'Hour hand',offset:32}),
  minute:Object.freeze({id:'minute',label:'Minute hand',offset:36}),
  bezel:Object.freeze({id:'bezel',label:'Bezel',offset:41}),
  frontGlass:Object.freeze({id:'frontGlass',label:'Front crystal',offset:46}),
  cover:Object.freeze({id:'cover',label:'Rear cover',offset:-38}),
  rearGlass:Object.freeze({id:'rearGlass',label:'Rear crystal',offset:-44}),
});
const sourceLayers=Array.from({length:166},(_,id)=>
  id<=40||id>=160?'plate':id<=80?'keyless':id<=99?'train':id<=107?'bridges':id<=109?'train':
  id===110||id===116||id===117||id===118?'bridges':id<=115?'train':id<=138?'balance':
  id>=141&&id<=143?'bridges':'calendar');
export function assemblyExplosionLayer(object) {
  const data=object.userData||{},sourceId=data.sourceIndex??data.replacementForSourceIndex;
  if(sourceId!==undefined)return EXPLOSION_LAYERS[sourceLayers[sourceId]]||null;
  if(data.premiumFacePart)return EXPLOSION_LAYERS.dial;
  let id=data.replacesAssemblyId||data.assemblyId;
  if(!id&&data.designPart==='QUALITY-HAND')id=/^(HOUR|MINUTE|SECONDS)\b/i.exec(object.name)?.[1]?.toUpperCase();
  for(let parent=object.parent;!id&&parent;parent=parent.parent)id=parent.userData?.replacesAssemblyId||parent.userData?.assemblyId;
  const layer=id==='HOUR'?'hour':id==='MINUTE'?'minute':id==='SECONDS'||id==='SECONDS-STAFF'?'seconds':
    id==='FRONT-CRYSTAL'?'frontGlass':id==='BEZEL'?'bezel':id==='REAR-CRYSTAL'?'rearGlass':
    id==='CASEBACK'||/^BACK-SCREW-/.test(id||'')?'cover':
    ['DIAL','CHAPTER','DIAL-CARRIER'].includes(id)||data.designPart==='QUALITY-FRAME'?'dial':null;
  return EXPLOSION_LAYERS[layer]||null;
}
export function assemblyExplosionOffset(object) {return assemblyExplosionLayer(object)?.offset||0;}

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
  const records=new Map(),origin=new Vector3(),normal=new Vector3();
  let amount=0,target=0,from=0,elapsed=duration,disposed=false;
  function unwrap(record) {
    const {object,wrapper,parent}=record;
    if(!wrapper)return;
    const index=parent.children.indexOf(wrapper);
    // Do not resurrect an object explicitly removed by its owner.
    if(object.parent===wrapper){parent.add(object);object.matrixWorldNeedsUpdate=true;if(index>=0){parent.children.splice(parent.children.indexOf(object),1);parent.children.splice(index,0,object);}}
    wrapper.removeFromParent();record.wrapper=null;
  }
  function render() {
    if(amount===0){for(const record of records.values())unwrap(record);return;}
    if(root)root.updateWorldMatrix(true,false);
    normal.set(0,1,0);if(root){origin.set(0,0,0).applyMatrix4(root.matrixWorld);normal.applyMatrix4(root.matrixWorld).sub(origin);}
    const parentOffsets=new Map();
    for(const record of records.values()) {
      const {object,offset}=record;
      if(offset===0)continue;
      if(!record.wrapper) {
        if(!object.parent)continue;
        const parent=object.parent,index=parent.children.indexOf(object),wrapper=new Group();
        wrapper.name='Exploded · '+(record.layer?.label||'construction layer');wrapper.userData.assemblyExplosion=true;
        parent.add(wrapper);wrapper.add(object);
        parent.children.splice(parent.children.indexOf(wrapper),1);parent.children.splice(index,0,wrapper);
        record.parent=parent;record.wrapper=wrapper;
      }
      const {parent,wrapper}=record;
      // Compute each shared parent's transformed watch axis once per update.
      if(!parentOffsets.has(parent)){
        parent.updateWorldMatrix(true,false);
        const local=new Vector3();
        if(parent.matrixWorld.determinant()!==0){
          const inverse=new Matrix4().copy(parent.matrixWorld).invert();
          origin.set(0,0,0).applyMatrix4(inverse);local.copy(normal).applyMatrix4(inverse).sub(origin);
          if(!local.toArray().every(Number.isFinite))local.set(0,0,0);
        }
        parentOffsets.set(parent,local);
      }
      wrapper.position.copy(parentOffsets.get(parent)).multiplyScalar(offset*amount);
      wrapper.updateMatrix();
      object.matrixWorldNeedsUpdate=true;
    }
  }
  const api={
    get amount(){return amount;},get target(){return target;},
    get active(){return !disposed&&(amount!==0||target!==0);},
    get animating(){return !disposed&&amount!==target;},
    snapshot(){const layers=new Map();for(const {object,layer}of records.values()){if(!layer)continue;const row=layers.get(layer.id)||{...layer,parts:0,sourceParts:0};row.parts++;if(object.userData.sourceIndex!==undefined)row.sourceParts++;layers.set(layer.id,row);}return {amount,target,active:api.active,animating:api.animating,layers:[...layers.values()]};},
    register(objects){
      if(disposed)return api;
      let added=false;
      for(const object of objects){if(!object?.isObject3D)throw new TypeError('Expected assembly objects.');if(!records.has(object)){const layer=assemblyExplosionLayer(object);records.set(object,{object,layer,offset:layer?.offset||0,wrapper:null,parent:null});added=true;}}
      if(added)render();return api;
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

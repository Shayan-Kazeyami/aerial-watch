import {BufferAttribute} from "./vendor/three.module.js";
// Explicit caller opt-in; fresh/private geometry only. No disposal or field mutation.
export function compactPrivateIndex(geometry,{enabled=false}={}){
 if(enabled!==true)return {changed:false,reason:'not opted in'};
 if(!geometry?.isBufferGeometry)throw new TypeError('BufferGeometry required');
 const a=geometry.index,p=geometry.attributes.position;
 if(!a||a.itemSize!==1||a.normalized||a.isInterleavedBufferAttribute||!(a.array instanceof Uint32Array)||!p||!Number.isInteger(p.count))throw new TypeError('Private Uint32 scalar index and POSITION required');
 let max=-1;for(const v of a.array){if(v>=p.count)throw new RangeError('Index out of range');max=Math.max(max,v);}
 if(max>=65535)return {changed:false,reason:'Uint32 required',max};
 const next=new BufferAttribute(new Uint16Array(a.array),1);next.name=a.name;next.setUsage(a.usage);geometry.setIndex(next);
 return {changed:true,max,avoidedBytes:a.array.byteLength-next.array.byteLength};
}

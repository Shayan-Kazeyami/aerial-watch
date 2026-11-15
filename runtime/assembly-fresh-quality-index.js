import {BufferAttribute} from "./vendor/three.module.js";
// Fresh private construction only; caller supplies synchronous exact hash verifier.
export function indexFreshQuality(factory,{flags={},expected,hashBytes}={}){
 if(!flags||typeof flags!=='object'||Array.isArray(flags))throw new TypeError('flags object required');
 for(const key of Reflect.ownKeys(flags)){if(typeof key!=='string'||!Object.hasOwn(expected,key)||typeof flags[key]!=='boolean')throw new TypeError('Unknown or nonboolean flag');}
 for(const[key,value]of Object.entries(flags)){if(value===true&&factory.meshes.filter(m=>m.name===key).length!==1)throw Error('Target missing or duplicate');}
 const results=[],plans=[];for(const mesh of factory.meshes){if(!Object.hasOwn(flags,mesh.name)||flags[mesh.name]!==true)continue;
 const spec=expected[mesh.name],g=mesh.geometry;if(!spec||g.index!==null)throw Error('Unverified target');
 const entries=Object.entries(g.attributes);if(JSON.stringify(entries.map(([k])=>k).sort())!==JSON.stringify(Object.keys(spec.attributes).sort()))throw Error('Attribute mismatch');
 for(const[k,a]of entries){const e=spec.attributes[k];if(a.isInterleavedBufferAttribute||a.normalized!==e.normalized||a.itemSize!==e.itemSize||a.count!==e.count||a.array.constructor.name!==e.type||hashBytes(new Uint8Array(a.array.buffer,a.array.byteOffset,a.array.byteLength))!==e.hash)throw Error('Field fingerprint mismatch');}
 if(JSON.stringify(g.groups)!==JSON.stringify(spec.groups)||JSON.stringify(mesh.userData)!==JSON.stringify(spec.userData))throw Error('Target metadata mismatch');
 plans.push({mesh,g,entries,spec,originalAttributes:{...g.attributes},originalIndex:g.index});}
 const prepared=[];for(const plan of plans){const {mesh,g,entries}=plan;const count=entries[0][1].count,map=new Map(),unique=[],ids=[];
 for(let i=0;i<count;i++){let key='';for(const[k,a]of entries){const b=new Uint8Array(a.array.buffer,a.array.byteOffset+i*a.itemSize*a.array.BYTES_PER_ELEMENT,a.itemSize*a.array.BYTES_PER_ELEMENT);key+=k+':'+Array.from(b).join(',')+';';}if(!map.has(key)){map.set(key,unique.length);unique.push(i);}ids.push(map.get(key));}
 const replacements={};const before=entries.reduce((s,[,a])=>s+a.array.byteLength,0);for(const[k,a]of entries){const array=new a.array.constructor(unique.length*a.itemSize);unique.forEach((id,i)=>array.set(a.array.subarray(id*a.itemSize,(id+1)*a.itemSize),i*a.itemSize));const replacement=new BufferAttribute(array,a.itemSize,a.normalized);replacement.name=a.name;replacement.setUsage(a.usage);replacements[k]=replacement;}const index=new BufferAttribute(unique.length-1<65535?new Uint16Array(ids):new Uint32Array(ids),1);prepared.push({...plan,replacements,index});results.push({name:mesh.name,beforeRows:count,afterRows:unique.length,avoidedBytes:before-entries.reduce((s,[k])=>s+replacements[k].array.byteLength,0)-index.array.byteLength});
 }
 try{for(const {g,replacements,index}of prepared){for(const[k,a]of Object.entries(replacements))g.setAttribute(k,a);g.setIndex(index);}}
 catch(error){for(const {g,originalAttributes,originalIndex}of plans){for(const key of Object.keys(g.attributes))if(!Object.hasOwn(originalAttributes,key))delete g.attributes[key];for(const[k,a]of Object.entries(originalAttributes))g.attributes[k]=a;g.index=originalIndex;}throw error;}
 return results;
}

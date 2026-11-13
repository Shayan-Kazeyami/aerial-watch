import {Float32BufferAttribute} from './vendor/three.module.js';
import {CAP_DELTA as D} from './assembly-cap-delta.js';
const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
export async function makeCapCandidate(source){
 const position=source?.getAttribute?.('position');
 if(!position||position.itemSize!==3||position.count!==D.vertexCount||position.normalized||position.isInterleavedBufferAttribute||!(position.array instanceof Float32Array))throw Error('Unexpected CASE position layout');
 const input=new Uint8Array(position.array.buffer,position.array.byteOffset,position.array.byteLength).slice();
 if(await digest(input)!==D.sourcePositionSHA256)throw Error('Unexpected CASE position hash');
 const output=new Float32Array(input.buffer.slice(0));
 for(let i=0;i<D.indices.length;i++)for(let j=0;j<3;j++)output[3*D.indices[i]+j]=D.positions[3*i+j];
 if(await digest(new Uint8Array(output.buffer))!==D.candidatePositionSHA256)throw Error('Cap candidate hash mismatch');
 const current=source.getAttribute('position');
 if(current!==position||new Uint8Array(position.array.buffer,position.array.byteOffset,position.array.byteLength).some((v,i)=>v!==input[i]))throw Error('CASE changed during preparation');
 const copy=source.clone();copy.setAttribute('position',new Float32BufferAttribute(output,3));copy.computeBoundingBox();copy.computeBoundingSphere();
 return copy;
}

// Fixed production geometry, not a presentation option. Reset only changes viewer state.
// The owner must dispose this installation before disposing the source object tree.
export async function installCapRefinement(root,{signal}={}){
 signal?.throwIfAborted();
 const cases=[];root.traverse(o=>{if(o.isMesh&&o.userData?.assemblyId==='CASE')cases.push(o);});
 if(cases.length!==1)throw Error('Expected exactly one CASE mesh');
 const mesh=cases[0],original=mesh.geometry;let candidate;
 try{
  candidate=await makeCapCandidate(original);signal?.throwIfAborted();
  if(mesh.geometry!==original)throw Error('CASE changed during preparation');
  mesh.geometry=candidate;
 }catch(error){candidate?.dispose();throw error;}
 let disposed=false;
 return {audit:Object.freeze({revision:'case-cap-radius-015',sourcePositionSHA256:D.sourcePositionSHA256,candidatePositionSHA256:D.candidatePositionSHA256,changedVertices:D.changedVertices,fixedGeometry:true}),
  get active(){return !disposed&&mesh.geometry===candidate;},
  dispose(){if(disposed)return;disposed=true;if(mesh.geometry===candidate)mesh.geometry=original;candidate.dispose();}};
}

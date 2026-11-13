// Local lossless ordering experiment. No geometry/normal values are changed.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {MeshoptEncoder as E} from '../../strap-combined-qa/encoder-source/vendor/meshopt/meshopt_encoder.js';
await E.ready;
const dir='movement-retopo-qa/serialized-current',b=fs.readFileSync(dir+'/assembly.glb'),n=b.readUInt32LE(12),original=JSON.parse(b.subarray(20,20+n)),binary=b.subarray(28+n);
const read=(j,id)=>{const a=j.accessors[id],v=j.bufferViews[a.bufferView];return binary.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength)};
const p=new Float32Array(Uint8Array.from(read(original,718)).buffer),normal=new Float32Array(Uint8Array.from(read(original,719)).buffer),index=new Uint16Array(Uint8Array.from(read(original,720)).buffer);
const triangleDigests=(pos,norm,indices)=>{const out=[];for(let i=0;i<indices.length;i+=3){const ar=new Float32Array(18);for(let k=0;k<3;k++){ar.set(pos.subarray(indices[i+k]*3,indices[i+k]*3+3),k*6);ar.set(norm.subarray(indices[i+k]*3,indices[i+k]*3+3),k*6+3)}out.push(crypto.createHash('sha256').update(new Uint8Array(ar.buffer)).digest('hex'))}return out.sort()};
const triangles=triangleDigests(p,normal,index);
for(const [name,trianglesOn,optsize]of [['fetch',false,false],['cache',true,false],['strip',true,true]]){
const j=structuredClone(original),ix=new Uint32Array(index),[remap,count]=E.reorderMesh(ix,trianglesOn,optsize);assert.equal(count,p.length/3);const pp=new Float32Array(p.length),nn=new Float32Array(normal.length);for(let i=0;i<remap.length;i++){pp.set(p.subarray(i*3,i*3+3),remap[i]*3);nn.set(normal.subarray(i*3,i*3+3),remap[i]*3)}
assert.deepEqual(triangleDigests(pp,nn,ix),triangles);const reps=new Map([[718,Buffer.from(pp.buffer)],[719,Buffer.from(nn.buffer)],[720,Buffer.from(new Uint16Array(ix).buffer)]]);let offset=0;const chunks=[];
for(let ai=0;ai<j.accessors.length;ai++){const a=j.accessors[ai],v=j.bufferViews[a.bufferView],data=reps.get(ai)||read(original,ai);v.byteOffset=offset;v.byteLength=data.length;chunks.push(data,Buffer.alloc((4-data.length%4)%4));offset+=data.length+(4-data.length%4)%4}
j.buffers=[{byteLength:offset}];let jb=Buffer.from(JSON.stringify(j));jb=Buffer.concat([jb,Buffer.alloc((4-jb.length%4)%4,32)]);const h=Buffer.alloc(20),bh=Buffer.alloc(8);[0x46546c67,2,28+jb.length+offset,jb.length,0x4e4f534a].forEach((x,i)=>h.writeUInt32LE(x,i*4));bh.writeUInt32LE(offset);bh.writeUInt32LE(0x004e4942,4);const out=dir+'/'+name;fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/assembly.glb',Buffer.concat([h,jb,bh,...chunks]));fs.writeFileSync(out+'/ordering-proof.json',JSON.stringify({orientedPositionNormalTriangleMultisetExact:true,unchangedOtherAccessors:true,name,count},null,2));
}

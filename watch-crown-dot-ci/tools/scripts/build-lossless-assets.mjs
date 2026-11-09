import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import {MeshoptEncoder as E} from '../vendor/meshopt/meshopt_encoder.js';
import {MeshoptDecoder as D} from '../vendor/meshopt/meshopt_decoder.mjs';
await Promise.all([E.ready,D.ready]);
const root=new URL('../',import.meta.url).pathname;
const destination=root+'optimized-assets/';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ext='EXT_meshopt_compression';
const parse=b=>{assert.equal(b.readUInt32LE(0),0x46546c67);let n=b.readUInt32LE(12);return {j:JSON.parse(b.subarray(20,20+n)),bin:b.subarray(28+n)}};
const receipt=JSON.parse(fs.readFileSync(root+'vendor/meshopt/PROVENANCE.json'));
for(const [file,hash]of Object.entries(receipt.files))assert.equal(sha(fs.readFileSync(root+'vendor/meshopt/'+file)),hash);
fs.mkdirSync(destination,{recursive:true});
const outputs=[];
for(const name of (process.argv.length>2?process.argv.slice(2):['rebuild/assembly.glb','premium-face/face-svg04.glb','quality-study/leather-craft-r11.glb'])) {
 const input=fs.readFileSync(root+name), originalHash=sha(input),{j,bin}=parse(input),out=structuredClone(j);const views=[];let chunks=[],length=0,encodeMs=0,decodeMs=0,geom=0,comp=0;const cpuStart=process.cpuUsage();
 const append=b=>{const offset=length;chunks.push(b);length+=b.length;const pad=(4-length%4)%4;if(pad){chunks.push(Buffer.alloc(pad));length+=pad;}return offset;};
 for(let i=0;i<j.bufferViews.length;i++){
  const v=j.bufferViews[i],raw=bin.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength),a=j.accessors.find(a=>a.bufferView===i),nv=out.bufferViews[i];let record={view:i,originalBytes:raw.length,sourceSha256:sha(raw)};
  if(a){assert.equal(a.byteOffset||0,0);assert(!a.sparse);const stride=({SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type])*({5123:2,5125:4,5126:4}[a.componentType]);assert.equal(a.count*stride,raw.length);const mode=v.target===34963?'INDICES':'ATTRIBUTES';let t=performance.now();const encoded=E.encodeGltfBuffer(raw,a.count,stride,mode,0);encodeMs+=performance.now()-t;let target=new Uint8Array(raw.length);t=performance.now();D.decodeGltfBuffer(target,a.count,stride,encoded,mode,'NONE');decodeMs+=performance.now()-t;assert.deepEqual(Buffer.from(target),raw);geom+=raw.length;
   // Require ample space saving to cover JSON extension metadata.
   if(encoded.length+200<raw.length){nv.buffer=1;nv.extensions={...(nv.extensions||{}),[ext]:{buffer:0,byteOffset:append(Buffer.from(encoded)),byteLength:encoded.length,byteStride:stride,count:a.count,mode,filter:'NONE'}};comp+=encoded.length;record={...record,mode,stride,count:a.count,compressedBytes:encoded.length,retainedCompressed:true};}
   else {nv.buffer=0;nv.byteOffset=append(raw);comp+=raw.length;record={...record,mode,compressedBytes:encoded.length,retainedCompressed:false};}
  }else {nv.buffer=0;nv.byteOffset=append(raw);record.imageOrOtherUnchanged=true;}
  views.push(record);
 }
 out.buffers=[{byteLength:length},{byteLength:j.buffers[0].byteLength,extensions:{[ext]:{fallback:true}}}];out.extensionsUsed=[...(j.extensionsUsed||[]),ext];out.extensionsRequired=[...(j.extensionsRequired||[]),ext];
 let json=Buffer.from(JSON.stringify(out));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);const body=Buffer.concat(chunks),head=Buffer.alloc(20);head.writeUInt32LE(0x46546c67,0);head.writeUInt32LE(2,4);head.writeUInt32LE(28+json.length+body.length,8);head.writeUInt32LE(json.length,12);head.writeUInt32LE(0x4e4f534a,16);const bh=Buffer.alloc(8);bh.writeUInt32LE(body.length,0);bh.writeUInt32LE(0x004e4942,4);const result=Buffer.concat([head,json,bh,body]);
 // Verify serialized artifact, every view and image; normalized storage-only JSON.
 const read=parse(result);for(let i=0;i<j.bufferViews.length;i++){const v=read.j.bufferViews[i],c=v.extensions?.[ext],old=j.bufferViews[i],expected=bin.subarray(old.byteOffset||0,(old.byteOffset||0)+old.byteLength);let got;if(c){got=new Uint8Array(v.byteLength);D.decodeGltfBuffer(got,c.count,c.byteStride,read.bin.subarray(c.byteOffset,c.byteOffset+c.byteLength),c.mode,c.filter);}else got=read.bin.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength);assert.deepEqual(Buffer.from(got),expected);}
 const normalized=structuredClone(read.j);normalized.buffers=j.buffers;normalized.bufferViews=normalized.bufferViews.map((v,i)=>{const o=j.bufferViews[i];v.buffer=o.buffer;if('byteOffset'in o)v.byteOffset=o.byteOffset;else delete v.byteOffset;if(v.extensions){delete v.extensions[ext];if(!Object.keys(v.extensions).length)delete v.extensions;}return v;});for(const key of ['extensionsUsed','extensionsRequired']){if(j[key])normalized[key]=j[key];else delete normalized[key];}assert.deepEqual(normalized,j);assert.equal(sha(fs.readFileSync(root+name)),originalHash);
 const canonicalPath=name.replaceAll('/','__').replace('.glb','.meshopt.glb');
 let path=canonicalPath,delivery=result,transportFormat='glb';
 if(name==='rebuild/assembly.glb'){
  const gzip=zlib.gzipSync(result,{level:9});
  assert.deepEqual(zlib.gunzipSync(gzip),result);assert.deepEqual(zlib.gzipSync(result,{level:9}),gzip);assert.equal(gzip.readUInt32LE(4),0);
  if(gzip.length<result.length){path+='.gz';delivery=gzip;transportFormat='explicit-gzip';}
 }
 fs.writeFileSync(destination+path,delivery);
 // The canonical oversized GLB is reproducible in memory, not a required deploy file.
 if(path!==canonicalPath)fs.rmSync(destination+canonicalPath,{force:true});
 const record={name,transportFormat,deliveryBytes:delivery.length,deliverySha256:sha(delivery),deliverySavedPercent:100*(1-delivery.length/input.length),gzipRoundtripExact:transportFormat==='explicit-gzip',inputBytes:input.length,outputBytes:result.length,savedBytes:input.length-result.length,savedPercent:100*(1-result.length/input.length),geometryBytes:geom,storedGeometryBytes:comp,inputBrotliBytes:zlib.brotliCompressSync(input,{params:{[zlib.constants.BROTLI_PARAM_QUALITY]:5}}).length,outputBrotliBytes:zlib.brotliCompressSync(result,{params:{[zlib.constants.BROTLI_PARAM_QUALITY]:5}}).length,inputGzipBytes:zlib.gzipSync(input,{level:9}).length,outputGzipBytes:zlib.gzipSync(result,{level:9}).length,encodeMs,decodeMs,cpuMicroseconds:process.cpuUsage(cpuStart),maxRSSKiB:process.resourceUsage().maxRSS,inputSha256:originalHash,outputSha256:sha(result),viewCount:views.length,compressedViews:views.filter(v=>v.retainedCompressed).length,allViewsByteExact:true,nonStorageJSONExact:true,path,views};outputs.push(record);console.log(JSON.stringify({...record,views:undefined}));
}
fs.writeFileSync(destination+'audit.json',JSON.stringify({transportCompression:{node:process.version,zlib:process.versions.zlib,brotli:process.versions.brotli,gzipLevel:9,brotliQuality:5,actualHTTPEncoding:'unknown'},codec:{tag:'v1.0',commit:'73583c335e541c139821d0de2bf5f12960a04941',license:'MIT',encoderSHA256:sha(fs.readFileSync(root+'vendor/meshopt/meshopt_encoder.js')),decoderSHA256:sha(fs.readFileSync(root+'vendor/meshopt/meshopt_decoder.mjs'))},outputs},null,2));

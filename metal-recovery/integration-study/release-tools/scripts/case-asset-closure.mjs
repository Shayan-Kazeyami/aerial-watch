import {createHash} from 'node:crypto';import {gunzipSync} from 'node:zlib';
export const CASE_ASSETS=Object.freeze(['case-assets/case-combined-r5.meshopt.glb.gz',...['planar-satin.png','planar-normal-g32.png','revolved-satin.png','body-normal-g32.png'].map(n=>'case-assets/'+n)]);
const sha=b=>createHash('sha256').update(b).digest('hex');
const descriptor=(buffers,name)=>{const b=buffers.get(name);if(!b)throw Error(`Missing CASE descriptor ${name}`);const s=b.toString().trim(),m=s.match(/^export const [A-Z_]+ = (?:Object\.freeze\()?({[\s\S]*})(?:\))?;$/);if(!m)throw Error(`Unsupported CASE descriptor syntax ${name}`);return JSON.parse(m[1]);};
export function validateCaseAssetClosure(buffers){
 if(!buffers.has('assembly-case-combined-data.js'))return null;
 const data=descriptor(buffers,'assembly-case-combined-data.js'),delivery=descriptor(buffers,'assembly-case-combined-delivery-data.js'),material=descriptor(buffers,'assembly-case-combined-material-data.js');
 const check=(path,hash,size)=>{const b=buffers.get(path);if(!CASE_ASSETS.includes(path)||!b||sha(b)!==hash||(size!==undefined&&b.length!==size))throw Error(`CASE resource identity mismatch: ${path}`);return b;};
 const compressed=check(delivery.url,delivery.gzipSHA256,delivery.gzipBytes),decoded=gunzipSync(compressed,{maxOutputLength:delivery.decodedBytes});if(decoded.length!==delivery.decodedBytes||sha(decoded)!==delivery.decodedSHA256)throw Error('CASE decoded GLB identity mismatch');
 let cursor=0;for(const g of data.groups){if(g.start!==cursor||g.count%3||![0,1,2,3,4].includes(g.materialIndex))throw Error('CASE group closure invalid');cursor+=g.count}if(cursor!==data.triangles*3||data.triangles!==delivery.triangles)throw Error('CASE triangle closure invalid');
 for(const [i,r]of material.normalProof.records.entries()){check('case-assets/'+(i?'revolved-satin.png':'planar-satin.png'),r.sourceHeightSHA256);check('case-assets/'+r.normalPNG,r.normalSHA256)}
 if(!buffers.get('assembly-case-combined-material.js')?.toString().includes("new URL('./case-assets/',import.meta.url)"))throw Error('CASE material resource namespace missing');
 return {geometrySHA256:delivery.gzipSHA256,decodedSHA256:delivery.decodedSHA256,triangles:data.triangles,resources:CASE_ASSETS.length,textureBytesExact:true};
}

export function validateCaseAssetPartitions(partitions){const containing=[...partitions].filter(p=>CASE_ASSETS.some(f=>p.has(f)));if(containing.length&&(containing.length!==1||!CASE_ASSETS.every(f=>containing[0].has(f))))throw Error('CASE resources must occupy one complete immutable URL-owner namespace');}

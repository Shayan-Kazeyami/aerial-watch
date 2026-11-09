import {validateCaseAssetPartitions} from './case-asset-closure.mjs';
/** Local verified immutable-owner graph. No network, mutation, or runtime chains. */
import {readFile,lstat,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';import path from 'node:path';
import {validateAssetClosure} from './build-atelier-release.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
export const safeReleasePath=p=>typeof p==='string'&&/^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(p)&&p.split('/').every(x=>x!=='.'&&x!=='..');
const id=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x),sort=(a,b)=>a.path<b.path?-1:a.path>b.path?1:0;
export function releaseIdentity(f){if(!f||!safeReleasePath(f.path)||['deployment-manifest.json','release-receipt.json'].includes(f.path.split('/')[0])||!Number.isSafeInteger(f.sizeBytes)||f.sizeBytes<0||!id(f.sha256))throw Error('Invalid file identity');return {path:f.path,sizeBytes:f.sizeBytes,sha256:f.sha256};}
async function noLinks(filename){let cursor=path.parse(filename).root;for(const part of filename.split(path.sep).filter(Boolean)){cursor=path.join(cursor,part);if((await lstat(cursor)).isSymbolicLink())throw Error(`Symlink rejected: ${cursor}`);}}
async function inventory(root,prefix=''){const result=[];for(const e of await readdir(path.join(root,prefix),{withFileTypes:true})){const p=prefix?`${prefix}/${e.name}`:e.name;if(e.isSymbolicLink())throw Error(`Symlink rejected: ${p}`);if(e.isDirectory())result.push(...await inventory(root,p));else if(e.isFile())result.push(p);else throw Error(`Non-regular entry: ${p}`);}return result.sort();}
export async function readReleaseOwners({ownerRoot,ownerRoots=[],closureOptions}={}){
 if(!Array.isArray(ownerRoots))throw Error('ownerRoots must be an array');
 const supplied=[...new Set([ownerRoot,...ownerRoots].filter(Boolean).map(r=>path.resolve(r)))];if(!supplied.length)throw Error('Sealed owner roots required');
 const locations=new Map(),cache=new Map(),active=new Set();
 // Catalog names are not trusted until their complete content-derived identity verifies.
 for(const root of supplied){await noLinks(root);await noLinks(path.join(root,'release-receipt.json'));const receipt=JSON.parse(await readFile(path.join(root,'release-receipt.json'),'utf8'));if(!id(receipt.releaseId))throw Error('Owner receipt identity mismatch');if(locations.has(receipt.releaseId)&&locations.get(receipt.releaseId)!==root)throw Error('Ambiguous owner roots');locations.set(receipt.releaseId,root);}
 async function load(root,expected){root=path.resolve(root);if(cache.has(root)){const cached=cache.get(root);if(expected&&cached.releaseId!==expected)throw Error('Owner receipt identity mismatch');return cached;}if(active.has(root))throw Error('Cyclic immutable owner references');if(active.size>=128)throw Error('Owner chain exceeds safety limit');active.add(root);
  try{await noLinks(root);const names=await inventory(root),manifest=JSON.parse(await readFile(path.join(root,'deployment-manifest.json'),'utf8')),receipt=JSON.parse(await readFile(path.join(root,'release-receipt.json'),'utf8'));
   if(![1,2].includes(manifest.schemaVersion))throw Error('Invalid deployment manifest');const schemaVersion=manifest.schemaVersion,rawLocal=schemaVersion===1?manifest.files:manifest.localFiles;
   if(!Array.isArray(rawLocal)||!rawLocal.length||schemaVersion===2&&!Array.isArray(manifest.references))throw Error('Invalid deployment manifest');
   const localFiles=rawLocal.map(releaseIdentity).sort(sort),references=(schemaVersion===2?manifest.references:[]).map(f=>{if(!id(f.ownerReleaseId))throw Error('Invalid immutable owner ID');return {...releaseIdentity(f),ownerReleaseId:f.ownerReleaseId};}).sort(sort),seen=new Set();
   for(const f of [...localFiles,...references]){if(seen.has(f.path))throw Error(`Duplicate/colliding identity: ${f.path}`);seen.add(f.path);}
   if(JSON.stringify(names)!==JSON.stringify([...localFiles.map(f=>f.path),'deployment-manifest.json','release-receipt.json'].sort()))throw Error('Release inventory mismatch: unexpected or absent files');
   const releaseId=sha(JSON.stringify(schemaVersion===1?localFiles:{schemaVersion:2,localFiles,references})),totalBytes=localFiles.reduce((n,f)=>n+f.sizeBytes,0);
   if(expected&&expected!==releaseId||receipt.schemaVersion!==schemaVersion||receipt.releaseId!==releaseId||receipt.fileCount!==localFiles.length||receipt.totalBytes!==totalBytes||schemaVersion===2&&(manifest.releaseId!==releaseId||manifest.referenceLayout!=='../<ownerReleaseId>/<path>'||receipt.referenceCount!==references.length||receipt.referencedBytes!==references.reduce((n,f)=>n+f.sizeBytes,0)))throw Error('Release receipt identity mismatch');
   const buffers=new Map(),files=new Map();
   for(const f of localFiles){const b=await readFile(path.join(root,f.path));if(b.length!==f.sizeBytes||sha(b)!==f.sha256)throw Error(`Identity mismatch: ${f.path}`);buffers.set(f.path,b);files.set(f.path,{...f,ownerReleaseId:releaseId});}
   for(const f of references){const owner=await load(locations.get(f.ownerReleaseId)||path.join(path.dirname(root),f.ownerReleaseId),f.ownerReleaseId),canonical=owner.files.get(f.path);if(!canonical||canonical.sizeBytes!==f.sizeBytes||canonical.sha256!==f.sha256)throw Error(`Reference not in verified owner: ${f.path}`);files.set(f.path,canonical);buffers.set(f.path,owner.buffers.get(f.path));}
   const assetClosure=validateAssetClosure(buffers,closureOptions),partitions=new Map();for(const [p,f]of files){if(!partitions.has(f.ownerReleaseId))partitions.set(f.ownerReleaseId,new Map());partitions.get(f.ownerReleaseId).set(p,buffers.get(p));}validateCaseAssetPartitions(partitions.values());for(const partition of partitions.values())validateAssetClosure(partition,{...closureOptions,partitionOnly:true});
   const result={root,schemaVersion,releaseId,totalBytes:[...files.values()].reduce((n,f)=>n+f.sizeBytes,0),localFiles,files,buffers,assetClosure};cache.set(root,result);return result;
  }finally{active.delete(root);}
 }
 const owners=[];for(const root of supplied)owners.push(await load(root));return {owners,releases:[...cache.values()],roots:[...cache.keys()]};
}

import {validateCaseAssetPartitions} from './case-asset-closure.mjs';
import {readFile,writeFile,mkdir,lstat,rename,readdir,rm} from 'node:fs/promises';
import {createHash,randomUUID} from 'node:crypto';
import path from 'node:path';
import {readReleaseOwners} from './read-release-owners.mjs';
import {validateAssetClosure} from './build-atelier-release.mjs';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const safe=p=>typeof p==='string'&&/^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(p)&&p.split('/').every(x=>x!=='.'&&x!=='..');
const reserved=p=>['deployment-manifest.json','release-receipt.json'].includes(p.split('/')[0]);
const sort=(a,b)=>a.path<b.path?-1:a.path>b.path?1:0;
async function noLinks(filename){let cursor=path.parse(path.resolve(filename)).root;for(const part of path.resolve(filename).split(path.sep).filter(Boolean)){cursor=path.join(cursor,part);try{if((await lstat(cursor)).isSymbolicLink())throw Error(`Symlink rejected: ${cursor}`);}catch(e){if(e.code==='ENOENT')break;throw e;}}}
async function treeFiles(root,prefix=''){const result=[];for(const e of await readdir(path.join(root,prefix),{withFileTypes:true})){const p=prefix?`${prefix}/${e.name}`:e.name;if(e.isSymbolicLink())throw Error(`Symlink rejected: ${p}`);if(e.isDirectory())result.push(...await treeFiles(root,p));else if(e.isFile())result.push(p);else throw Error(`Non-regular file: ${p}`);}return result.sort();}
function identity(f){if(!safe(f.path)||reserved(f.path)||!Number.isSafeInteger(f.sizeBytes)||f.sizeBytes<0||!/^[a-f0-9]{64}$/.test(f.sha256))throw Error(`Invalid identity: ${f.path}`);return {path:f.path,sizeBytes:f.sizeBytes,sha256:f.sha256};}
async function readIdentity(root,f){const name=path.join(root,f.path);await noLinks(name);if(!(await lstat(name)).isFile())throw Error(`Not a regular file: ${f.path}`);const b=await readFile(name);if(b.length!==f.sizeBytes||sha(b)!==f.sha256)throw Error(`Identity mismatch: ${f.path}`);return b;}
/** Local-only sparse staging. No promotion, deletion of existing releases, or network.
 * References are same-path immutable siblings; verified schema-1/2 owner chains
 * are flattened to the release that physically owns each referenced file.
 * Runtime routing must be embodied in localBuffers and independently browser-tested.
 */
export async function stageSharedRelease({localBuffers,references,ownerRoot,ownerRoots=[],outputRoot,entry='atelier-preview.html'}={}){
 if(!(localBuffers instanceof Map)||!Array.isArray(references)||(!ownerRoot&&!ownerRoots.length)||!outputRoot)throw Error('Local buffers, references, sealed owner and output required');
 if(!safe(entry)||!entry.endsWith('.html')||!localBuffers.has(entry))throw Error('Entry must be a local HTML file');
 outputRoot=path.resolve(outputRoot);
 // Snapshot caller buffers before any awaits can allow mutations to change staged bytes.
 const local=new Map();for(const [p,b] of localBuffers){if(!safe(p)||reserved(p)||!Buffer.isBuffer(b))throw Error(`Invalid local file: ${p}`);local.set(p,Buffer.from(b));}
 const refs=references.map(f=>({...identity(f),ownerReleaseId:f.ownerReleaseId})).sort(sort);
 await noLinks(outputRoot);
 const catalog=await readReleaseOwners({ownerRoot,ownerRoots});
 for(const root of catalog.roots)if(outputRoot===root||outputRoot.startsWith(root+path.sep))throw Error('Output must not modify immutable owner tree');
 const byId=new Map(catalog.releases.map(o=>[o.releaseId,o])),referencedBuffers=new Map(),partitions=new Map();
 for(const f of refs){const owner=byId.get(f.ownerReleaseId);if(!owner)throw Error(`Wrong immutable owner: ${f.path}`);if(local.has(f.path)||referencedBuffers.has(f.path))throw Error(`Duplicate/colliding reference: ${f.path}`);const existing=owner.files.get(f.path);if(!existing||existing.sizeBytes!==f.sizeBytes||existing.sha256!==f.sha256)throw Error(`Reference not in verified owner: ${f.path}`);f.ownerReleaseId=existing.ownerReleaseId;const bytes=owner.buffers.get(f.path);referencedBuffers.set(f.path,bytes);if(!partitions.has(f.ownerReleaseId))partitions.set(f.ownerReleaseId,new Map());partitions.get(f.ownerReleaseId).set(f.path,bytes);}
 const merged=new Map([...local,...referencedBuffers]);const closure=validateAssetClosure(merged);
 // Logical closure alone is insufficient: a local glTF cannot resolve its
 // relative buffer in another release. Each URL-owner partition must close too.
 validateCaseAssetPartitions([local,...partitions.values()]);validateAssetClosure(local,{partitionOnly:true});for(const partition of partitions.values())validateAssetClosure(partition,{partitionOnly:true});
 const localFiles=[...local].map(([p,b])=>({path:p,sizeBytes:b.length,sha256:sha(b)})).sort(sort);
 const canonical={schemaVersion:2,localFiles,references:refs};const releaseId=sha(JSON.stringify(canonical));
 const manifest=Buffer.from(JSON.stringify({...canonical,releaseId,referenceLayout:'../<ownerReleaseId>/<path>',assetClosure:closure},null,2)+'\n');
 const totalBytes=localFiles.reduce((n,f)=>n+f.sizeBytes,0),referencedBytes=refs.reduce((n,f)=>n+f.sizeBytes,0);
 const receipt=Buffer.from(JSON.stringify({schemaVersion:2,releaseId,algorithm:'SHA-256',canonicalization:'SHA-256 of UTF-8 JSON.stringify({schemaVersion:2,localFiles,references}); each array sorted lexicographically by path; field order as shown in manifest',fileCount:localFiles.length,totalBytes,referenceCount:refs.length,referencedBytes},null,2)+'\n');
 const root=path.join(outputRoot,'releases'),destination=path.join(root,releaseId);
 const verify=async directory=>{await noLinks(directory);for(const f of localFiles)await readIdentity(directory,f);for(const [p,b] of [['deployment-manifest.json',manifest],['release-receipt.json',receipt]]){await noLinks(path.join(directory,p));if(!(await readFile(path.join(directory,p))).equals(b))throw Error(`Existing shared metadata differs: ${p}`);}if(JSON.stringify(await treeFiles(directory))!==JSON.stringify([...localFiles.map(f=>f.path),'deployment-manifest.json','release-receipt.json'].sort()))throw Error('Shared release inventory mismatch');};
 await mkdir(root,{recursive:true});await noLinks(root);let exists=false;try{await lstat(destination);exists=true;}catch(e){if(e.code!=='ENOENT')throw e;}
 if(exists)await verify(destination);else{const temporary=path.join(root,`.stage-shared-${randomUUID()}`);await mkdir(temporary);try{for(const [p,b] of local){await mkdir(path.dirname(path.join(temporary,p)),{recursive:true});await writeFile(path.join(temporary,p),b);}await writeFile(path.join(temporary,'deployment-manifest.json'),manifest);await writeFile(path.join(temporary,'release-receipt.json'),receipt);await verify(temporary);try{await rename(temporary,destination);}catch(e){if(!['EEXIST','ENOTEMPTY'].includes(e.code))throw e;await verify(destination);await rm(temporary,{recursive:true});}}catch(e){await rm(temporary,{recursive:true,force:true});throw e;}}
 return {releaseId,releasePath:destination,files:localFiles.length,references:refs.length,totalBytes,referencedBytes,assetClosure:closure};
}

// Immutable a8c129-derived capture-readiness release. Private builder; no publication/ref writes.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {stageSharedRelease} from '../../../metal-recovery/integration-study/release-tools/scripts/stage-shared-release.mjs';
import {readReleaseOwners} from '../../../metal-recovery/integration-study/release-tools/scripts/read-release-owners.mjs';
export const OWNER='a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473';
export const GEOMETRY='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7';
export const PATCH_SHA='7f8e74fe8114eb75a5dafa7501b555b7cd2e03683fdd171e8ea81a7dbc028675';
export const MODULES=['atelier-preview.js'];
export const sha=b=>createHash('sha256').update(b).digest('hex');
export function applyPatch(text,ops,name){for(const op of ops){if(Object.hasOwn(op,'append')){text+=op.append;continue;}if(!op.old||text.split(op.old).length!==2)throw Error('Patch anchor must occur exactly once: '+name);text=text.replace(op.old,op.new);}return text;}
const importPaths=s=>[...s.matchAll(/(?:from\s*|import\s*\(|import\s*)['"]([^'"]+)['"]/g)].map(x=>x[1]);
export async function transform(owner){
 const old=JSON.parse(await fs.readFile(path.join(owner,'deployment-manifest.json')));
 if(old.releaseId!==OWNER)throw Error('Wrong baseline owner');
 const patchBytes=await fs.readFile(new URL('./patches.json',import.meta.url));if(sha(patchBytes)!==PATCH_SHA)throw Error('Unreviewed patch changes');
 const patches=JSON.parse(patchBytes);if(JSON.stringify(Object.keys(patches).sort())!==JSON.stringify(MODULES))throw Error('Wrong module scope');
 const buffers=new Map(),before=new Map();
 for(const f of old.localFiles){if(['deployment-manifest.json','release-receipt.json'].includes(f.path))throw Error('Reserved owner entry');const b=await fs.readFile(path.join(owner,f.path));if(b.length!==f.sizeBytes||sha(b)!==f.sha256)throw Error('Owner local identity mismatch '+f.path);buffers.set(f.path,b);before.set(f.path,b);}
 if(sha(buffers.get('leather-assets/r14/geometry.bin'))!==GEOMETRY)throw Error('Wrong UV15 geometry');
 const changes=[];
 for(const name of MODULES){const original=buffers.get(name);if(!original)throw Error('Patched module not local: '+name);const s=original.toString(),updated=applyPatch(s,patches[name],name);if(JSON.stringify(importPaths(s))!==JSON.stringify(importPaths(updated)))throw Error('Import paths changed: '+name);const b=Buffer.from(updated);buffers.set(name,b);changes.push({path:name,previousSHA256:sha(original),sha256:sha(b),bytes:b.length});}
 // Capture identity must describe build-transformed runtime bytes, not editable source metadata.
 const files=[...buffers].filter(([p])=>!p.includes('/')&&/\.(js|css|html)$/.test(p)).sort(([a],[b])=>a<b?-1:a>b?1:0).map(([p,b])=>({path:p,bytes:b.length,sha256:sha(b)}));
 const revision={schemaVersion:1,algorithm:'SHA-256',scope:'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.',canonicalization:'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.',digest:sha(JSON.stringify(files)),files};
 buffers.set('quality-study/viewer-revision.json',Buffer.from(JSON.stringify(revision,null,2)+'\n'));buffers.set('quality-study/viewer-revision.js',Buffer.from('export default '+JSON.stringify(revision)+';\n'));
 const meta=JSON.parse(buffers.get('shared-release-build.json'));meta.predecessorReleaseId=OWNER;meta.captureReadiness={revision:'capture-readiness-headroom-v1',patchSHA256:PATCH_SHA,scope:'Readiness timeout 10000 to 30000 milliseconds only; exact frame acknowledgement, dimensions, stability, cancellation and cleanup guards unchanged.',verification:'Editable source 805 tests; bounded stalled-loop and trusted UI cancellation evidence; sealed and live acceptance tracked separately.',limitations:'Additional bounded readiness headroom, not an FPS improvement or guaranteed export reliability.',modules:changes};buffers.set('shared-release-build.json',Buffer.from(JSON.stringify(meta,null,2)+'\n'));
 const allowed=new Set([...MODULES,'quality-study/viewer-revision.js','quality-study/viewer-revision.json','shared-release-build.json']);for(const[p,b]of buffers)if(!allowed.has(p)&&!b.equals(before.get(p)))throw Error('Unexpected change '+p);
 return{buffers,references:old.references,proof:{owner:OWNER,geometryIdentity:{bytes:buffers.get('leather-assets/r14/geometry.bin').length,sha256:GEOMETRY,bufferIndex:0},changes,allowedChangedPaths:[...allowed].sort(),actualChangedPaths:[...buffers].filter(([p,b])=>!b.equals(before.get(p))).map(([p])=>p).sort(),preservedLocalFiles:[...buffers.keys()].filter(p=>!allowed.has(p)).length,referenceCount:old.references.length,importOwnerPathsPreserved:true,revisionDigest:revision.digest}};
}
export async function build(owner='preview-b/releases/'+OWNER,output='preview-b',receipt='capture-readiness-output/sealed-release.json'){
 await readReleaseOwners({ownerRoot:owner});const {buffers,references,proof}=await transform(owner);
 const result=await stageSharedRelease({localBuffers:buffers,references,ownerRoot:owner,outputRoot:output});await readReleaseOwners({ownerRoot:result.releasePath});
 const relativeReleasePath=path.relative(process.cwd(),result.releasePath);if(relativeReleasePath.startsWith('..')||path.isAbsolute(relativeReleasePath))throw Error('Output must be inside working directory');
 await fs.mkdir(path.dirname(receipt),{recursive:true});const value={...result,releasePath:relativeReleasePath,geometryIdentity:proof.geometryIdentity,captureReadinessRevision:'capture-readiness-headroom-v1',proof,rollbackMain:'77989272c971724b90c932c48d4f769573c933a5',rollbackRelease:OWNER,promotionAllowed:false};await fs.writeFile(receipt,JSON.stringify(value,null,2)+'\n');console.log(JSON.stringify(value));return value;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await build(...process.argv.slice(2));

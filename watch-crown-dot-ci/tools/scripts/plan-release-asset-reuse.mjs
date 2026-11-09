/** Read-only feasibility audit. NOT a deployment manifest or a sparse release builder. */
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {readReleaseOwners} from './read-release-owners.mjs';
const safe=p=>typeof p==='string'&&/^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(p)&&p.split('/').every(x=>x!=='.'&&x!=='..');
const generated=new Set(['quality-study/viewer-revision.js','quality-study/viewer-revision.json']);
const roots=new Set(['assets','aerial-assets','rebuild','premium-face','quality-study','optimized-assets','vendor','docs','open-front','leather-assets','case-assets','leather-compat-r12']);
/** Whole top-level asset directories stay together: conservative relative-resource closure.
 * Excludes release-local provenance. Vendor remains one indivisible directory.
 * A group is reusable only when every candidate path has the same owner bytes.
 * Extra owner files are harmless and remain preserved, never deleted.
 */
export async function planReleaseAssetReuse({ownerRoot,ownerRoots=[],assetDirectories=[],candidateRoot,publishedBytes=null,hostingLimitBytes=2**30,closureOptions}={}){
 if((!ownerRoot&&!ownerRoots.length)||!candidateRoot)throw Error('Owner and candidate sealed release roots required');for(const [key,value] of Object.entries({publishedBytes,hostingLimitBytes}))if(value!==null&&(!Number.isSafeInteger(value)||value<0))throw Error(`Invalid ${key}`);
 const catalog=await readReleaseOwners({ownerRoot,ownerRoots,closureOptions}),owner=catalog.owners[0],candidate=(await readReleaseOwners({ownerRoot:candidateRoot,closureOptions})).owners[0];if(candidate.schemaVersion!==1)throw Error('Candidate must remain a full schema-1 release');
 const allowed=new Set(roots);for(const directory of assetDirectories){if(!safe(directory)||directory.includes('/')||['__proto__','constructor','prototype'].includes(directory))throw Error('Invalid asset directory');allowed.add(directory);}
 const groups=new Map(),local=[];
 for(const {ownerReleaseId,...f} of candidate.files.values()){const group=f.path.split('/')[0];if(!allowed.has(group)||generated.has(f.path)){local.push(f);continue;}if(!groups.has(group))groups.set(group,[]);groups.get(group).push(f);}
 const bundles=[...groups].map(([directory,files])=>{
  const matches=catalog.owners.map(owner=>{const changed=files.filter(f=>{const before=owner.files.get(f.path);return !before||before.sizeBytes!==f.sizeBytes||before.sha256!==f.sha256;}).map(f=>f.path);const ids=new Set(files.map(f=>owner.files.get(f.path)?.ownerReleaseId));return {owner,changed,canonical:changed.length===0&&ids.size===1?[...ids][0]:null};});
  // Select deterministically; one actual URL owner per whole directory, never a runtime chain.
  const match=matches.filter(m=>m.canonical).sort((a,b)=>a.canonical.localeCompare(b.canonical))[0],diagnostic=matches[0];
  return {directory,reusable:!!match,ownerReleaseId:match?.canonical||null,bytes:files.reduce((n,f)=>n+f.sizeBytes,0),changedPaths:match?[]:diagnostic.changed,reason:match?'identical-single-owner':diagnostic.changed.length?'changed-files':'mixed-canonical-owners',files:files.map(f=>({...f,...(match?{ownerReleaseId:match.canonical,ownerURL:`../${match.canonical}/${f.path}`}:{})}))};
 });
 const reusableBytes=bundles.filter(b=>b.reusable).reduce((n,b)=>n+b.bytes,0),minimumPayloadBytes=candidate.totalBytes-reusableBytes;
 return {schemaVersion:1,kind:'asset-reuse-feasibility-plan',deployable:false,ownerReleaseId:owner.releaseId,ownerReleaseIds:catalog.owners.map(o=>o.releaseId).sort(),canonicalOwnerReleaseIds:[...new Set(bundles.filter(b=>b.reusable).map(b=>b.ownerReleaseId))].sort(),candidateReleaseId:candidate.releaseId,ownerPrefix:`preview-b/releases/${owner.releaseId}/`,candidatePayloadBytes:candidate.totalBytes,reusableBytes,minimumPayloadBytes,publishedBytes,hostingLimitBytes,projectedPayloadOnlyBytes:publishedBytes===null?null:publishedBytes+minimumPayloadBytes,payloadOnlyFits:publishedBytes===null?null:publishedBytes+minimumPayloadBytes<=hostingLimitBytes,warning:'Not a sparse deployment manifest. No files may be omitted until runtime URL routing and a reference-aware deployment validator are implemented and browser-tested. Projection excludes changed routing bytes, new manifests, receipt and promotion files.',assetClosure:{owner:owner.assetClosure,candidate:candidate.assetClosure},localFiles:local,bundles};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const [ownerRoot,candidateRoot,published]=process.argv.slice(2);planReleaseAssetReuse({ownerRoot,candidateRoot,publishedBytes:published===undefined?null:Number(published)}).then(r=>console.log(JSON.stringify(r,null,2))).catch(e=>{console.error(e.message);process.exitCode=1;});
}

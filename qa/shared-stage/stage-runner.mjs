// Runner-only, read-only live checkout + separate artifact output. No git operations/promotion.
import fs from 'node:fs/promises';import path from 'node:path';import {pathToFileURL} from 'node:url';
const sourceRoot=path.resolve(process.env.SOURCE_ROOT),liveRoot=path.resolve(process.env.LIVE_ROOT),output=path.resolve(process.env.STAGE_ROOT);
const inventory=JSON.parse(await fs.readFile(process.env.LIVE_TREE_JSON,'utf8'));
const commit=JSON.parse(await fs.readFile(process.env.LIVE_COMMIT_JSON,'utf8'));
if(commit.sha!=='2a8748aeabc70e75f10f63fa644bcad9f315f26f'||!commit.tree?.sha||inventory.truncated||inventory.sha!==commit.tree.sha)throw Error('Pinned commit and its complete exact tree required');
const {buildAtelierRelease}=await import(pathToFileURL(path.join(sourceRoot,'scripts/build-atelier-release.mjs')));
const {buildSharedAtelierRelease}=await import(pathToFileURL(path.join(sourceRoot,'scripts/build-shared-atelier-release.mjs')));
await fs.mkdir(output,{recursive:true});
const full=await buildAtelierRelease({sourceRoot,outputRoot:path.join(output,'full'),publishedRootFiles:inventory.tree.filter(f=>f.type==='blob').map(f=>f.path),maxBytes:256*2**20});
const owner=path.join(liveRoot,'preview-b/releases/9c055e4777a79c7987dd6cd5ccabf9f189121fd6c64e2f54853aa694827add06');
const sparse=await buildSharedAtelierRelease({ownerRoot:owner,candidateRoot:full.releasePath,outputRoot:path.join(output,'shared'),assetDirectories:['leather-compat-r12','open-front-candidate']});
// Count every physical staged byte, not just payload receipt; refs already live.
async function bytes(root){let n=0;for(const e of await fs.readdir(root,{withFileTypes:true})){const p=path.join(root,e.name);if(e.isDirectory())n+=await bytes(p);else if(e.isFile())n+=(await fs.stat(p)).size;else throw Error('Unexpected artifact link');}return n;}
const currentBytes=inventory.tree.filter(f=>f.type==='blob').reduce((n,f)=>n+f.size,0),addedBytes=await bytes(sparse.releasePath),reservedPromotionBytes=65536;
const projectedBytes=currentBytes+addedBytes+reservedPromotionBytes;
if(addedBytes>8*2**20)throw Error(`Unexpected sparse growth: ${addedBytes}; investigate reuse before staging`);
if(projectedBytes>2**30)throw Error('Repository published-byte budget exceeded');
const compact={pinnedLiveCommit:commit.sha,pinnedLiveTree:inventory.sha,fullReleaseId:full.releaseId,fullPayloadBytes:full.totalBytes,sharedReleaseId:sparse.releaseId,localFileCount:sparse.files,referenceCount:sparse.references,reusedBytes:sparse.reusedBytes,currentBytes,addedBytes,reservedPromotionBytes,projectedBytes,headroomBytes:2**30-projectedBytes,status:'STAGED ONLY. No publication or entry-pointer changes.'};
await fs.writeFile(path.join(output,'stage-report.json'),JSON.stringify(compact,null,2));
// A runner-private pointer for additive overlay; never upload inventory/source mapping.
await fs.writeFile(path.join(output,'release-path.txt'),sparse.releasePath+'\n');
console.log(JSON.stringify(compact,null,2));

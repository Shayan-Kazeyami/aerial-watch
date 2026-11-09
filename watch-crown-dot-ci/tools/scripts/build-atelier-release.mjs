import {STRUCTURAL_SUPPORT_ASSET} from '../assembly-structural-support.js';
import {CASE_ASSETS,validateCaseAssetClosure} from './case-asset-closure.mjs';
import {readFile,writeFile,mkdir,mkdtemp,rm,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {stageRelease} from './stage-release.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
const safe=p=>typeof p==='string'&&/^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(p)&&p.split('/').every(x=>x!=='.'&&x!=='..');
const firstParty=p=>!p.includes('/')&&(/^(assembly-|material-review|studio-console|atelier-)/.test(p)||['index.html','integrated-preview.html','avif-detect.js','lining-fallback.js'].includes(p))&&/\.(js|css|html)$/.test(p)&&!p.includes('-r187');
// Explicit runtime assets: all face/leather variants and raw failure fallbacks.
// Future asset variants must be supplied through the extra manifest or this list.
export const R14_LEATHER_ASSETS=Object.freeze(['leather.gltf','geometry.bin','original-0.png','original-3.jpg','original-4.jpg','outer-color-2k.ktx2','outer-roughness-2k.ktx2','outer-normal-4k.chunks.json','outer-normal-4k.ktx2.part0','outer-normal-4k.ktx2.part1','thread-fiber-normal.png','thread-fiber-color.png'].map(name=>'leather-assets/r14/'+name));
export const R12_LEATHER_ASSETS=Object.freeze(['leather.gltf','geometry.bin','original-0.png','original-1.jpg','original-2.jpg','original-3.jpg','original-4.jpg','outer-color-2k.ktx2','outer-roughness-2k.ktx2','outer-normal-4k.chunks.json','outer-normal-4k.ktx2.part0','outer-normal-4k.ktx2.part1'].map(name=>'quality-study/leather-r12/'+name));
export const ATELIER_ASSETS=Object.freeze([
 ...R14_LEATHER_ASSETS,
 ...R12_LEATHER_ASSETS,
 'leather-assets/r14/outer-normal-2k.manifest.json','leather-assets/r14/normal-2048-existing-mips.ktx2',
 ...['leather-qa-avif-gentle.gltf','color-avif-crf12.avif','roughness-avif-crf12.avif','normal-avif-crf6.avif'].map(name=>'leather-assets/r14/'+name),
 ...['leather.gltf','geometry.bin','original-0.png','original-3.jpg','original-4.jpg','outer-color-2k.png','outer-roughness-2k.png'].map(name=>'leather-compat-r12/'+name),
 'assets/manual-a-parts.json','rebuild/assembly.glb','rebuild/assembly-report.json','aerial-assets/aerial-concept.png',
 'premium-face/face-b.glb','premium-face/face-svg-b.glb','premium-face/face-svg04.glb','premium-face/face-b-render.png','premium-face/face-b-render.webp',
 'open-front/open-front-plates.glb',STRUCTURAL_SUPPORT_ASSET,
 'quality-study/face-svg03-rim-candidate.glb','quality-study/form-legibility-r01.glb','quality-study/front-architecture-r07.glb','quality-study/open-front-plates.glb',
 'quality-study/leather-craft-r05.glb','quality-study/leather-craft-r09.glb','quality-study/leather-craft-r10.glb','quality-study/leather-craft-r11.glb',
 'quality-study/native-front.png','quality-study/native-front.webp','quality-study/native-r03-svg04-finish3-front.png',
 ...['01-front','02-three-quarter','03-interior','04-balance','05-train','06-leather'].flatMap(n=>['png','webp'].map(ext=>`quality-study/${n}.${ext}`)),
 'optimized-assets/rebuild__assembly.meshopt.glb.gz','optimized-assets/premium-face__face-svg04.meshopt.glb','optimized-assets/quality-study__leather-craft-r11.meshopt.glb',
 'optimized-assets/README.md','optimized-assets/audit.json','ATTRIBUTION.md','docs/OM10_Release_notes.pdf','docs/OM10_Technical_Information_20210314.pdf',
]);
async function checkedRead(root,name){if(!safe(name))throw Error(`Unsafe path: ${name}`);let cursor;
 const absolute=path.resolve(root,name);cursor=path.parse(absolute).root;
 for(const part of absolute.split(path.sep).filter(Boolean)){cursor=path.join(cursor,part);if((await lstat(cursor)).isSymbolicLink())throw Error(`Symlink rejected: ${cursor}`);}
 if(!(await lstat(absolute)).isFile())throw Error(`Not a regular file: ${name}`);return readFile(absolute);}
function identities(manifest){if(manifest.schemaVersion!==1||!Array.isArray(manifest.files))throw Error('Invalid asset manifest');const map=new Map();for(const e of manifest.files){if(!safe(e.path)||map.has(e.path)||!Number.isSafeInteger(e.sizeBytes)||e.sizeBytes<0||!/^[a-f0-9]{64}$/.test(e.sha256))throw Error('Invalid asset identity');map.set(e.path,e);}return map;}
export const CHUNKED_TEXTURES=Object.freeze([Object.freeze({manifestPath:'quality-study/leather-r12/outer-normal-4k.chunks.json',texturePath:'quality-study/leather-r12/outer-normal-4k.ktx2',bytes:15802166,sha256:'8c58f1bb4e819069ba951c3cb659ceacd44c3474c14b68a0f747186e121af2f2'}),Object.freeze({manifestPath:'leather-assets/r14/outer-normal-4k.chunks.json',texturePath:'leather-assets/r14/outer-normal-4k.ktx2',bytes:16562348,sha256:'bb022255b999645d468cc2b62100cef7c4226c3df136ab1732b40c107655d585'})]);
/** Proves glTF real-resource closure and audited virtual KTX2 reassembly. */
export function validateAssetClosure(buffers,{chunkedTextures=CHUNKED_TEXTURES,partitionOnly=false}={}){
 const caseClosure=partitionOnly?null:validateCaseAssetClosure(buffers);
 const virtual=new Map(),policies=new Map(chunkedTextures.map(p=>[p.manifestPath,p]));let gltfCount=0,realReferences=0;
 const resource=(from,uri)=>{if(!safe(uri))throw Error(`Unsafe glTF/chunk URI: ${from} -> ${uri}`);return path.posix.join(path.posix.dirname(from),uri);};
 for(const [name,encoded] of buffers)if(name.endsWith('.chunks.json')){
  const policy=policies.get(name);if(!policy)throw Error(`Unapproved chunk manifest: ${name}`);
  if(encoded.length>65536)throw Error(`Chunk manifest too large: ${name}`);
  const m=JSON.parse(encoded.toString());if(m.version!==1||m.bytes!==policy.bytes||m.sha256!==policy.sha256||!Array.isArray(m.chunks)||!m.chunks.length||m.chunks.length>32)throw Error(`Chunk manifest identity mismatch: ${name}`);
  const target=resource(name,m.texture);if(target!==policy.texturePath||virtual.has(target)||buffers.has(target))throw Error(`Ambiguous virtual texture: ${target}`);
  const seen=new Set(),digest=createHash('sha256');let total=0,magic=[];
  for(const c of m.chunks){const part=resource(name,c.uri);if(seen.has(part)||!Number.isSafeInteger(c.bytes)||c.bytes<=0||c.bytes>8*1024*1024)throw Error(`Invalid chunk: ${part}`);seen.add(part);const b=buffers.get(part);if(!b||b.length!==c.bytes)throw Error(`Missing/wrong-size chunk: ${part}`);digest.update(b);total+=b.length;for(let i=0;i<b.length&&magic.length<12;i++)magic.push(b[i]);}
  if(total!==policy.bytes||digest.digest('hex')!==policy.sha256)throw Error(`Reassembled chunk identity mismatch: ${target}`);
  if(JSON.stringify(magic)!==JSON.stringify([171,75,84,88,32,50,48,187,13,10,26,10]))throw Error(`Virtual texture is not KTX2: ${target}`);
  virtual.set(target,{bytes:total,sha256:policy.sha256});
 }
 for(const [name,b] of buffers){let doc;if(name.endsWith('.gltf'))doc=JSON.parse(b.toString());else if(name.endsWith('.glb')&&b.length>=20&&b.readUInt32LE(0)===0x46546c67){const n=b.readUInt32LE(12);if(n> b.length-20||b.readUInt32LE(16)!==0x4e4f534a)throw Error(`Invalid GLB JSON chunk: ${name}`);doc=JSON.parse(b.subarray(20,20+n).toString());}else continue;
  gltfCount++;for(const [kind,items] of [['buffer',doc.buffers||[]],['image',doc.images||[]]])for(const item of items){if(item.uri===undefined)continue;if(typeof item.uri!=='string')throw Error(`Invalid glTF URI: ${name}`);if(item.uri.startsWith('data:'))continue;const target=resource(name,item.uri),bytes=buffers.get(target),v=virtual.get(target);
   if(!bytes&&!v)throw Error(`Unpackaged glTF ${kind}: ${name} -> ${target}`);
   if(v&&kind!=='image')throw Error(`Virtual texture cannot replace glTF buffer: ${target}`);
   if(kind==='buffer'&&(!Number.isSafeInteger(item.byteLength)||item.byteLength<0||bytes.length!==item.byteLength))throw Error(`glTF buffer length mismatch: ${target}`);realReferences+=bytes?1:0;
  }
 }
 return {gltfCount,realReferences,virtualTextures:[...virtual].map(([path,identity])=>({path,...identity}))};
}
export function redirectScript(targets){return `// Build-only whitelisted historical navigation; never accepts a URL parameter.\nconst targets=Object.freeze(${JSON.stringify(targets)});\nconst name=location.pathname.split('/').pop()||'index.html';\nif(!Object.hasOwn(targets,name))throw new Error('Unknown release redirect');\nconst target=new URL(targets[name],import.meta.url);\ntarget.search=location.search;target.hash=location.hash;location.replace(target.href);\n`;}
function wrapper(target){return `<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aerial studio</title><script type="module" src="./release-redirect.js"></script></head><body><p>Opening the requested Aerial page…</p><noscript><a href="${target}">Continue to Aerial</a></noscript></body></html>\n`;}
/** Local build only. publishedRootFiles must come from the actual published tree. */
export async function buildAtelierRelease({sourceRoot,outputRoot,publishedRootFiles,extraAssetsManifest=null,assets=ATELIER_ASSETS,maxBytes=180*2**20}={}){
 if(!sourceRoot||!outputRoot||!Array.isArray(publishedRootFiles)||!Number.isSafeInteger(maxBytes)||maxBytes<=0)throw Error('Source, output, published-root inventory and positive byte budget required');
 const manifestBytes=await checkedRead(sourceRoot,'deployment-manifest.json');const sources=identities(JSON.parse(manifestBytes));
 if(extraAssetsManifest){for(const [p,e] of identities(extraAssetsManifest)){if(['deployment-manifest.json','release-receipt.json','lean-release-build.json','release-redirect.js','quality-study/viewer-revision.js','quality-study/viewer-revision.json'].includes(p))throw Error(`Reserved generated path: ${p}`);if(sources.has(p)&&['path','sizeBytes','sha256'].some(k=>sources.get(p)[k]!==e[k]))throw Error(`Conflicting extra identity: ${p}`);sources.set(p,e);}}
 const selected=new Set([...sources.keys()].filter(p=>firstParty(p)||p.startsWith('vendor/')));
 for(const p of assets)selected.add(p);if(sources.has('assembly-case-combined-data.js'))for(const p of CASE_ASSETS)selected.add(p);for(const e of extraAssetsManifest?.files||[])selected.add(e.path);
 for(const p of ['atelier-preview.html','atelier-preview.js','material-review.html','index.html'])if(!selected.has(p))throw Error(`Missing required viewer entry: ${p}`);
 const buffers=new Map(),inputFiles=[];for(const p of [...selected].sort()){
  const e=sources.get(p);if(!e)throw Error(`Required asset absent from source/extra manifest: ${p}`);const b=await checkedRead(sourceRoot,p);if(b.length!==e.sizeBytes||sha(b)!==e.sha256)throw Error(`Source identity mismatch: ${p}`);buffers.set(p,b);inputFiles.push(e);
 }
 const targets={};for(const p of selected){if(!p.endsWith('.html')||['atelier-preview.html','material-review.html'].includes(p))continue;if(p.includes('/'))throw Error(`Unexpected HTML extra: ${p}`);
  if(p==='index.html')targets[p]='./atelier-preview.html';else{if(publishedRootFiles.includes(`preview-b/${p}`))targets[p]=`../../${p}`;else if(publishedRootFiles.includes(p))targets[p]=`../../../${p}`;else throw Error(`Historical target not verified in published inventory: ${p}`);}buffers.set(p,Buffer.from(wrapper(targets[p])));
 }
 buffers.set('release-redirect.js',Buffer.from(redirectScript(targets)));
 // Fail closed on common runtime literals and actual entry src/href. This is a
 // dependency assertion, not a JS rewriter/parser; computed loaders need explicit assets.
 const missing=new Set();const check=(from,spec)=>{const clean=spec.split(/[?#]/)[0];if(!clean||/^(https?:|data:|blob:)/.test(clean))return;let p=clean==='three'?'vendor/three.module.js':clean.startsWith('three/addons/')?'vendor/'+clean.slice(13):path.posix.normalize(path.posix.join(path.posix.dirname(from),clean));if(p==='.'||p==='./')p='index.html';if(!buffers.has(p)&&!['quality-study/viewer-revision.js','quality-study/viewer-revision.json'].includes(p))missing.add(`${from} -> ${p}`);};
 for(const [p,b] of buffers){if(p.startsWith('vendor/'))continue;const s=b.toString();if(/\.(js|mjs)$/.test(p)&&p!=='release-redirect.js'){
   for(const m of s.matchAll(/(?:from\s*|import\s*\(\s*)['"]([^'"\n]+)['"]/g))check(p,m[1]);
   for(const m of s.matchAll(/['"]((?:open-front(?:-candidate)?|quality-study|premium-face|rebuild|optimized-assets|assets|leather-assets|leather-compat-r12)\/[A-Za-z0-9_./-]+\.(?:glb(?:\.gz)?|gltf|bin|ktx2(?:\.part[0-9]+)?|png|webp|jpg|avif|json)(?:\?[^'"\s]*)?)['"]/g))check(p,m[1]);
  }if(['atelier-preview.html','material-review.html'].includes(p))for(const m of s.matchAll(/(?:href|src|srcset)=["']([^"']+)["']/g))check(p,m[1]);
 }
 const assetClosure=validateAssetClosure(buffers);
 if(missing.size)throw Error(`Unpackaged runtime references:\n${[...missing].join('\n')}`);
 const provenanceFiles=[...buffers].filter(([p])=>firstParty(p)||p==='release-redirect.js').sort(([a],[b])=>a<b?-1:a>b?1:0).map(([p,b])=>({path:p,bytes:b.length,sha256:sha(b)}));
 const revision={schemaVersion:1,algorithm:'SHA-256',scope:'Build-transformed first-party viewer JS, CSS and HTML including historical redirect wrappers; excludes vendor dependencies, models and rendered images.',canonicalization:'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.',digest:sha(JSON.stringify(provenanceFiles)),files:provenanceFiles};
 buffers.set('quality-study/viewer-revision.json',Buffer.from(JSON.stringify(revision,null,2)+'\n'));buffers.set('quality-study/viewer-revision.js',Buffer.from('// Generated for immutable lean release; source tree unchanged.\nexport default '+JSON.stringify(revision)+';\n'));
 buffers.set('lean-release-build.json',Buffer.from(JSON.stringify({schemaVersion:1,sourceManifestSHA256:sha(manifestBytes),inputFiles,assetClosure,redirectTargets:targets,layout:'preview-b/releases/<id>/; ../../ resolves to preserved preview-b, ../../../ to repository root',limitation:'Server-byte identities, not executed-runtime attestation.'},null,2)+'\n'));
 const files=[...buffers].sort(([a],[b])=>a<b?-1:a>b?1:0).map(([p,b])=>({path:p,sizeBytes:b.length,sha256:sha(b)}));const totalBytes=files.reduce((n,f)=>n+f.sizeBytes,0);if(totalBytes>maxBytes)throw Error(`Release exceeds byte budget: ${totalBytes} > ${maxBytes}`);
 const prepared=await mkdtemp(path.join(tmpdir(),'atelier-lean-build-'));try{for(const [p,b] of buffers){await mkdir(path.dirname(path.join(prepared,p)),{recursive:true});await writeFile(path.join(prepared,p),b);}await writeFile(path.join(prepared,'deployment-manifest.json'),JSON.stringify({schemaVersion:1,files},null,2)+'\n');return {...await stageRelease({sourceRoot:prepared,outputRoot,entry:'atelier-preview.html'}),totalBytes,sourceFilesUnchanged:true};}finally{await rm(prepared,{recursive:true,force:true});}
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const [sourceRoot,outputRoot,inventoryPath,extraPath]=process.argv.slice(2);Promise.resolve().then(async()=>buildAtelierRelease({sourceRoot,outputRoot,publishedRootFiles:((inventory)=>Array.isArray(inventory)?inventory:inventory.files.map(f=>f.path))(JSON.parse(await readFile(inventoryPath,'utf8'))),extraAssetsManifest:extraPath?JSON.parse(await readFile(extraPath,'utf8')):null})).then(r=>console.log(JSON.stringify(r,null,2))).catch(e=>{console.error(e.message);process.exitCode=1;});
}

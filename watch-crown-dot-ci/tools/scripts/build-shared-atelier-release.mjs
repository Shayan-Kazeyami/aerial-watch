/** Experimental mixed-path release builder. Sealed inputs only; local staging only. */
import {readFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {planReleaseAssetReuse} from './plan-release-asset-reuse.mjs';
import {stageSharedRelease} from './stage-shared-release.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
function once(source,before,after,label){if(source.split(before).length!==2)throw Error(`Reviewed routing anchor changed: ${label}`);return source.replace(before,after);}
export function routeVendorImportMap(map,vendorRoot){
 if(!map?.imports||typeof map.imports!=='object')throw Error('Viewer import map required');
 const result={...map,imports:{...map.imports}};
 for(const [alias,file] of [['three/webgpu','three.webgpu.js'],['three/tsl','three.tsl.js']]){
  if(!Object.hasOwn(result.imports,alias))continue;
  if(result.imports[alias]!==`./vendor/${file}`)throw Error(`Reviewed node import alias changed: ${alias}`);
  result.imports[alias]=vendorRoot+file;
 }
 result.imports.three=vendorRoot+'three.module.js';result.imports['three/addons/']=vendorRoot;result.imports['./vendor/']=vendorRoot;
 return result;
}
export function routerSource(routes){return `// Generated immutable directory ownership; never reads URL parameters.\nconst routes=Object.freeze(${JSON.stringify(routes)});\nexport function assetBase(directory,fallback=import.meta.url){return Object.hasOwn(routes,directory)?new URL(routes[directory],import.meta.url).href:fallback;}\nexport function assetURL(value){if(typeof value!=='string')return value;const logical=value.replace(/^\\.\\//,'');const directory=logical.split('/')[0];if(!Object.hasOwn(routes,directory))return value;if(logical.split(/[?#]/)[0].split('/').some(p=>p==='..'||p==='.')||/[\\\\%:]/.test(logical))throw new Error('Unsafe logical asset URL');return new URL(logical,assetBase(directory)).href;}\n`;}
export async function buildSharedAtelierRelease({ownerRoot,ownerRoots=[],assetDirectories=[],candidateRoot,outputRoot}={}){
 const plan=await planReleaseAssetReuse({ownerRoot,ownerRoots,assetDirectories,candidateRoot}),references=plan.bundles.filter(b=>b.reusable).flatMap(b=>b.files.map(({ownerURL,...f})=>f)),omitted=new Set(references.map(f=>f.path));
 const manifest=JSON.parse(await readFile(path.join(candidateRoot,'deployment-manifest.json'),'utf8')),buffers=new Map();for(const f of manifest.files)if(!omitted.has(f.path)){const b=await readFile(path.join(candidateRoot,f.path));if(b.length!==f.sizeBytes||sha(b)!==f.sha256)throw Error(`Candidate changed during build: ${f.path}`);buffers.set(f.path,b);}
 if(buffers.has('assembly-asset-routing.js'))throw Error('Routing helper already exists; input must be unsplit schema-1 release');
 const routes=Object.fromEntries(plan.bundles.filter(b=>b.reusable).map(b=>[b.directory,`../${b.ownerReleaseId}/`]));
 buffers.set('assembly-asset-routing.js',Buffer.from(routerSource(routes)));
 const change=(name,edit)=>{if(!buffers.has(name))throw Error(`Required local module missing: ${name}`);buffers.set(name,Buffer.from(edit(buffers.get(name).toString())));};
 change('assembly-loading.js',s=>"import {assetURL} from './assembly-asset-routing.js';\n"+once(once(s,'export function loadGLTFAsset(url,options={}) {','export function loadGLTFAsset(url,options={}) {\n  url=assetURL(url);','GLTF entry'),'export function loadJSONAsset(url,{fetcher=fetch,...options}={}) {','export function loadJSONAsset(url,{fetcher=fetch,...options}={}) {\n  url=assetURL(url);','JSON entry'));
 change('assembly-ktx-leather.js',s=>"import {assetURL,assetBase} from './assembly-asset-routing.js';\n"+once(once(s,"new URL('./vendor/libs/basis/',import.meta.url).href","new URL(assetURL('./vendor/libs/basis/'),import.meta.url).href",'Basis path'),"withTexture({manager,baseURL,manifestURL:","withTexture({manager,baseURL:assetBase('quality-study',baseURL),manifestURL:",'KTX base'));
 // R14 has its own reviewed loader; old schema-1 releases without it remain valid.
 if(buffers.has('assembly-ktx-leather-r14.js'))change('assembly-ktx-leather-r14.js',s=>"import {assetURL,assetBase} from './assembly-asset-routing.js';\n"+once(once(s,"new URL('./vendor/libs/basis/',import.meta.url).href","new URL(assetURL('./vendor/libs/basis/'),import.meta.url).href",'R14 Basis path'),"withTexture({manager,baseURL,manifestURL:","withTexture({manager,baseURL:assetBase('leather-assets',baseURL),manifestURL:",'R14 KTX base'));
 if(buffers.has('assembly-case-combined-material.js'))change('assembly-case-combined-material.js',s=>"import {assetURL} from './assembly-asset-routing.js';\n"+once(s,"fetch(new URL(file,base),{signal})","fetch(new URL(assetURL('case-assets/'+file),new URL('../',base)),{signal})",'CASE texture namespace'));
 for(const name of ['atelier-preview.html','material-review.html'])change(name,s=>{
  let count=0;s=s.replace(/<script type="importmap">([^<]+)<\/script>/g,(_,json)=>{count++;let map=JSON.parse(json);if(routes.vendor)map=routeVendorImportMap(map,routes.vendor+'vendor/');return `<script type="importmap">${JSON.stringify(map)}</script>`;});if(count!==1)throw Error(`Exactly one import map required: ${name}`);
  const route=value=>{const logical=value.replace(/^\.\//,''),directory=logical.split('/')[0];return routes[directory]?routes[directory]+logical:value;};
  s=s.replace(/\b(href|src|poster)=(["'])([^"']+)\2/g,(all,attribute,quote,url)=>`${attribute}=${quote}${route(url)}${quote}`);
  return s.replace(/\bsrcset=(["'])([^"']+)\1/g,(all,quote,value)=>{if(value.includes('data:'))throw Error('Review data-URL srcset before shared build');const choices=value.split(',').map(choice=>{const parts=choice.trim().split(/\s+/);if(parts.length>2||parts[1]&&!/^(?:[0-9]+w|[0-9]+(?:\.[0-9]+)?x)$/.test(parts[1]))throw Error('Unsupported srcset syntax');parts[0]=route(parts[0]);return parts.join(' ');});return `srcset=${quote}${choices.join(', ')}${quote}`;});
 });
 // Current non-loader URL consumer: the Atelier's dynamically assigned static poster.
 // Match only static asset .src assignments; model constants and provenance stay logical/local.
 change('atelier-preview.js',s=>{let count=0;s=s.replace(/(\.src\s*=\s*)(['"])([A-Za-z0-9_.-]+\/[^'"\n]+)\2/g,(_,assignment,quote,url)=>{if(!Object.hasOwn(routes,url.split('/')[0]))return `${assignment}${quote}${url}${quote}`;count++;return `${assignment}sharedAssetURL(${quote}${url}${quote})`;});return count?"import {assetURL as sharedAssetURL} from './assembly-asset-routing.js';\n"+s:s;});
 // Explicit regression guard: asset-bearing CSS and additional raw fetch callers need review.
 for(const [name,b] of buffers){const s=b.toString();if(name.endsWith('.css')&&(/url\([^)]*(?:quality-study|premium-face|rebuild|assets|vendor)\//.test(s)||Object.keys(routes).some(directory=>s.includes(directory+'/')&&/url\(/.test(s))))throw Error(`Unreviewed CSS asset routing: ${name}`);}
 const provenanceFiles=[...buffers].filter(([p])=>!p.includes('/')&&/\.(js|css|html)$/.test(p)).sort(([a],[b])=>a<b?-1:a>b?1:0).map(([p,b])=>({path:p,bytes:b.length,sha256:sha(b)}));
 const revision={schemaVersion:1,algorithm:'SHA-256',scope:'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.',canonicalization:'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.',digest:sha(JSON.stringify(provenanceFiles)),files:provenanceFiles};
 buffers.set('quality-study/viewer-revision.json',Buffer.from(JSON.stringify(revision,null,2)+'\n'));buffers.set('quality-study/viewer-revision.js',Buffer.from('export default '+JSON.stringify(revision)+';\n'));
 buffers.set('shared-release-build.json',Buffer.from(JSON.stringify({schemaVersion:1,ownerReleaseId:plan.ownerReleaseId,ownerReleaseIds:plan.ownerReleaseIds,canonicalOwnerReleaseIds:plan.canonicalOwnerReleaseIds,sourceReleaseId:plan.candidateReleaseId,routes,reusedBytes:plan.reusableBytes,transforms:['central GLTF/JSON asset URLs','KTX chunk directory base','Basis transcoder URL','HTML assets/srcset, dynamic poster and vendor import maps','first-party provenance'],limitation:'Browser QA and complete published inventory budget required before promotion.'},null,2)+'\n'));
 return {...await stageSharedRelease({localBuffers:buffers,references,ownerRoot,ownerRoots,outputRoot}),reusedBytes:plan.reusableBytes};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){const [ownerRoot,candidateRoot,outputRoot,...extra]=process.argv.slice(2),ownerRoots=[],assetDirectories=[];for(let i=0;i<extra.length;i+=2){if(!extra[i+1]||!['--owner','--asset-dir'].includes(extra[i]))throw Error('Usage: OWNER CANDIDATE OUTPUT [--owner ROOT] [--asset-dir DIRECTORY]');(extra[i]==='--owner'?ownerRoots:assetDirectories).push(extra[i+1]);}buildSharedAtelierRelease({ownerRoot,ownerRoots,assetDirectories,candidateRoot,outputRoot}).then(r=>console.log(JSON.stringify(r,null,2))).catch(e=>{console.error(e.stack);process.exitCode=1;});}

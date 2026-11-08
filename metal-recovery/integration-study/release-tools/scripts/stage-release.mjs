import {readFile,writeFile,mkdir,lstat,realpath,copyFile,rename,readdir,rm} from 'node:fs/promises';
import {createHash,randomUUID} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const safe=value=>typeof value==='string'&&/^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(value)&&value.split('/').every(p=>p!=='.'&&p!=='..');
const inside=(root,target)=>target===root||target.startsWith(root+path.sep);
async function noLinks(filename){
 const absolute=path.resolve(filename),parts=absolute.split(path.sep).filter(Boolean);let cursor=path.parse(absolute).root;
 for(const part of parts){cursor=path.join(cursor,part);try{if((await lstat(cursor)).isSymbolicLink())throw new Error(`Symlink path rejected: ${cursor}`);}catch(error){if(error.code==='ENOENT')break;throw error;}}
}
async function bytesMatch(filename,entry){await noLinks(filename);const stat=await lstat(filename);if(!stat.isFile())throw new Error(`Not a regular file: ${entry.path}`);const bytes=await readFile(filename);if(bytes.length!==entry.sizeBytes||hash(bytes)!==entry.sha256)throw new Error(`Hash mismatch: ${entry.path}`);return bytes;}
async function treeFiles(root,prefix=''){const result=[];for(const entry of await readdir(path.join(root,prefix),{withFileTypes:true})){const name=prefix?`${prefix}/${entry.name}`:entry.name;if(entry.isSymbolicLink())throw new Error(`Symlink path rejected: ${name}`);if(entry.isDirectory())result.push(...await treeFiles(root,name));else if(entry.isFile())result.push(name);else throw new Error(`Non-regular staged entry: ${name}`);}return result.sort();}

/** Local packaging only. Never changes a public pointer or removes older releases. */
export async function stageRelease({sourceRoot,outputRoot,entry='atelier-preview.html'}={}){
 if(!sourceRoot||!outputRoot)throw new Error('sourceRoot and outputRoot are required.');
 if(!safe(entry)||!entry.endsWith('.html'))throw new Error('Unsafe entry path.');
 sourceRoot=path.resolve(sourceRoot);outputRoot=path.resolve(outputRoot);
 await noLinks(sourceRoot);await noLinks(outputRoot);sourceRoot=await realpath(sourceRoot);
 await noLinks(path.join(sourceRoot,'deployment-manifest.json'));
 const manifestBytes=await readFile(path.join(sourceRoot,'deployment-manifest.json'));
 const manifest=JSON.parse(manifestBytes);if(manifest.schemaVersion!==1||!Array.isArray(manifest.files)||!manifest.files.length)throw new Error('Invalid deployment manifest.');
 const seen=new Set();const files=manifest.files.map(item=>{
  if(!safe(item.path)||seen.has(item.path)||['deployment-manifest.json','release-receipt.json'].includes(item.path.split('/')[0])||!Number.isSafeInteger(item.sizeBytes)||item.sizeBytes<0||!/^[a-f0-9]{64}$/.test(item.sha256))throw new Error(`Unsafe or invalid manifest entry: ${item.path}`);
  seen.add(item.path);return {path:item.path,sizeBytes:item.sizeBytes,sha256:item.sha256};
 }).sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0);
 if(!seen.has(entry))throw new Error('Entry HTML is absent from manifest.');
 for(const file of files){const source=path.resolve(sourceRoot,file.path);if(!inside(sourceRoot,source))throw new Error('Source path escaped root.');await bytesMatch(source,file);}
 const id=hash(JSON.stringify(files));const releaseRoot=path.join(outputRoot,'releases');const destination=path.join(releaseRoot,id);
 // Metadata is supplemental, never part of the content ID input. Preserve the
 // supplied manifest exactly; an existing ID with changed metadata fails closed.
 const stagedManifest=manifestBytes;
 const receipt=Buffer.from(JSON.stringify({schemaVersion:1,releaseId:id,algorithm:'SHA-256',canonicalization:'SHA-256 of UTF-8 JSON.stringify(sorted {path,sizeBytes,sha256} identities)',fileCount:files.length,totalBytes:files.reduce((n,f)=>n+f.sizeBytes,0)},null,2)+'\n');
 const verify=async root=>{for(const f of files)await bytesMatch(path.join(root,f.path),f);for(const [name,bytes] of [['deployment-manifest.json',stagedManifest],['release-receipt.json',receipt]]){await noLinks(path.join(root,name));if(!(await readFile(path.join(root,name))).equals(bytes))throw new Error(`Existing release metadata differs: ${name}`);}const expected=[...files.map(f=>f.path),'deployment-manifest.json','release-receipt.json'].sort();if(JSON.stringify(await treeFiles(root))!==JSON.stringify(expected))throw new Error('Release contains unexpected files.');};
 await mkdir(releaseRoot,{recursive:true});await noLinks(releaseRoot);
 let existing=false;try{await lstat(destination);existing=true;}catch(error){if(error.code!=='ENOENT')throw error;}
 if(existing){await noLinks(destination);await verify(destination);}else{
  const temporary=path.join(releaseRoot,`.stage-${randomUUID()}`);await mkdir(temporary);
  try{for(const f of files){const target=path.join(temporary,f.path);await mkdir(path.dirname(target),{recursive:true});await noLinks(path.join(sourceRoot,f.path));await copyFile(path.join(sourceRoot,f.path),target);}
   await writeFile(path.join(temporary,'deployment-manifest.json'),stagedManifest);await writeFile(path.join(temporary,'release-receipt.json'),receipt);await verify(temporary);
   // Concurrent identical staging is harmless; conflicting bytes fail verification.
   try{await rename(temporary,destination);}catch(error){if(!['EEXIST','ENOTEMPTY'].includes(error.code))throw error;await verify(destination);await rm(temporary,{recursive:true});}
  }catch(error){await rm(temporary,{recursive:true,force:true});throw error;}
 }
 const candidate=path.join(outputRoot,'promotion-candidate',id);await noLinks(candidate);await mkdir(candidate,{recursive:true});
 const scriptName=`entry-${id}.js`;
 const script=`// Copy beside the stable entry only after publication approval.\nconst target=new URL(${JSON.stringify(`releases/${id}/${entry}`)},import.meta.url);\ntarget.search=location.search;\ntarget.hash=location.hash;\nlocation.replace(target.href);\n`;
 const html=`<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aerial studio</title><script type="module" src="./${scriptName}"></script></head><body><p>Opening the Aerial studio…</p><noscript>JavaScript is needed to open the interactive studio.</noscript></body></html>\n`;
 for(const [name,contents] of [['index.html',html],[scriptName,script]]){const filename=path.join(candidate,name);await noLinks(filename);try{await writeFile(filename,contents,{flag:'wx'});}catch(error){if(error.code!=='EEXIST')throw error;if(await readFile(filename,'utf8')!==contents)throw new Error(`Promotion candidate differs: ${name}`);}}
 return {releaseId:id,releasePath:destination,promotionCandidate:candidate,files:files.length};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const [sourceRoot,outputRoot,entry]=process.argv.slice(2);stageRelease({sourceRoot,outputRoot,entry}).then(result=>console.log(JSON.stringify(result,null,2))).catch(error=>{console.error(error.message);process.exitCode=1;});
}

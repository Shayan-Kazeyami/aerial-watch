import {readFile,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root=fileURLToPath(new URL('../',import.meta.url));
async function javascriptFiles(directory){
 const files=[];
 for(const entry of await readdir(directory,{withFileTypes:true})){
  if(entry.name==='.git'||entry.name==='node_modules')continue;
  const filename=path.join(directory,entry.name);
  if(entry.isDirectory())files.push(...await javascriptFiles(filename));
  else if(entry.isFile()&&/\.m?js$/.test(entry.name))files.push(filename);
 }
 return files;
}
const files=await javascriptFiles(root);
for(const filename of files){
 const result=spawnSync(process.execPath,['--check',filename],{stdio:'inherit'});
 if(result.error)throw result.error;
 if(result.status!==0)throw new Error(`Syntax check failed: ${path.relative(root,filename)}`);
}
console.log(`Syntax verified: ${files.length} JavaScript files.`);
const manifest=JSON.parse(await readFile(path.join(root,'deployment-manifest.json'),'utf8'));
const seen=new Set();
for(const entry of manifest.files){
 if(seen.has(entry.path))throw new Error(`Duplicate manifest path: ${entry.path}`);
 seen.add(entry.path);
 const bytes=await readFile(path.join(root,entry.path));
 const hash=createHash('sha256').update(bytes).digest('hex');
 if(bytes.length!==entry.sizeBytes||hash!==entry.sha256)throw new Error(`Manifest mismatch: ${entry.path}`);
}
console.log(`Manifest verified: ${manifest.files.length} files.`);

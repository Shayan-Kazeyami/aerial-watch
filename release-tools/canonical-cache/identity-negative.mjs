import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';import {pathToFileURL} from 'node:url';import {verifyIdentity} from './identity-gate.mjs';
const modulePath=path.resolve(process.argv[2]);const {CANONICAL_ASSET_OWNERS:owners}=await import(pathToFileURL(modulePath));const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'owner-gate-'));
try {
 const options={modulePath,baseline:path.join(tmp,'baseline'),overlay:path.join(tmp,'overlay'),releases:path.join(tmp,'releases'),manifest:{localFiles:[],references:[]}};
 const binding=(name,bytes)=>({path:name,sizeBytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
 for(const [name,owner] of Object.entries(owners)) {
  const bytes=Buffer.from('original fixture bytes'),entry=binding(name,bytes);options.manifest.localFiles.push(entry);options.manifest.references.push({...entry,ownerReleaseId:owner});
  for(const base of [options.baseline,path.join(options.releases,owner)]){const f=path.join(base,name);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,bytes);}
 }
 assert.equal(await verifyIdentity(options),4);
 const name=Object.keys(owners)[0],bytes=Buffer.from('changed geometry fixture');const f=path.join(options.overlay,name);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,bytes);
 Object.assign(options.manifest.localFiles[0],binding(name,bytes));Object.assign(options.manifest.references[0],binding(name,bytes));
 await assert.rejects(()=>verifyIdentity(options),/Canonical byte/);
 console.log('Coordinated intended-byte and both-metadata mutation rejected against retained owner');
} finally {fs.rmSync(tmp,{recursive:true,force:true});}

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
export async function verifyIdentity({manifest,modulePath,overlay,baseline,releases}) {
 const mod=await import(pathToFileURL(path.resolve(modulePath)));
 mod.assertCanonicalAssetOwners(manifest);
 for(const [name,owner]of Object.entries(mod.CANONICAL_ASSET_OWNERS)) {
  assert(/^[a-f0-9]{64}$/.test(owner),'Unsafe owner');
  assert(!name.split('/').some(x=>x==='..'||x==='.'),'Unsafe asset path');
  const expected=manifest.localFiles.find(x=>x.path===name);
  const staged=path.join(overlay,name),intended=fs.existsSync(staged)?staged:path.join(baseline,name);
  for(const file of [intended,path.join(releases,owner,name)]) {
   const bytes=fs.readFileSync(file);
   assert.equal(bytes.length,expected.sizeBytes,`Canonical byte size mismatch: ${file}`);
   assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),expected.sha256,`Canonical byte digest mismatch: ${file}`);
  }
 }
 return Object.keys(mod.CANONICAL_ASSET_OWNERS).length;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) {
 const [manifestPath,modulePath,overlay,baseline,releases]=process.argv.slice(2);
 const count=await verifyIdentity({manifest:JSON.parse(fs.readFileSync(manifestPath)),modulePath,overlay,baseline,releases});
 console.log(`Verified ${count} intended/current/owner byte identities before seal`);
}

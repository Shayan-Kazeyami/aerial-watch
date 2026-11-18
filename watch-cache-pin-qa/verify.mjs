import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';import {pathToFileURL} from 'node:url';
const rid=process.argv[2],root=path.resolve('preview-b/releases'),dir=path.join(root,rid),m=JSON.parse(fs.readFileSync(path.join(dir,'deployment-manifest.json'))),mod=await import(pathToFileURL(path.join(dir,'assembly-asset-routing.js')));
assert.equal(mod.assertCanonicalAssetOwners(m),4);let tests=1;
for(const [name,owner]of Object.entries(mod.CANONICAL_ASSET_OWNERS)){
 const intended=m.localFiles.find(x=>x.path===name),ref=m.references.find(x=>x.path===name&&x.ownerReleaseId===owner);assert(ref);for(const base of [dir,path.join(root,owner)]){const b=fs.readFileSync(path.join(base,name));assert.equal(b.length,intended.sizeBytes);assert.equal(crypto.createHash('sha256').update(b).digest('hex'),intended.sha256);}
 assert.equal(mod.assetURL(name+'?proof=1#x'),pathToFileURL(path.join(root,owner,name)).href+'?proof=1#x');
 const bad=structuredClone(m);bad.localFiles.find(x=>x.path===name).sha256='f'.repeat(64);assert.throws(()=>mod.assertCanonicalAssetOwners(bad),/differs from intended/);tests++;
 const missing=structuredClone(m);missing.references=missing.references.filter(x=>!(x.path===name&&x.ownerReleaseId===owner));assert.throws(()=>mod.assertCanonicalAssetOwners(missing),/differs from intended/);tests++;
}
assert.throws(()=>mod.assetURL('optimized-assets/../secret'),/Unsafe/);assert.equal(mod.assetURL('leather-assets/r14/geometry.bin'),'leather-assets/r14/geometry.bin');console.log(JSON.stringify({passed:true,tests:tests+2,bindings:4,scope:'intended-current / declared-owner / both actual bytes equal; stale and absent owner rejected; URLs retain suffixes; leather untouched'}));

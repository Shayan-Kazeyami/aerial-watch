import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import boot from '../quality-study/viewer-revision.js';
const sha=b=>createHash('sha256').update(b).digest('hex');
test('capture revision metadata matches current served source bytes',async()=>{
 const revision=JSON.parse(await readFile(new URL('../quality-study/viewer-revision.json',import.meta.url),'utf8'));
 assert.deepEqual(boot,revision);assert.equal(sha(JSON.stringify(revision.files)),revision.digest);
 for(const entry of revision.files){const bytes=await readFile(new URL('../'+entry.path,import.meta.url));assert.equal(bytes.length,entry.bytes,entry.path);assert.equal(sha(bytes),entry.sha256,entry.path);}
 for(const path of ['assembly-image-export.js','assembly-premium-face.js','studio-console.js','integrated-preview.html'])assert(revision.files.some(f=>f.path===path));
});

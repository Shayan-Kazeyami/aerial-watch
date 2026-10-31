import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const read=name=>readFile(new URL('../'+name,import.meta.url),'utf8');
test('integrated candidate preserves every runtime control ID exactly once',async()=>{
 const baseline=await read('index.html'),candidate=await read('integrated-preview.html');
 const ids=html=>[...html.matchAll(/\bid=["']([^"']+)["']/g)].map(m=>m[1]);
 const old=ids(baseline),next=ids(candidate);
 for(const id of old)assert.equal(next.filter(n=>n===id).length,1,`missing or duplicate ${id}`);
});
test('candidate exposes its camera actions and does not change the production entry',async()=>{
 const candidate=await read('integrated-preview.html'),baseline=await read('index.html');
 assert.match(candidate,/studio-console\.js/);assert.match(candidate,/studio-console\.css/);
 assert.doesNotMatch(baseline,/studio-console/);
 const controls=candidate.split('id="showcase-controls"')[1].split('</aside>')[0];
 assert.doesNotMatch(controls,/<details\b/);
 const views=html=>[...html.matchAll(/data-view=["']([^"']+)["']/g)].map(m=>m[1]).sort();
 assert.deepEqual(views(candidate),views(baseline));
});
test('power-path control remains outside the duplicate interior guide',async()=>{
 const html=await read('integrated-preview.html');
 const guide=html.slice(html.indexOf('id="interior-guide"'),html.indexOf('id="inspection-details"'));
 assert(!guide.includes('id="power-path"'));
 assert.equal((html.match(/id="power-path"/g)||[]).length,1);
 assert(html.indexOf('id="power-path"')<html.indexOf('id="interior-guide"'));
});
test('premium poster has a lightweight WebP source and original PNG fallback',async()=>{
 const html=await read('integrated-preview.html');
 assert.match(html,/<source type="image\/webp" srcset="premium-face\/face-b-render.webp"\/>/);
 assert.match(html,/<img[^>]+src="premium-face\/face-b-render.png"/);
 const bytes=await readFile(new URL('../premium-face/face-b-render.webp',import.meta.url));
 assert.equal(bytes.toString('ascii',0,4),'RIFF');assert.equal(bytes.toString('ascii',8,12),'WEBP');
 assert(bytes.length<150000);
});

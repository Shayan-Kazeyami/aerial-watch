import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../assembly-review.js',import.meta.url),'utf8');
test('premium hand clearance is reversible and tied to the visible premium face',()=>{
 assert.match(source,/const premium=premiumActive\(\);\s*handClearance\?\.setEnabled\(premium\);/);
 assert.match(source,/if\(premiumRequested\)\{handClearance=createHandClearance\(exterior\);resources\.own\('premium seconds hand clearance',\(\)=>handClearance\.dispose\(\)\);\}/);
 assert.match(source,/handClearance:\{enabled:!!handClearance\?\.enabled,\.\.\.PREMIUM_HAND_CLEARANCE\}/);
});
test('compact crown capture metadata follows its actual non-premium display condition',()=>{
 assert.match(source,/crownVisual\?\.setEnabled\(active\)/);
 assert.match(source,/const active=openFrontActive\(\)&&!premium/);
 assert.match(source,/compactCrown:!!crownVisual&&openFrontActive\(\)&&!premiumActive\(\)/);
});

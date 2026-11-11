import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dirname,join} from 'node:path';
const root=dirname(process.env.AERIAL_RUNTIME_TEST_PATH||'assembly-review.js');
const source=readFileSync(join(root,'assembly-framing.js'),'utf8');
const body=source.match(/export function isPanelOnlyResize\([^]*?\n}/)[0].replace('export ','');
const check=new Function(`${body};return isPanelOnlyResize;`)();
test('side-panel and bottom-sheet changes retain imported camera, viewport changes still refit',()=>{
 const base={width:640,viewportWidth:640,viewportHeight:480,panelOpen:false};
 const open={...base,width:316,panelOpen:true};
 assert.equal(check(base,open,true),true);assert.equal(check(open,base,true),true);
 assert.equal(check(open,{...open,width:340},true),true);
 assert.equal(check(base,{...base,panelOpen:true},true),true);
 assert.equal(check(open,{...open,viewportWidth:660},true),false);
 assert.equal(check(open,{...open,viewportHeight:700},true),false);
 assert.equal(check(base,{...base,width:316},true),false);
 assert.equal(check(base,open,false),false);assert.equal(check(null,open,true),false);
});

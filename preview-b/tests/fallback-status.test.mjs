import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
for(const name of ['index.html','assembly-review.html'])test(name+' failed startup clears all stale loading statuses',async()=>{
 const html=await readFile(new URL('../'+name,import.meta.url),'utf8');
 const body=html.match(/import\('\.\/assembly-review\.js'\)\.catch\(error => \{([\s\S]*?)\n\s*\}\);/)[1];
 const nodes=new Map();const document={getElementById:id=>{if(!nodes.has(id))nodes.set(id,{textContent:'Preparing the watch…',hidden:true,setAttribute(){}});return nodes.get(id);}};
 vm.runInNewContext(body,{document,error:new Error('WebGL unavailable'),console:{error(){}},location:{reload(){}}});
 for(const id of ['primary-motion-status','motion-status'])assert.match(nodes.get(id).textContent,/unavailable.*Reload/);
 assert.match(nodes.get('render-status').textContent,/unavailable/);assert.equal(nodes.get('retry').hidden,false);assert.equal(nodes.get('loading').hidden,false);
});
test('runtime renderer failure clears motion status and disables inspection',async()=>{
 const source=await readFile(new URL('../assembly-review.js',import.meta.url),'utf8');
 const body=source.match(/function fail\(message,error\) \{([\s\S]*?)\n\}/)[1];
 const nodes=new Map();const $=id=>{if(!nodes.has(id))nodes.set(id,{textContent:'Preparing',setAttribute(){}});return nodes.get(id);};
 vm.runInNewContext(body,{$,message:'Graphics lost',error:null,announce(){},console:{error(){}}});
 assert.match($('primary-motion-status').textContent,/unavailable/);assert.match($('motion-status').textContent,/unavailable/);assert.equal($('inspection-controls').disabled,true);
});

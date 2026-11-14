import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const q='watch-support-text-build/',rid=fs.readFileSync(q+'release-id.txt','utf8'),old='fa85a6e595b33a9bc9bfcf74d3fec624aa1ab29e4341496314de8aa981685edb';
const sources={'BASE_STATEMENT.txt':fs.readFileSync('watch-empty-search-build/staging/preview-b/releases/'+old+'/assembly-review.js','utf8'),'CANDIDATE_STATEMENT.txt':fs.readFileSync(q+'staging/preview-b/releases/'+rid+'/assembly-review.js','utf8')};
function extract(name){const s=sources[name];const lines=s.split('\n').filter(x=>x.includes("$('part-support').textContent") && x.includes("Original OM10 component"));assert.equal(lines.length,1);return lines[0];}
function run(name,data){const node={};vm.runInNewContext(extract(name),{$:id=>{assert.equal(id,'part-support');return node;},mesh:{userData:data}});return node.textContent;}
const cases=[{}, {support:''},{support:null},{support:undefined},{support:'Upper bridge'},{support:'Plate & bridge'},{support:'輪列'}, {support:'<untrusted>'}];
for(const c of cases){const a=run('BASE_STATEMENT.txt',c),b=run('CANDIDATE_STATEMENT.txt',c);assert.equal(b,a.replace('â€”','—'));if(c.support)assert.equal(b,'Attachment: '+c.support);else assert.equal(b,'Original OM10 component — original placement preserved');}
console.log('PASS 8 actual detail-statement cases; fallback text repaired, attachment paths unchanged; textContent remains safe.');

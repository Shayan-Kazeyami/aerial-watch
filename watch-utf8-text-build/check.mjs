import fs from 'node:fs';import assert from 'node:assert/strict';import vm from 'node:vm';
const base=fs.readFileSync(new URL('../watch-explorer-label-build/staging/preview-b/releases/94ad3066d775ac9b39dd95a4c52a70388d86df29e327e556edfeee0328624817/assembly-review.js',import.meta.url),'utf8'),candidate=fs.readFileSync(new URL('./staging/preview-b/releases/48438e79481a6258e2ae563e943d25a516c2e5a515f15a6335bdb08197ca752d/assembly-review.js',import.meta.url),'utf8');
const pairs=[['Â·','·',10],['â€¦','…',2],['â†’','→',6],['Ã—','×',1]];let expected=base;for(const[a,b,n]of pairs){assert.equal(base.split(a).length-1,n);expected=expected.replaceAll(a,b);assert(!candidate.includes(a));}assert.equal(expected,candidate);
const old=base.split('\n'),lines=candidate.split('\n');assert.equal(lines.length,old.length);assert.deepEqual(lines.flatMap((s,i)=>s===old[i]?[]:[i+1]),[495, 505, 560, 650, 663, 736, 1026, 1076, 1234, 1251, 1256, 1356]);
const tests=[
[377,{'profile':{label:'Studio'}},'Studio · measuring playback…'],
[495,{shot:{index:1,count:6,view:'showcase'}},'2 / 6 · Studio'],
[505,{powerPath:true},'Barrel → wheel train → escapement → balance. Highlights identify original source parts; bridges and bearings remain in place.'],
[650,{pulled:true,running:false},'Time setting · turn the crown'],
[663,{state:{pulled:true}},'Pulled · turn to set time'],
[663,{state:{pulled:false}},'Seated · turn crown'],
[736,{$:id=>({checked:id==='animate'})},'Mechanism paused · Hands running'],
[1251,{powerPath:true},'Barrel → wheel train → escapement → balance. Original source parts highlighted.'],
[1356,{backendIdentity:{actual:'WebGL',fallbackReason:null},qualityProfiles:{studio:{label:'Studio'}},quality:'studio',running:false},'WebGL · Studio · still view, renders on change'],
[1356,{backendIdentity:{actual:'WebGL',fallbackReason:'test'},qualityProfiles:{studio:{label:'Studio'}},quality:'studio',running:true,rate:60},'WebGL (fallback) · Studio · 60 fps']
];for(const[n,ctx,want]of tests){const exp=lines[n-1].split('.textContent')[1].replace(/^\s*=\s*/,'').replace(/;\s*$/,'');assert.equal(vm.runInNewContext(exp,ctx),want);}
assert(candidate.includes("announce('Preparing PNG image…')"));assert(candidate.includes("textContent='Lighting the watch studio…'"));assert(candidate.includes('`${config.clock.speed}× · saved time scale`'));console.log('PASS:19 exact replacements/12 UI lines;10 VM expression cases;loading,PNG and saved-speed literals preserved;all remaining source bytes identical');

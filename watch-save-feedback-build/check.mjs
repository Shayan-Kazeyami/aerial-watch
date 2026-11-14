import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const q='watch-save-feedback-build/',rid=fs.readFileSync(q+'release-id.txt','utf8'),old='5af481a243687d5d809267eb8912a8cdbfd859f6b7daf2e00b60164da12406c2';
const sources={'BASE_HANDLER.txt':fs.readFileSync('watch-support-text-build/staging/preview-b/releases/'+old+'/assembly-review.js','utf8'),'CANDIDATE_HANDLER.txt':fs.readFileSync(q+'staging/preview-b/releases/'+rid+'/assembly-review.js','utf8')};
function extract(file){const s=sources[file],start=s.indexOf("if($('export-config'))$('export-config').onclick=async()=>{");assert.ok(start>=0);const end=s.indexOf('\n};',start);assert.ok(end>start);return s.slice(start,end+3);}
async function run(file,options={}){
 const node={},announcements=[],downloads=[],pending=new Set(options.pending?['export-config']:[]);
 const crown={active:!!options.active},lifecycle={disposed:!!options.disposed};let resolves=0,captures=0;
 const context={$:()=>node,crownInteraction:crown,crownVisual:{active:!!options.visualActive},pendingCaptures:pending,lifecycle,
 captureProvenance:{async resolve(){resolves++;if(options.resolveError)throw Error('provenance unavailable');if(options.becomesActive)crown.active=true;}},
 captureConfiguration(){captures++;return{schema:1,clock:{time:123}};},
 downloadBlob(blob,name){if(options.downloadError)throw Error('download blocked');downloads.push({blob,name});},
 announce(text){announcements.push(text);},Blob,JSON};
 vm.runInNewContext(extract(file),context);await node.onclick();
 return{announcements,downloads:await Promise.all(downloads.map(async d=>({name:d.name,type:d.blob.type,text:await d.blob.text()}))),pending:[...pending],resolves,captures};
}
const scenarios=[{}, {active:true},{visualActive:true},{pending:true},{disposed:true},{resolveError:true},{becomesActive:true},{downloadError:true}];
for(const options of scenarios){
 const base=await run('BASE_HANDLER.txt',options),candidate=await run('CANDIDATE_HANDLER.txt',options);
 assert.deepEqual(candidate.downloads,base.downloads);assert.deepEqual(candidate.pending,base.pending);assert.equal(candidate.resolves,base.resolves);assert.equal(candidate.captures,base.captures);
 if(base.downloads.length){assert.equal(base.announcements.length,0);assert.deepEqual(candidate.announcements,['View settings download requested. Check your browser downloads.']);}
 else assert.deepEqual(candidate.announcements,base.announcements);
}
console.log('PASS 8 async-handler scenarios; success requests announced once, errors/guards/JSON/downloads unchanged.');

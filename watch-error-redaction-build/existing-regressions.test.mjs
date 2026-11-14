import {test} from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {errorDetails,copyErrorDetails,sanitizeError} from './staging/preview-b/releases/3448182496cf6c2b906abe4b5a7128a9537ab745e8f992d4d55783fd389879e6/atelier-error-details.js';
import {createPresentationGate} from './staging/preview-b/releases/3448182496cf6c2b906abe4b5a7128a9537ab745e8f992d4d55783fd389879e6/assembly-presentation-gate.js';
test('initial asset failure visibly names the failed asset and sanitized cause',()=>{const gate=createPresentationGate({enabled:true});gate.settle('leather',new Error('Resource request failed (503).'));const details=errorDetails({state:gate.snapshot()});assert.match(details.summary,/Selected leather: Resource request failed \(503\)/);assert.equal(gate.snapshot().interactive,false);});
test('module and renderer failures report useful bounded cause',()=>{assert.match(errorDetails({error:new Error('WebGL context creation failed')}).summary,/3D runtime: WebGL context creation failed/);const gate=createPresentationGate({enabled:true});gate.fail('Rendering unavailable',new Error('Framebuffer incomplete'));assert.match(errorDetails({state:gate.snapshot()}).summary,/Framebuffer incomplete/);});
test('report excludes arbitrary query, secrets, source URLs and capability properties',()=>{const details=errorDetails({error:new Error('fetch https://example.org/file?token=secret failed api_key=secret'),search:'?face=svg04&leather=craft12&secret=hello&quality=arbitrary',source:'https://example.org/releases/'+'a'.repeat(64)+'/atelier-preview.js?secret=hi',capabilities:{webgl2ApiPresent:true,secureContext:true,vendor:'private GPU',secret:'hi'}});assert.doesNotMatch(details.text,/example.org|secret|private GPU|arbitrary|api_key/);assert.match(details.text,/svg04/);assert.match(details.text,/aaaaaaaa/);assert.equal(sanitizeError('<tag>\n'+'x'.repeat(500)).length,220);});
test('clipboard success copies once without fallback',async()=>{let calls=0;assert.equal(await copyErrorDetails('report',{clipboard:{writeText:async text=>{calls++;assert.equal(text,'report');}},showFallback:()=>assert.fail()}),true);assert.equal(calls,1);});
test('clipboard unavailable or denied exposes selectable diagnostic text',async()=>{for(const clipboard of [undefined,{writeText:async()=>{throw new Error('denied');}}]){let shown;assert.equal(await copyErrorDetails('report',{clipboard,showFallback:text=>shown=text}),false);assert.equal(shown,'report');}});
test('successful retry clears error report rather than retaining stale warning',()=>{const gate=createPresentationGate({enabled:true});for(const asset of ['baseline','proposal','premiumFace','leather'])gate.settle(asset,asset==='premiumFace'?new Error('503'):undefined);assert.ok(errorDetails({state:gate.snapshot()}));gate.retry('premiumFace');assert.equal(errorDetails({state:gate.snapshot()}),null);gate.settle('premiumFace');gate.rendered();assert.equal(errorDetails({state:gate.snapshot()}),null);});
test('error controls are attached to the cover outside disabled runtime controls',()=>{const shell=readFileSync(new URL('./staging/preview-b/releases/3448182496cf6c2b906abe4b5a7128a9537ab745e8f992d4d55783fd389879e6/atelier-preview.js',import.meta.url),'utf8');assert.match(shell,/\$\('studio-poster'\).append\(errorBox\)/);assert.match(shell,/errorText.readOnly=true/);assert.match(shell,/errorText.select\(\)/);assert.match(shell,/runtimeFailure=error/);assert.match(shell,/setAttribute\('aria-hidden',String\(!details\)\)/);});

const release='a'.repeat(64),owner='b'.repeat(64),origin='https://watch.example',prefix='/aerial-watch/preview-b/releases/';
const source=origin+prefix+release+'/atelier-preview.js';
test('failed same-origin module reports its path while stripping origin/query/fragment',()=>{
 const details=errorDetails({source,error:new Error('Failed to fetch dynamically imported module: '+origin+prefix+release+'/assembly-review.js?v=runtime&token=private#secret'),search:'?leather=craft14'});
 assert.match(details.summary,/assembly-review\.js/);assert.doesNotMatch(details.text,/watch\.example|private|secret|token|\?v=/);assert.equal(JSON.parse(details.text).options.leather,'craft14');
});
test('same-project immutable owner module remains identifiable',()=>{
 const summary=errorDetails({source,error:new Error('Import failed: '+origin+prefix+owner+'/vendor/postprocessing/GTAOPass.js?key=private')}).summary;
 assert(summary.includes(owner+'/vendor/postprocessing/GTAOPass.js'));assert(!summary.includes('private'));
});
test('external, credential-bearing, encoded, non-module and unrelated paths remain redacted',()=>{
 for(const url of ['https://external.example/file.js',origin.replace('https://','https://user:private@')+prefix+release+'/file.js',origin+prefix+release+'/token%2Fprivate.js',origin+'/private/module.js',origin+prefix+release+'/model.glb','blob:'+source,'data:text/javascript,private']){
  const value=sanitizeError('Import failed: '+url,{source});assert.equal(value,'Import failed: [resource]',url);
 }
});
test('warning diagnostics use the same safe module path policy',()=>{
 const report=errorDetails({source,state:{phase:'degraded',warnings:[{asset:'leather',message:'Failed module '+origin+prefix+release+'/assembly-ktx-leather-r14.js?token=private'}]}});
 assert.match(report.summary,/Selected leather: Failed module \[module/);assert.match(report.summary,/assembly-ktx-leather-r14\.js/);assert.doesNotMatch(report.text,/private|token|watch\.example/);
});

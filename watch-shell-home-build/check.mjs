import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const base='watch-import-readiness-build/staging/preview-b/releases/e157f07921363a07a67dffd367bbc5bec2392691313632a4169d951974abb5a2/';
const shell=fs.readFileSync(base+'atelier-preview.js','utf8'),review=fs.readFileSync(base+'assembly-review.js','utf8');
const old=shell.split('\n').find(x=>x.startsWith("document.addEventListener('keydown',e=>{if(e.key==='Escape'"));
const candidate=fs.readFileSync("watch-shell-home-build/staging/preview-b/releases/"+fs.readFileSync("watch-shell-home-build/release-id.txt","utf8")+"/atelier-preview.js","utf8").split("\n").find(x=>x.startsWith("document.addEventListener('keydown',e=>{if(e.key==='Escape'"));
const start=review.indexOf("renderer.domElement.addEventListener('keydown', event => {"),end=review.indexOf('\n// Project one known crown anchor',start);const canvas=review.slice(start,end);
function run(line,{tag='CANVAS',key='Home',mod='',prevented=false,canvasTarget=true,interior=false}={}){
 let canvasHandler,shellHandler,home=0,views=[],closed=0,stops=0;
 const c={document:{addEventListener(k,f){shellHandler=f}},renderer:{domElement:{addEventListener(k,f){canvasHandler=f}}},loading:false,failed:false,interiorView:interior,stopTour(){stops++},view(x){views.push(x)},closeContext(){closed++},$:id=>id==='movement-only'?{checked:false}:id==='context'?{hidden:false}:{click(){home++}},camera:{zoom:1,updateProjectionMatrix(){}},THREE:{MathUtils:{clamp:x=>x}},controls:{minZoom:.4,maxZoom:12},dirty:false};
 vm.createContext(c);vm.runInContext(canvas,c);vm.runInContext(line,c);
 const e={key,defaultPrevented:prevented,target:{tagName:tag,closest(){return null}},[mod]:true,preventDefault(){this.defaultPrevented=true},stopImmediatePropagation(){}};
 if(canvasTarget)canvasHandler(e);shellHandler(e);return{home,views,closed,stops,prevented:e.defaultPrevented};
}
let n=0;
for(const mod of ['ctrlKey','metaKey','altKey']){assert.equal(run(old,{mod}).home,1);const r=run(candidate,{mod});assert.equal(r.home,0);assert.equal(r.views.length,0);assert.equal(r.prevented,false);n++}
for(const interior of [false,true]){const a=run(old,{interior}),b=run(candidate,{interior});assert.equal(a.home,1);assert.equal(b.home,0);assert.deepEqual(b.views,[interior?'interior':'face']);n++}
assert.equal(run(candidate,{tag:'BUTTON',canvasTarget:false}).home,1);n++;
assert.equal(run(candidate,{tag:'BUTTON',canvasTarget:false,prevented:true}).home,0);n++;
for(const tag of ['INPUT','SELECT','TEXTAREA']){assert.equal(run(candidate,{tag,canvasTarget:false}).home,0);n++}
for(const key of ['Escape','x','+']){assert.deepEqual(run(old,{key}),run(candidate,{key}));n++}
console.log('PASS '+n+' extracted actual shell+canvas listener modeled propagation cases; modified Home preserved, canvas Home once, other controls unchanged.');

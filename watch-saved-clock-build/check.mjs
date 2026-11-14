import fs from 'node:fs';import assert from 'node:assert/strict';import vm from 'node:vm';
import {validateViewConfiguration as old} from './base.mjs';import {validateViewConfiguration as next} from './candidate.mjs';
const fixture=()=>({version:1,camera:{position:[0,0,50],target:[0,0,0],zoom:1},options:{openWork:true,finishes:true,crystals:true,movementOnly:false,quality:'detail'},clock:{mechanism:0,hands:0,speed:1}});
const escape=fs.readFileSync(new URL('../watch-canvas-shortcut-build/staging/preview-b/releases/9865b37ea1813c85badb404935f7710c688f04beef36da55d7d517ceef96b353/assembly-escapement.js',import.meta.url),'utf8');const guard=escape.match(/if\(!Number\.isFinite\(seconds\)\)fail\('finite seconds required'\);\s*const cycles=seconds\*3\.5,cycle=Math\.floor\(cycles\);\s*if\(!Number\.isSafeInteger\(cycle\)\)fail\('time exceeds safe cycle range'\);/)[0];
const downstream=seconds=>vm.runInNewContext(guard,{seconds,fail:m=>{throw Error(m)}});
let n=0;
for(const t of [1e308,Number.MAX_VALUE,Number.MAX_SAFE_INTEGER]){let f=fixture();f.clock.mechanism=t;old(f);assert.throws(()=>downstream(t));assert.throws(()=>next(f),/Invalid saved clock/);n++;}
for(const t of [0,.1,1,60,86400,31536000,1e12,Number.MAX_SAFE_INTEGER/7]){let f=fixture();f.clock.mechanism=t;assert.deepEqual(next(f),old(f));downstream(t);n++;}
for(const t of [Number.MAX_SAFE_INTEGER/3.5-1,Number.MAX_SAFE_INTEGER/3.5,Number.MAX_SAFE_INTEGER/3.5+1]){let f=fixture();f.clock.mechanism=t;const safe=Number.isSafeInteger(Math.floor(t*3.5));if(safe){next(f);downstream(t)}else{assert.throws(()=>next(f));assert.throws(()=>downstream(t))}n++;}
for(const t of [-1,NaN,Infinity,'1',null]){let f=fixture();f.clock.mechanism=t;assert.throws(()=>old(f));assert.throws(()=>next(f));n++;}
for(const mutate of [f=>delete f.clock,f=>f.clock={hands:2},f=>f.clock.hands=1e308,f=>f.clock.speed=1000]){let f=fixture();mutate(f);assert.deepEqual(next(f),old(f));n++;}
// Import boundary ordering must validate before changing scene. This is source-order evidence, not browser execution.
const review=fs.readFileSync(new URL('../watch-canvas-shortcut-build/staging/preview-b/releases/9865b37ea1813c85badb404935f7710c688f04beef36da55d7d517ceef96b353/assembly-review.js',import.meta.url),'utf8');const restore=review.slice(review.indexOf('function restoreSavedView'),review.indexOf('function restoreSavedView')+2500);
assert(restore.includes('validateViewConfiguration'));assert(restore.indexOf('validateViewConfiguration')<restore.indexOf('powerPath='));
console.log(`PASS ${n} cases: invalid huge mechanism rejected upstream; valid/default/hands/speed behavior preserved; exact downstream sample guard agrees; restore validates before options mutation. Not integrated browser restore proof.`);
const body=review.slice(review.indexOf('function restoreSavedView('),review.indexOf('\nlet configurationRequest=0;'));let mutated=0;
const context=vm.createContext({validateViewConfiguration:next,qualityProfiles:{detail:{}},resolveInspectionState:()=>{mutated++;throw Error('mutation sentinel');}});vm.runInContext(body,context);
for(const time of [1e308,Number.MAX_VALUE,Number.MAX_SAFE_INTEGER]){const f=fixture();f.clock.mechanism=time;assert.throws(()=>context.restoreSavedView(f),/Invalid saved clock/);assert.equal(mutated,0);}
context.validateViewConfiguration=old;let f=fixture();f.clock.mechanism=1e308;assert.throws(()=>context.restoreSavedView(f),/mutation sentinel/);assert.equal(mutated,1);
console.log('PASS actual extracted restoreSavedView rejects three huge times before downstream scene/inspection calls; baseline reaches mutation sentinel. VM harness, not rendered-browser suite.');

import fs from 'node:fs';import crypto from 'node:crypto';
const D='isolated-main-graphite-chapter-fresh',H=x=>crypto.createHash('sha256').update(x).digest('hex');
const source=fs.readFileSync('assembly-open-front.js'),core=fs.readFileSync('vendor/three.core.js');
if(H(source)!=='4e44c427a788dfb52fcecd6d0154f3ad69497347ea8c046563d5f56436a693eb')throw Error('Fresh source generator SHA mismatch: '+H(source));
if(H(core)!=='613e370f76638fdef83926642bf256dc9615684922de1ce1f63a8583e5d78578')throw Error('Three core SHA mismatch');
fs.writeFileSync(D+'/open-front.mjs',source.toString().replace("from './vendor/three.module.js'","from './three.mjs'"));fs.writeFileSync(D+'/three.core.mjs',core);fs.writeFileSync(D+'/three.mjs',fs.readFileSync('vendor/three.module.js','utf8').replaceAll("'./three.core.js'","'./three.core.mjs'"));
await import('./generate.mjs');fs.writeFileSync(D+'/source-authority.json',JSON.stringify({generatorSHA256:H(source),threeCoreSHA256:H(core),route:'pinned b84a51ec preview-b/assembly-review.html authentic nonpremium'},null,2));

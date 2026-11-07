
import assert from 'node:assert/strict';
import {bindGraphiteFragmentValidity as bind,GRAPHITE_FRAGMENT_VALIDITY_REVISION as revision} from '../assembly-fragment-validity.js';
let calls=0;const m={name:'Graphite dial',userData:{retained:1},onBeforeCompile(s){calls++;s.fragmentShader=s.fragmentShader.replace('ORIGINAL','DERIVATIVES_AND_LIGHTING');},customProgramCacheKey(){return 'prior';}};
assert.equal(bind(m),true);assert.equal(bind(m),false);assert.equal(m.userData.retained,1);assert.equal(m.needsUpdate,true);assert.equal(m.customProgramCacheKey(),'prior|'+revision);
const s={fragmentShader:'ORIGINAL\n#include <opaque_fragment>\nAFTER'};m.onBeforeCompile(s);assert.equal(calls,1);
assert.equal(s.fragmentShader,'DERIVATIVES_AND_LIGHTING\nif (isnan(gl_FragCoord.z) || isinf(gl_FragCoord.z)) discard;\n#include <opaque_fragment>\nAFTER');
assert.throws(()=>m.onBeforeCompile({fragmentShader:'missing'}),/expected one/);
assert.throws(()=>m.onBeforeCompile({fragmentShader:'#include <opaque_fragment>\n#include <opaque_fragment>'}),/expected one/);
assert.equal(bind({...m,name:'OM10 / brass',userData:{}}),false);
const reject=z=>Number.isNaN(z)||!Number.isFinite(z);
for(const z of [0,Number.MIN_VALUE,.5,1,-1,2,65504])assert.equal(reject(z),false);
for(const z of [NaN,Infinity,-Infinity])assert.equal(reject(z),true);
assert(!s.fragmentShader.includes('clamp'));assert(!s.fragmentShader.includes('normal='));
console.log('Graphite validity: callback chaining, idempotence, exact ordinary path, scoped membership, anchor guards and finite/nonfinite cases pass');

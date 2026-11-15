import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

const hash=text=>createHash('sha256').update(text).digest('hex');
const sourceURL=new URL('../preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6/assembly-review.js',import.meta.url);
export const baseline=readFileSync(sourceURL,'utf8');
export const candidate=readFileSync(new URL('assembly-review.js',import.meta.url),'utf8');
function block(source,start,end){const a=source.indexOf(start),b=source.indexOf(end,a);assert(a>=0&&b>a);return source.slice(a,b);}

// Source identity/scope assertions, not a claim about renderer or browser state.
export function verifyScope(){
 assert.equal(hash(baseline),'91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee');
 assert.equal(hash(candidate),'41125fe4a5138e085197c0eef5b9c7d9a8587bd988474c8d6d58dae672654c9c');
 const oldReset=block(baseline,"$('reset').onclick", "\ndocument.addEventListener('keydown'"),newReset=block(candidate,"$('reset').onclick", "\ndocument.addEventListener('keydown'");
 const oldFit=block(baseline,'function fitBounds(','function view('),newFit=block(candidate,'function fitBounds(','function view(');
 assert.equal(hash(newReset),'b5d9ee5af628f7b1c588f4d5abb0fbcd98e205d4fe8cb2afa3b592b505132218');
 assert.equal(hash(newFit),'901726655a72ed85fc499f7f16d869c5b8ef57c8f8a7f3a5c44268ca8ee1887c');
 const bad='Original OM10 component â€” original placement preserved',good='Original OM10 component \\u2014 original placement preserved';
 for(const anchor of [oldReset,oldFit,bad])assert.equal(baseline.split(anchor).length,2);
 assert.equal(candidate,baseline.replace(oldReset,newReset).replace(oldFit,newFit).replace(bad,good));
}

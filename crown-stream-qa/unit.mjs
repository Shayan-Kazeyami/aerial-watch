import test from 'node:test';import assert from 'node:assert/strict';
import{createCrownInteraction as make}from'./assembly-crown.js';
import{createCrownInteraction as baseline}from'./baseline-crown.js';
for(const pulled of[false,true])test(`stream parity, callback count and exact deltas (${pulled?'setting':'winding'})`,()=>{
 function fixture(fn){const e={changes:0,turns:[],seconds:[]};const c=fn({duration:.24,secondsPerDegree:20/3,onChange:()=>e.changes++,onTurn:d=>e.turns.push(d),onSetTime:s=>e.seconds.push(s)});c.setPulled(pulled);return{c,e}}
 const a=fixture(baseline),b=fixture(make);a.c.turn(90);b.c.turn(90);a.c.update(.06);b.c.update(.06);const ac=a.e.changes,bc=b.e.changes;
 for(const d of[2,2,2,-2,-2,12,-12,1.3333333]){a.c.cancel();a.c.turn(d);a.c.finish();b.c.turn(d,{immediate:true});assert.deepEqual(b.c.snapshot(),a.c.snapshot());assert.equal(b.c.active,false)}
 assert.deepEqual(b.e.turns,a.e.turns);assert.deepEqual(b.e.seconds,a.e.seconds);assert.equal(a.e.changes-ac,16);assert.equal(b.e.changes-bc,8);
 const end=b.c.snapshot();for(let i=0;i<60;i++)b.c.update(1/60);assert.deepEqual(b.c.snapshot(),end);
 b.c.turn(15);assert.equal(b.c.active,true);assert.equal(b.c.snapshot().degrees,end.degrees);b.c.update(.24);assert.equal(b.c.snapshot().degrees,end.degrees+15);
});
test('zero, invalid, dispose and reduced-motion semantics',()=>{let changes=0;const c=make({duration:0,onChange:()=>changes++});c.turn(2,{immediate:true});assert.equal(c.snapshot().degrees,2);assert.equal(changes,1);c.turn(0,{immediate:true});assert.equal(changes,1);assert.throws(()=>c.turn(NaN,{immediate:true}));c.dispose();c.turn(3,{immediate:true});assert.equal(c.snapshot().degrees,2)});
test('reduced-motion stream parity and mode switch preserve exact committed motion',()=>{let oldCalls=0,newCalls=0;const a=baseline({duration:0,onChange:()=>oldCalls++}),b=make({duration:0,onChange:()=>newCalls++});for(const pulled of[false,true,false]){a.setPulled(pulled);b.setPulled(pulled);for(const d of[2,-2,10]){a.cancel();a.turn(d);a.finish();b.turn(d,{immediate:true});assert.deepEqual(a.snapshot(),b.snapshot())}}assert.equal(oldCalls,30);assert.equal(newCalls,12)});
test('invalid immediate target does not mutate committed or pending state',()=>{const c=make({duration:.24});c.turn(1e308,{immediate:true});const before=c.snapshot();assert.throws(()=>c.turn(1e308,{immediate:true}));assert.deepEqual(c.snapshot(),before);assert.equal(c.active,false)});

import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('./assembly-story.js',import.meta.url),'utf8');
const {createTourSequence,TOUR_SHOTS,TOUR_TITLES,resolveInitialView}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('pause freezes shot and elapsed; resume finishes the remaining dwell',()=>{
 const t=createTourSequence(); t.start();t.tick(7.5);t.tick(2.5);
 const paused=t.pause(); assert.equal(paused.index,1);assert.equal(paused.elapsed,3);
 assert.equal(t.tick(40),null);assert.deepEqual(t.snapshot(),paused);
 assert.equal(t.resume().title,'Dial and hands');assert.equal(t.tick(3.9),null);assert.equal(t.tick(.11).index,2);
});
test('manual navigation pauses playback, wraps consistently, and starts at first view',()=>{
 const t=createTourSequence();assert.equal(t.step(1).index,0);assert.equal(t.step(-1).index,5);assert.equal(t.step(1).index,0);
 t.resume();assert.equal(t.step(1).running,false);assert.equal(t.snapshot().elapsed,0);
 t.stop();assert.equal(t.snapshot().active,false);assert.equal(t.resume().index,0);
});
test('reduced motion is manual, keeps first pose and does not autoadvance',()=>{
 const t=createTourSequence();const start=t.start({reducedMotion:true});assert.equal(start.running,false);assert.equal(start.title,'Complete watch');
 assert.equal(t.tick(70),null);assert.equal(t.step(1).index,1);
 assert.equal(t.resume({reducedMotion:true}).index,1);assert.equal(t.tick(70),null);
});
test('same authored default and six shots, elapsed timing survives slow frames',()=>{
 assert.equal(resolveInitialView(null),'face');assert.equal(TOUR_SHOTS.length,6);
 assert.equal(new Set(TOUR_SHOTS.map(s=>TOUR_TITLES[s])).size,6);
 const t=createTourSequence();t.start();assert.equal(t.tick(7.5).index,1);assert.equal(t.tick(14).index,3);
});

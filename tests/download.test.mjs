import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createDownloadManager} from '../assembly-download.js';
test('download URL survives activation then releases on timeout or teardown',()=>{
 const events=[],timers=[];let sequence=0;
 const link={click(){events.push('click')},remove(){events.push('remove')}};
 const m=createDownloadManager({document:{createElement:()=>link,body:{append:()=>events.push('append')}},urlAPI:{createObjectURL:()=>`blob:${++sequence}`,revokeObjectURL:u=>events.push(u)},setTimer:(fn,ms)=>{timers.push({fn,ms});return timers.length;},clearTimer:id=>events.push(`clear:${id}`)});
 assert(m.save(new Blob(),'test.png').requested);assert.deepEqual(events,['append','click','remove']);assert.equal(timers[0].ms,60000);assert.equal(m.pendingCount,1);
 timers[0].fn();assert.equal(m.pendingCount,0);assert(events.includes('blob:1'));
 m.save(new Blob(),'two.png');m.dispose();m.dispose();assert.equal(m.pendingCount,0);assert.throws(()=>m.save(new Blob(),'three.png'),/closed/);
});

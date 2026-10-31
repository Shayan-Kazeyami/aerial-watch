import {test} from 'node:test';
import assert from 'node:assert/strict';
import {captureCanvasPNG} from '../assembly-image-export.js';
test('image encoding resolves successful Blob',async()=>{
 const b=new Blob(['test'],{type:'image/png'});assert.equal(await captureCanvasPNG({toBlob:cb=>cb(b)}),b);
});
test('image encoding rejects missing callback and permits a new attempt',async()=>{
 await assert.rejects(captureCanvasPNG({toBlob:()=>{}},{timeoutMs:5}),/timed out/);
 const b=new Blob(['test']);assert.equal(await captureCanvasPNG({toBlob:cb=>cb(b)}),b);
});
test('image encoding rejects null and thrown errors',async()=>{
 await assert.rejects(captureCanvasPNG({toBlob:cb=>cb(null)}),/could not create/);
 await assert.rejects(captureCanvasPNG({toBlob:()=>{throw Error('tainted')}}),/tainted/);
 assert.throws(()=>captureCanvasPNG({},{timeoutMs:0}),/positive/);
});

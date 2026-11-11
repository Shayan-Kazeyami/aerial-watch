import test from 'node:test';import assert from 'node:assert/strict';
import {createReadbackVideoFrame} from '../assembly-video-frame.js';
test('owned RGBA readback flips WebGL rows, preserves metadata and reallocates after resize',()=>{
 const canvas={width:2,height:3};let framebuffer=null,lost=false;
 const gl={FRAMEBUFFER_BINDING:1,RGBA:2,UNSIGNED_BYTE:3,getParameter:()=>framebuffer,isContextLost:()=>lost,readPixels(x,y,w,h,format,type,data){assert.equal(format,2);assert.equal(type,3);for(let r=0;r<h;r++)data.fill(r+1,r*w*4,(r+1)*w*4);}};
 class Frame{constructor(data,options){this.data=new Uint8Array(data);this.options=options;}}
 const read=createReadbackVideoFrame({canvas,gl,Frame});let f=read({timestamp:100,duration:33333});assert.deepEqual([...f.data],[...Array(8).fill(3),...Array(8).fill(2),...Array(8).fill(1)]);assert.deepEqual(f.options,{timestamp:100,duration:33333,format:'RGBA',codedWidth:2,codedHeight:3});
 canvas.width=1;canvas.height=2;let next=read({timestamp:200});assert.deepEqual([...next.data],[2,2,2,2,1,1,1,1]);assert.equal(f.data[0],3);
 framebuffer={};assert.throws(()=>read({}),/completed screen/);framebuffer=null;lost=true;assert.throws(()=>read({}),/context closed/);
});
test('non-WebGL canvas falls back to top-left CPU pixels',()=>{let drawn=false;const source={width:1,height:1},data=new Uint8ClampedArray([2,3,4,255]);const c={getContext:()=>({drawImage(s){assert.equal(s,source);drawn=true;},getImageData:()=>({data})})};class Frame{constructor(p,o){assert.equal(p,data);assert.equal(o.codedWidth,1);}}const read=createReadbackVideoFrame({canvas:source,doc:{createElement:()=>c},Frame});read({timestamp:0});assert.ok(drawn);});

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
const source = await readFile(new URL('../assembly-webm-muxer.js', import.meta.url), 'utf8');
const { muxWebM } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const chunk = (timestamp = 0, type = 'key') => ({timestamp, type, data: new Uint8Array([1,2,3])});
const options = {chunks:[chunk()], width:64,height:48,frameRate:10,durationMs:100};
function elements(data, start=0,end=data.length) {
  const result=[]; let p=start;
  while(p<end) {
    const begin=p; let n=1,mask=128; while(!(data[p]&mask)){mask>>=1;n++;if(n>8)throw Error('Bad EBML');}
    let tag=0; for(let i=0;i<n;i++)tag=tag*256+data[p++];
    n=1;mask=128;while(!(data[p]&mask)){mask>>=1;n++;if(n>8)throw Error('Bad size');}
    let size=data[p++]&(mask-1);for(let i=1;i<n;i++)size=size*256+data[p++];
    assert.ok(p+size<=end);result.push({tag,start:p,end:p+size,begin,size});p+=size;
  } assert.equal(p,end);return result;
}
const number = (b, e) => [...b.subarray(e.start,e.end)].reduce((v,x)=>v*256+x,0);
test('finite Segment, metadata, cues and safe cluster timecodes',()=>{
 const b=muxWebM({...options,chunks:[chunk(),chunk(33000000,'delta'),chunk(34000000)],durationMs:34100});
 const top=elements(b);assert.equal(top[1].tag,0x18538067);assert.equal(top[1].end,b.length);
 const seg=elements(b,top[1].start,top[1].end);const clusters=seg.filter(x=>x.tag===0x1f43b675);assert.equal(clusters.length,3);
 for(const cl of clusters){const e=elements(b,cl.start,cl.end);const block=e.find(x=>x.tag===0xa3);assert.equal(new DataView(b.buffer).getInt16(block.start+1),0);}
 const cues=seg.find(x=>x.tag===0x1c53bb6b);const entries=elements(b,cues.start,cues.end);assert.equal(entries.length,2);
 for(const entry of entries){const fields=elements(b,entry.start,entry.end);const pos=fields.find(x=>x.tag===0xb7);const cp=elements(b,pos.start,pos.end).find(x=>x.tag===0xf1);assert.ok(clusters.some(c=>c.begin-top[1].start===number(b,cp)));}
});
test('input validation and bounded output',()=>{
 for(const patch of [{width:0},{height:NaN},{frameRate:Infinity},{durationMs:0},{codec:'h264'},{expectedFrames:2},{chunks:[]},{chunks:[chunk(0,'delta')]},{chunks:[chunk(),chunk()]},{chunks:[chunk(-1)]},{chunks:[chunk(100000)]},{chunks:[{...chunk(),duration:200000}]},{maxOutputBytes:1024,chunks:[{...chunk(),data:new Uint8Array(1024)}]}]) assert.throws(()=>muxWebM({...options,...patch}));
 const original=chunk();assert.deepEqual(muxWebM(options),muxWebM({...options,chunks:[{type:'key',timestamp:0,byteLength:3,copyTo(out){out.set(original.data);}}]}));
});
for(const codec of ['vp8','vp9'])test(`real ${codec}: ffprobe metadata, decoding and seeking`,async()=>{
 const dir=await mkdtemp(join(tmpdir(),'webm-test-'));
 try{
 const ivf=join(dir,'source.ivf'), webm=join(dir,'output.webm');
 execFileSync('ffmpeg',['-v','error','-f','lavfi','-i','testsrc2=size=96x64:rate=10:duration=3','-c:v',codec==='vp8'?'libvpx':'libvpx-vp9','-g','10','-threads','1','-f','ivf',ivf]);
 const data=await readFile(ivf);let p=32;const chunks=[];
 while(p<data.length){const size=data.readUInt32LE(p);const timestamp=Number(data.readBigUInt64LE(p+4))*100000;p+=12;const packet=data.subarray(p,p+size);p+=size;chunks.push({type:chunks.length%10===0?'key':'delta',timestamp,duration:100000,data:packet});}
 const out=muxWebM({chunks,width:96,height:64,frameRate:10,durationMs:3000,codec,expectedFrames:30});await writeFile(webm,out);
 const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',webm],{encoding:'utf8'}));const stream=probe.streams[0];
 assert.equal(stream.codec_name,codec);assert.equal(stream.width,96);assert.equal(stream.height,64);assert.equal(stream.nb_read_frames,'30');assert.equal(Number(probe.format.duration),3);assert.equal(stream.r_frame_rate,'10/1');
 execFileSync('ffmpeg',['-v','error','-i',webm,'-f','null','-']);
 const seek=execFileSync('ffmpeg',['-v','error','-ss','2','-i',webm,'-frames:v','1','-f','rawvideo','-pix_fmt','yuv420p','-']);assert.equal(seek.length,96*64*1.5);
 const expected=execFileSync('ffmpeg',['-v','error','-i',ivf,'-ss','2','-frames:v','1','-f','rawvideo','-pix_fmt','yuv420p','-']);assert.deepEqual(seek,expected);
 }finally{await rm(dir,{recursive:true,force:true});}
});

from pathlib import Path
import sys,hashlib,json,subprocess
r=Path(sys.argv[1]).resolve()
BEFORE={'assembly-recording.js': '30bb8d3a54e3daaefe4835d5709af63b12da307b0c7e085d101a39ad7eb2a864', 'tests/recording.test.mjs': 'bcb3fe118c1fbf9146199185ac571d9938588c6241ed7a4e013de160906544a3', 'deployment-manifest.json': 'e5b0f301629214ed5af9f95ce44a24fb2f4ab99ed9b027e1bec0c4a32d6610ce', 'quality-study/viewer-revision.js': '49ec6c8a5713ced937b3fec115635087a134708e7bf96b344a7d31630e3c5de9', 'quality-study/viewer-revision.json': '2cc9243d701cee77f23c15410631f77acc2a7c86d9f9a448443dc99fb8288c2d'}
AFTER={'assembly-recording.js': '5f8fc345104e03e87e358bcec9f24d19d1ae0cf0c7769e5753bb96cfcb7d4b4f', 'tests/recording.test.mjs': 'dc5ce15895fcb1ffb353f977c4fdfddd962b50239ccf597c692b5b285b6f30df', 'deployment-manifest.json': '31dc6d4c4849d1cd2362932873908a0dc17317998d8f247b0293a8d6a57ff0a0', 'quality-study/viewer-revision.js': '66be94c04891cec24e4c18ae7714846d41bd41cecfd79f6bdb982ecc1aa749fb', 'quality-study/viewer-revision.json': 'e27ba75727fd9a9959cfaab1063932bbc27480777ea7f15ea0af5591ff108e91'}
for n,h in BEFORE.items():
 assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,'Unexpected capture-v2 baseline: '+n
p=r/'assembly-recording.js';s=p.read_text()
assert s.count('            // A few widely spaced packets are not a useful motion clip even\n')==1
s=s.replace('            // A few widely spaced packets are not a useful motion clip even\n',"            if(videoTiming.invalid){const error=new Error('The browser produced an incomplete or invalid video clip. No file was saved. Try a hardware-accelerated browser, or save a PNG image instead.');error.videoTiming=videoTiming;fail(recording,error);return;}\n            // A few widely spaced packets are not a useful motion clip even\n",1)
assert s.count('  }catch{return unverified;}\n')==1
s=s.replace('  }catch{return unverified;}\n',"  }catch(error){\n    // A recognized WebM header followed by broken/truncated EBML cannot be a\n    // usable canvas clip. Unsupported valid layouts (e.g. lacing) stay unknown.\n    if(parsedHeader&&/^(Invalid EBML|Truncated EBML|Truncated video block)/.test(error.message))return {...unverified,invalid:true,reason:'malformed-webm'};\n    return unverified;\n  }\n",1)
assert s.count('    if(!header||!segment||videoTracks.length!==1||scale<=0)return unverified;\n')==1
s=s.replace('    if(!header||!segment||videoTracks.length!==1||scale<=0)return unverified;\n',"    if(header&&!segment)return {...unverified,invalid:true,reason:'missing-video-segment'};\n    if(header&&segment&&videoTracks.length===0)return {...unverified,invalid:true,reason:'missing-video-track'};\n    if(!header||!segment||videoTracks.length!==1||scale<=0)return unverified;\n",1)
assert s.count('      if(id===0x1a45dfa3)header=true;\n')==1
s=s.replace('      if(id===0x1a45dfa3)header=true;\n','      if(id===0x1a45dfa3){header=true;parsedHeader=true;}\n',1)
assert s.count('  if(blob.size>128*1024*1024)return unverified;\n  try{\n')==1
s=s.replace('  if(blob.size>128*1024*1024)return unverified;\n  try{\n','  if(blob.size>128*1024*1024)return unverified;\n  let parsedHeader=false;\n  try{\n',1)
p.unlink();p.write_text(s)
p=r/'tests/recording.test.mjs';s=p.read_text()
s+="\ntest('observed Chrome header-only 110-byte clip is known invalid, never downloadable',async()=>{\n const header=Buffer.from('1a45dfa39f4286810142f7810142f2810442f381084282847765626d4287810442858102','hex');const bytes=Buffer.concat([header,Buffer.alloc(110-header.length)]);\n const timing=await inspectWebM(new Blob([bytes]));assert.equal(timing.invalid,true);assert.equal(timing.reason,'malformed-webm');\n let completed=0;const h=setup({onComplete:()=>completed++}),pending=h.recorder.start(),instance=h.instances[0];instance.data(bytes);instance.finish();await assert.rejects(pending,/incomplete or invalid video.*No file was saved/);assert.equal(completed,0);assertClean(h,instance);\n});\ntest('unsupported laced WebM remains unknown, not falsely labeled invalid',async()=>{\n const timing=await inspectWebM(webm([0,100],{laced:true}));assert.equal(timing.verified,false);assert.equal(timing.invalid,undefined);\n});\ntest('known header missing segment, missing video track and truncated body are invalid',async()=>{\n const full=new Uint8Array(await webm([0,100]).arrayBuffer());const truncated=await inspectWebM(new Blob([full.subarray(0,full.length-1)]));assert.equal(truncated.invalid,true);\n const header=Buffer.from('1a45dfa380','hex');assert.equal((await inspectWebM(new Blob([header]))).reason,'missing-video-segment');assert.equal((await inspectWebM(new Blob([header,Buffer.from('1853806780','hex')]))).reason,'missing-video-track');\n});\n"
assert s.count('    assert.deepEqual(await inspectWebM(blob),{verified:false,encodedPacketCount:null,timestampSpanMs:null});\n')==1
s=s.replace('    assert.deepEqual(await inspectWebM(blob),{verified:false,encodedPacketCount:null,timestampSpanMs:null});\n','    const timing=await inspectWebM(blob);assert.equal(timing.verified,false);assert.equal(timing.encodedPacketCount,null);assert.equal(timing.timestampSpanMs,null);\n',1)
p.unlink();p.write_text(s)
p=r/'deployment-manifest.json';m=json.loads(p.read_text());p.unlink()
for e in m['files']:
 if e['path']=='assembly-recording.js':
  b=(r/e['path']).read_bytes();e.update(sizeBytes=len(b),sha256=hashlib.sha256(b).hexdigest())
p.write_text(json.dumps(m,indent=2)+'\n')
for n in ['quality-study/viewer-revision.js','quality-study/viewer-revision.json']:
 p=r/n;b=p.read_bytes();p.unlink();p.write_bytes(b)
subprocess.run(['node','tools/capture-provenance.mjs'],cwd=r,check=True)
p=r/'deployment-manifest.json';m=json.loads(p.read_text())
for e in m['files']:
 if e['path'].startswith('quality-study/viewer-revision.'):
  b=(r/e['path']).read_bytes();e.update(sizeBytes=len(b),sha256=hashlib.sha256(b).hexdigest())
p.write_text(json.dumps(m,indent=2)+'\n')
for n,h in AFTER.items():
 assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,'Recording guard result mismatch: '+n
print('Known-invalid WebM guard verified. Unknown layouts and cadence threshold preserved.')

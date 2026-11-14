from pathlib import Path
import hashlib,json
ROOT=Path('qa-video-lifetime');release=Path('preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6')
proof={}
for name in ['original','candidate']:
 d=ROOT/name;d.mkdir(parents=True,exist_ok=True)
 for f in ['assembly-video-frame.js','assembly-offline-video.js','assembly-video-export.js','assembly-video-dialog.js','assembly-webm-muxer.js']:
  src=(release/f).read_text();before=hashlib.sha256(src.encode()).hexdigest()
  if name=='candidate' and f=='assembly-video-frame.js':
   assert src.count(' return metadata=>{')==1
   src=src.replace(' return metadata=>{',' const snapshot=metadata=>{')
   assert src.count('\n };\n}')==1
   src=src.replace('\n };\n}', '\n };\n snapshot.release=()=>{pixels=row=copyCanvas=copyContext=undefined;width=height=0;};\n return snapshot;\n}')
  if name=='candidate' and f=='assembly-offline-video.js':
   assert src.count('finally{progress=null;if(!disposed)dialog.close();}')==1
   src=src.replace('finally{progress=null;if(!disposed)dialog.close();}','finally{snapshot.release?.();progress=null;if(!disposed)dialog.close();}')
   assert src.count('exporter.dispose();dialog.dispose();')==1
   src=src.replace('exporter.dispose();dialog.dispose();','exporter.dispose();snapshot.release?.();dialog.dispose();')
  after=hashlib.sha256(src.encode()).hexdigest()
  # QA accounting logs allocation byte counts only, no retained buffer references.
  if f=='assembly-video-frame.js':
   src=src.replace('new Uint8Array(stride*h)','window.qaAllocate(stride*h)').replace('new Uint8Array(stride)','window.qaAllocate(stride)')
   if name=='candidate':src=src.replace('snapshot.release=()=>{','snapshot.release=()=>{window.qaReleaseCount++;')
  (d/f).write_text(src)
  proof[name+'/'+f]={'exact_release_sha256':before,'candidate_before_QA_instrumentation_sha256':after}
 (d/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Video lifetime QA</title><canvas width="96" height="64"></canvas><script type="module" src="../harness.js"></script>')
(ROOT/'source-proof.json').write_text(json.dumps(proof,indent=2))

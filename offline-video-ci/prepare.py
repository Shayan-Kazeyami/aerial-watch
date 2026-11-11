import pathlib,json,hashlib,shutil
RID='36f0aca93a5c9e1cf01e0237aabcc0c71ee96fbfc2cc64394b74b35c32cf75e8'
root=pathlib.Path('preview-b/releases')/RID
out=pathlib.Path('offline-output');out.mkdir(exist_ok=True)
manifest=json.loads((root/'deployment-manifest.json').read_text());canonical={k:manifest[k] for k in ['schemaVersion','localFiles','references']};assert hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()==RID
files={}
for name in ['assembly-video-export.js','assembly-webm-muxer.js']:
 src=pathlib.Path('offline-video-ci')/name;b=src.read_bytes();files[name]=hashlib.sha256(b).hexdigest();shutil.copyfile(src,root/name)
hook=r'''
let offlineVideoBusy=false;
const offlineExporter=createFrameVideoExporter({canvas:renderer.domElement,
 begin(){
  if(loading||failed||cameraTween||crownInteraction.active||crownVisual?.active||explosion?.animating)throw new Error('Viewer is busy');
  const saved=clock.snapshot();offlineVideoBusy=true;
  clock.setRunning('mechanism',false);clock.setRunning('hands',false);return saved;
 },
 renderFrame(seconds,{context:saved}){
  applyClockPose({...saved,mechanism:saved.mechanism+(saved.running.mechanism?seconds*saved.speed:0),hands:saved.hands+(saved.running.hands?seconds*saved.speed:0)});
  composer.render();
 },
 end(saved){
  clock.seek(saved.mechanism,{track:'mechanism'});clock.seek(saved.hands,{track:'hands'});
  clock.setRunning('mechanism',saved.running.mechanism);clock.setRunning('hands',saved.running.hands);
  applyClockPose(clock.snapshot());offlineVideoBusy=false;dirty=true;
 },onProgress:progress=>{window.__offlineProgress=progress;},
});
window.__offlineQA={async start(durationMs=2000){
 const before={clock:clock.snapshot(),camera:camera.position.toArray(),target:controls.target.toArray(),quality,viewport:{width:renderer.domElement.width,height:renderer.domElement.height},backend:backendIdentity.actual,gpu:renderer.getContext().getParameter(renderer.getContext().getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL)};
 const result=await offlineExporter.start({durationMs,frameRate:30});downloadBlob(result.blob,'aerial-offline-motion.webm');
 return {before,after:{clock:clock.snapshot(),camera:camera.position.toArray(),target:controls.target.toArray(),busy:offlineVideoBusy},result:{width:result.width,height:result.height,frameRate:result.frameRate,frameCount:result.frameCount,durationMs:result.durationMs,codec:result.codec,bytes:result.blob.size}};
},cancel:()=>offlineExporter.cancel(),progress:()=>window.__offlineProgress};
'''
runtime=(root/'assembly-review.js').read_text();runtime="import {createFrameVideoExporter} from './assembly-video-export.js';\n"+runtime.replace("if(lifecycle.disposed)return;\n  animationFrame=requestAnimationFrame(frame);","if(lifecycle.disposed)return;\n  animationFrame=requestAnimationFrame(frame);\n  if(offlineVideoBusy)return;")+hook
assert 'if(offlineVideoBusy)return;' in runtime
(root/'qa-offline-runtime.js').write_text(runtime)
(root/'qa-offline-shell.js').write_text((root/'atelier-preview.js').read_text().replace('./assembly-review.js?v=atelier-local-1','./qa-offline-runtime.js'))
(root/'qa-offline.html').write_text((root/'atelier-preview.html').read_text().replace('atelier-preview.js','qa-offline-shell.js'))
(out/'identity.json').write_text(json.dumps({'baseline':RID,'modules':files,'runtimeSha256':hashlib.sha256(runtime.encode()).hexdigest()},indent=2))

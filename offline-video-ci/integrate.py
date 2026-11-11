# Apply the product integration only to a copied immutable source tree.
import pathlib

def integrate(root):
 p=root/'assembly-review.js';s=p.read_text()
 s="import {createOfflineVideoExport} from './assembly-offline-video.js';\n"+s
 old="""if($('record-scene'))$('record-scene').onclick=async()=>{
  $('record-scene').disabled=true;
  try{const result=await recorder.start();downloadBlob(result.blob,'aerial-motion.webm');}
  catch(error){if(error.name!=='AbortError')announce(`Could not record: ${error.message}`);}
  finally{if(!lifecycle.disposed)$('record-scene').disabled=false;}
};"""
 new="""const frameVideo=createOfflineVideoExport({canvas:renderer.domElement,
  begin(){
    const presentation=presentationGate.snapshot();
    if(loading||failed||contextLost||!presentation.interactive||!presentation.canRender||(presentation.enabled&&presentation.pending.length)||proposalLoading||comparisonDetails.snapshot().loading||['waiting-for-first-frame','upgrading'].includes(progressiveNormalState)||pendingCaptures.has('import-config')||cameraTween||crownInteraction.active||crownVisual?.active||explosion?.animating)throw new Error('Wait for the watch view to settle, then render again.');
    const saved={clock:clock.snapshot(),controlsEnabled:controls.enabled};
    controls.enabled=false;clock.setRunning('mechanism',false);clock.setRunning('hands',false);return saved;
  },
  renderFrame(seconds,{context:saved}){
    if(contextLost||lifecycle.disposed)throw new Error('The watch renderer closed. No video was saved.');
    const stamp=saved.clock;
    applyClockPose({...stamp,mechanism:stamp.mechanism+(stamp.running.mechanism?seconds*stamp.speed:0),hands:stamp.hands+(stamp.running.hands?seconds*stamp.speed:0)});
    composer.render();
  },
  end(saved){
    if(lifecycle.disposed)return;
    const stamp=saved.clock;
    clock.seek(stamp.mechanism,{track:'mechanism'});clock.seek(stamp.hands,{track:'hands'});
    clock.setRunning('mechanism',stamp.running.mechanism);clock.setRunning('hands',stamp.running.hands);
    applyClockPose(clock.snapshot());controls.enabled=saved.controlsEnabled;dirty=true;
  },
});
resources.own('frame-by-frame video export',()=>frameVideo.dispose());
if($('record-scene')){
 $('record-scene').textContent=frameVideo.supported?'Render 8s video':'Record 8s video';
 $('record-scene').onclick=async()=>{
  if(frameVideo.active||recorder.recording)return;
  if(pendingCaptures.has('import-config')){announce('Wait for the saved view to finish restoring before rendering video.');return;}
  const returnFocus=document.activeElement;
  $('record-scene').disabled=true;
  try{
    const result=frameVideo.supported?await frameVideo.start():await recorder.start();
    if(lifecycle.disposed)return;downloadBlob(result.blob,'aerial-motion.webm');
    announce(frameVideo.supported?'8-second video rendered at 30 frames per second. Check your browser downloads.':'Video download requested. Check your browser downloads.');
  }catch(error){announce(error.name==='AbortError'?'Video render cancelled. No video was saved.':`Could not save video: ${error.message}`);}
  finally{if(!lifecycle.disposed){$('record-scene').disabled=false;
   const focusTarget=returnFocus?.isConnected&&!returnFocus.disabled&&returnFocus.getClientRects().length?returnFocus:document.querySelector('.task-dock [data-mode=capture]')||$('record-scene');focusTarget.focus({preventScroll:true});
  }}
 };
} """
 assert s.count(old)==1;s=s.replace(old,new)
 needle='  animationFrame=requestAnimationFrame(frame);';assert s.count(needle)==1
 s=s.replace(needle,needle+'\n  if(frameVideo.active){last=time;return;}')
 s=s.replace('window.assemblyInspect = () => ({explosion:', 'window.assemblyInspect = () => ({videoExport:{active:frameVideo.active,progress:frameVideo.progress},explosion:')
 s=s.replace('  const request=++configurationRequest;','  const request=++configurationRequest;pendingCaptures.add(\'import-config\');')
 s=s.replace("    const restoredInspection=resolveInspectionState(config.inspection);","    if(frameVideo.active)throw new Error('Wait for video rendering to finish before restoring a view.');\n    const restoredInspection=resolveInspectionState(config.inspection);")
 s=s.replace("finally{if(request===configurationRequest)input.value='';}","finally{if(request===configurationRequest){input.value='';pendingCaptures.delete('import-config');}}")
 p.write_text(s)
 p=root/'atelier-preview.js';s=p.read_text().replace("${button('Record 8s video','record-scene')}","${button('Save 8s video','record-scene')}").replace('Downloads stay on this device. Video availability depends on browser support.','Downloads stay on this device. Rendering builds every video frame and may take longer than 8 seconds. Older browsers use live recording.');p.write_text(s)

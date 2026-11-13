// A modal blocks view changes during deterministic export while leaving a clear,
// keyboard-accessible Cancel action. Native dialog supplies background inertness.
export function createVideoExportDialog({onCancel=()=>{},doc=globalThis.document}={}){
 const dialog=doc.createElement('dialog');dialog.className='aerial-video-dialog';
 dialog.setAttribute('aria-labelledby','aerial-video-heading');dialog.setAttribute('aria-describedby','aerial-video-description');
 dialog.innerHTML='<h2 id="aerial-video-heading">Rendering video</h2><p id="aerial-video-description">Building every frame for smooth playback. This can take longer than the video itself.</p><progress max="1" value="0" aria-label="Video rendering progress"></progress><p class="aerial-video-progress" aria-live="polite" aria-atomic="true">Preparing the video…</p><button type="button" autofocus>Cancel render</button>';
 const style=doc.createElement('style');style.textContent='.aerial-video-dialog{box-sizing:border-box;width:min(430px,calc(100vw - 32px));max-height:calc(100dvh - 32px);overflow:auto;border:1px solid #c6c3b9;border-radius:16px;padding:24px;background:#f3f0e8;color:#232820;box-shadow:0 18px 80px #0005;font:14px/1.55 Arial,sans-serif}.aerial-video-dialog::backdrop{background:#11170fb3}.aerial-video-dialog h2{margin:0 0 10px;font:500 26px/1.1 Georgia,serif}.aerial-video-dialog p{margin:0 0 16px}.aerial-video-dialog progress{display:block;width:100%;height:8px;accent-color:#536047;margin:20px 0 12px}.aerial-video-dialog .aerial-video-progress{font-size:12px;min-height:19px}.aerial-video-dialog button{display:block;width:100%;min-height:44px;border:1px solid #989d8e;border-radius:8px;color:#232820;background:transparent;font:inherit;cursor:pointer}.aerial-video-dialog button:focus-visible{outline:3px solid #788a62;outline-offset:3px}.aerial-video-dialog button:disabled{opacity:.65;cursor:wait}';
 doc.head.append(style);doc.body.append(dialog);
 const progress=dialog.querySelector('progress'),message=dialog.querySelector('.aerial-video-progress'),button=dialog.querySelector('button');let lastAnnouncement=-1;
 const cancel=event=>{event?.preventDefault();if(button.disabled)return;button.disabled=true;message.textContent='Cancelling and restoring the watch…';onCancel();};
 // Native modality prevents pointer interaction, but document-level hotkeys
 // still receive bubbled events. Keep Home/Escape from changing the watch.
 // Do not prevent the default: Escape must still request native cancellation.
 dialog.addEventListener('keydown',event=>event.stopPropagation());
 button.addEventListener('click',cancel);dialog.addEventListener('cancel',cancel);
 return {
  open(){button.disabled=false;progress.value=0;lastAnnouncement=-1;message.textContent='Preparing the video…';dialog.showModal();},
  update({completed,total,phase}){
   if(button.disabled)return;progress.max=total;progress.value=completed;
   const percent=Math.floor(completed/total*100);
   if(phase==='encoding')message.textContent='Finishing the video…';
   else if(Math.floor(percent/10)!==lastAnnouncement){lastAnnouncement=Math.floor(percent/10);message.textContent=`Rendering ${percent}% · ${completed} of ${total} frames`;} 
  },
  close(){if(dialog.open)dialog.close();},
  dispose(){if(dialog.open)dialog.close();dialog.remove();style.remove();},
 };
}

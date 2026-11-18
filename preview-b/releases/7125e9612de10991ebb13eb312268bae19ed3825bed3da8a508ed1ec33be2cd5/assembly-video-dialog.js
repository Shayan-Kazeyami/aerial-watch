// Native modal makes the watch inert while choosing or rendering the video.
export function createVideoExportDialog({onCancel=()=>{},doc=globalThis.document}={}){
 const dialog=doc.createElement('dialog');dialog.className='aerial-video-dialog';
 dialog.setAttribute('aria-labelledby','aerial-video-heading');dialog.setAttribute('aria-describedby','aerial-video-description');
 dialog.innerHTML='<h2 id="aerial-video-heading"></h2><p id="aerial-video-description"></p><form class="aerial-video-choice" hidden><fieldset><legend>Video resolution</legend><label><input type="radio" name="size" value="view" checked> <span data-video-size="view"></span></label><label><input type="radio" name="size" value="compact"> <span data-video-size="compact"></span></label></fieldset><button type="submit">Render 8s video</button></form><div class="aerial-video-status" hidden><progress max="1" value="0" aria-label="Video rendering progress"></progress><p class="aerial-video-progress" aria-live="polite" aria-atomic="true"></p></div><button class="aerial-video-cancel" type="button">Cancel</button>';
 const style=doc.createElement('style');style.textContent='.aerial-video-dialog{box-sizing:border-box;width:min(430px,calc(100vw - 32px));max-height:calc(100dvh - 32px);overflow:auto;border:1px solid #c6c3b9;border-radius:16px;padding:24px;background:#f3f0e8;color:#232820;box-shadow:0 18px 80px #0005;font:14px/1.55 Arial,sans-serif}.aerial-video-dialog::backdrop{background:#11170fb3}.aerial-video-dialog h2{margin:0 0 10px;font:500 26px/1.1 Georgia,serif}.aerial-video-dialog p{margin:0 0 16px}.aerial-video-dialog progress{display:block;width:100%;height:8px;accent-color:#536047;margin:20px 0 12px}.aerial-video-dialog .aerial-video-progress{font-size:12px;min-height:19px}.aerial-video-dialog fieldset{margin:0 0 12px;padding:4px 10px;border:1px solid #989d8e;border-radius:8px}.aerial-video-dialog label{display:flex;align-items:center;gap:8px;min-height:44px}.aerial-video-dialog input{accent-color:#536047}.aerial-video-dialog button{display:block;width:100%;min-height:44px;border:1px solid #989d8e;border-radius:8px;color:#232820;background:transparent;font:inherit;cursor:pointer}.aerial-video-dialog [type=submit]{background:#536047;color:white;margin-bottom:8px}.aerial-video-dialog :is(input,button):focus-visible{outline:3px solid #788a62;outline-offset:3px}.aerial-video-dialog button:disabled{opacity:.65;cursor:wait}';
 doc.head.append(style);doc.body.append(dialog);
 const heading=dialog.querySelector('h2'),description=dialog.querySelector('#aerial-video-description');
 const form=dialog.querySelector('.aerial-video-choice'),status=dialog.querySelector('.aerial-video-status');
 const progress=dialog.querySelector('progress'),message=dialog.querySelector('.aerial-video-progress'),button=dialog.querySelector('.aerial-video-cancel');
 let lastAnnouncement=-1,chooseResolve=null;
 const settleChoice=value=>{if(!chooseResolve)return false;const resolve=chooseResolve;chooseResolve=null;resolve(value);return true;};
 const cancel=event=>{event?.preventDefault();if(settleChoice(null)||button.disabled)return;button.disabled=true;message.textContent='Cancelling and restoring the watch…';onCancel();};
 const show=()=>{if(!dialog.open)dialog.showModal();};
 form.addEventListener('submit',event=>{event.preventDefault();const checked=form.querySelector('input:checked');if(checked)settleChoice(checked.value);});
 // Escape still requests native cancellation; stop other document hotkeys.
 dialog.addEventListener('keydown',event=>event.stopPropagation());
 button.addEventListener('click',cancel);dialog.addEventListener('cancel',cancel);
 const dimensions=({width,height})=>`${width} × ${height}`;
 return {
  choose({view,compact}){
   heading.textContent='Save an 8-second video';
   description.textContent='Choose the output size. Both options keep the watch in frame at 30 fps. Rendering may take longer than playback.';
   form.hidden=false;status.hidden=true;button.disabled=false;button.textContent='Cancel';
   form.querySelector('[value=view]').checked=true;
   form.querySelector('[data-video-size=view]').textContent=`Current view · ${dimensions(view)}`;
   form.querySelector('[data-video-size=compact]').textContent=`Compact · ${dimensions(compact)}`;
   return new Promise(resolve=>{chooseResolve=resolve;show();form.querySelector('[value=view]').focus();});
  },
  cancelChoice(){return settleChoice(null);},
  open({size}={}){
   heading.textContent='Rendering video';
   description.textContent=size?`8 seconds at 30 fps · ${dimensions(size)}. Rendering may take longer than playback.`:'Building every frame for smooth playback. This can take longer than the video itself.';
   form.hidden=true;status.hidden=false;button.disabled=false;button.textContent='Cancel render';
   progress.max=1;progress.value=0;lastAnnouncement=-1;message.textContent='Preparing the video…';show();button.focus();
  },
  update({completed,total,phase}){
   if(button.disabled)return;
   if(phase==='encoding'){progress.removeAttribute('value');message.textContent='Finishing the video…';return;}
   progress.max=total;progress.value=completed;
   const percent=Math.floor(completed/total*100);
   if(Math.floor(percent/10)!==lastAnnouncement){lastAnnouncement=Math.floor(percent/10);message.textContent=`Rendered ${completed} of ${total} frames`;}
  },
  close(){settleChoice(null);if(dialog.open)dialog.close();},
  dispose(){settleChoice(null);if(dialog.open)dialog.close();dialog.remove();style.remove();},
 };
}

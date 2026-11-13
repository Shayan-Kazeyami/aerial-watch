import {createFirstUseGuide} from './atelier-first-use.js';
import {COMPAT_LEATHER_WARNING} from './assembly-leather-compat.js';
import {errorDetails,copyErrorDetails} from './atelier-error-details.js';
import {withAtelierDefaults} from './atelier-defaults.js';
import {createAtelierNavigation,EXPERIENCE_MODES} from './atelier-navigation.js';
// Local atelier shell: legacy IDs remain the single source of runtime state.
// Integration: document atelier:capabilities {explode:boolean,crownDrag:boolean};
// document atelier:explode {amount:0..1}; runtime -> atelier:explode-state {amount}.
// Crown's existing controls are live now; direct on-object gestures belong to runtime.
const $=id=>document.getElementById(id), bridge=$('runtime-bridge');
$('atelier-stage-host').append($('stage'));
const defaultURL=withAtelierDefaults(location.href);
if(defaultURL.href!==location.href)history.replaceState(null,'',defaultURL.pathname+defaultURL.search+defaultURL.hash);
let runtimeFailure=null,captureDetail=null,detailRetryRequested=false;
const errorBox=document.createElement('div');errorBox.id='atelier-error-details';errorBox.hidden=true;
const errorSummary=document.createElement('p');errorSummary.setAttribute('role','alert');
const copyError=document.createElement('button');copyError.type='button';copyError.textContent='Copy error details';
const errorText=document.createElement('textarea');errorText.readOnly=true;errorText.hidden=true;errorText.setAttribute('aria-label','Error details — select and copy');
const copyStatus=document.createElement('p');copyStatus.setAttribute('role','status');
errorBox.append(errorSummary,copyError,copyStatus,errorText);$('studio-poster').append(errorBox);
let currentErrorText='';
copyError.onclick=async()=>{const text=currentErrorText;if(!text)return;const copied=await copyErrorDetails(text,{clipboard:navigator.clipboard,showFallback:value=>{if(currentErrorText!==text)return;errorText.value=value;errorText.hidden=false;errorText.focus();errorText.select();}});if(currentErrorText===text)copyStatus.textContent=copied?'Error details copied.':'Copy unavailable. Select and copy the details below.';};
function syncErrorDetails(){
 const details=errorDetails({state:presentationState,error:runtimeFailure,search:location.search,source:import.meta.url,capabilities:{webglApiPresent:typeof WebGLRenderingContext!=='undefined',webgl2ApiPresent:typeof WebGL2RenderingContext!=='undefined',secureContext:isSecureContext}});
 errorBox.hidden=!details;$('studio-poster').setAttribute('aria-hidden',String(!details));
 if(!details){currentErrorText='';errorText.value='';errorText.hidden=true;copyStatus.textContent='';return;}
 errorSummary.textContent=details.summary;if(currentErrorText!==details.text){currentErrorText=details.text;errorText.hidden=true;copyStatus.textContent='';}
}
if(new URLSearchParams(location.search).get('leather')==='compat12'){
 const warning=document.createElement('details');warning.id='atelier-leather-compat-warning';
 const summary=document.createElement('summary');summary.textContent='Reduced leather detail';
 const detail=document.createElement('p');detail.textContent=COMPAT_LEATHER_WARNING;warning.append(summary,detail);
 document.querySelector('.masthead').after(warning);document.body.dataset.leatherCompat='true';
 let lastHeight=-1;const measure=()=>{const height=Math.ceil(warning.getBoundingClientRect().height);if(height!==lastHeight){lastHeight=height;document.body.style.setProperty('--atelier-compat-height',`${height}px`);}};
 const observer=new ResizeObserver(measure);observer.observe(warning);measure();
 window.addEventListener('pagehide',()=>observer.disconnect());window.addEventListener('pageshow',event=>{if(event.persisted){observer.observe(warning);measure();}});
}
let presentationState={enabled:true,interactive:false,phase:'preparing',message:'Preparing the selected dial and leather.',warnings:[]};
let mode='explore', ready=false, failed=false, explodeAvailable=false, crownDragAvailable=false, explodeAmount=0, selectedBefore=false, selectedIdentity='';
const tools=$('atelier-tools');
const navigation=createAtelierNavigation();
const firstUseGuide=createFirstUseGuide({canvas:$('assembly-canvas'),host:$('atelier-stage-host')});
window.addEventListener('pagehide',event=>{if(!event.persisted)firstUseGuide.dispose();});
const inspectionControls=document.querySelector('.inspection-tools');
inspectionControls.remove();inspectionControls.hidden=false;
function syncNavigation(){
 const state=navigation.snapshot(),open=!$('context').hidden;
 document.body.dataset.experience=state.experience;
 document.querySelectorAll('[data-mode]').forEach(b=>{
  const next=b.dataset.mode,primary=b.closest('.task-dock')&&EXPERIENCE_MODES.includes(next);
  b.setAttribute('aria-pressed',String(primary?next===state.experience:open&&next===mode));
  b.setAttribute('aria-controls','context');
  b.setAttribute('aria-expanded',String(open&&next===mode));
 });
}
function returnFromSelection(){
 const state=navigation.returnFromSelection();
 setMode(state.tool||state.experience,{activate:false,navigate:false});
 if(!state.tool){closeContext();$('assembly-canvas').focus();}
 else $('close').focus();
}

let inspectionDisplay={wireframe:false,solidWireframe:false,transparent:false,transparentBackplate:false,hideStrap:false};
document.addEventListener('atelier:inspection-state',event=>{inspectionDisplay=event.detail;syncInspectionDisplay();});
function syncInspectionDisplay(){inspectionControls.querySelectorAll('[data-inspection]').forEach(button=>{
 button.disabled=!ready;button.setAttribute('aria-pressed',String(!!inspectionDisplay[button.dataset.inspection]));
 if(button.dataset.inspection==='hideStrap'){button.hidden=!inspectionDisplay.strapAvailable&&!inspectionDisplay.hideStrap;button.textContent=inspectionDisplay.hideStrap?'Strap hidden · Restore':'Hide strap';button.setAttribute('aria-label',inspectionDisplay.hideStrap?'Strap hidden for inspection. Restore strap assembly':'Hide strap for inspection');button.title='Inspection only: hide strap, keepers and buckle without changing case or rear cover. Explore and Reset restore the strap.';return;}
 if(button.dataset.inspection==='solidWireframe'){button.title='Shaded surfaces with triangle edges overlaid';return;}
 if(button.dataset.inspection==='transparent'){button.title='Translucent whole assembly for internal inspection';return;}
 button.title=button.dataset.inspection==='wireframe'?'Inspect current assembly triangles':(inspectionDisplay.backplateVisible?'Make only the rear cover transparent; supports stay intact.':'Rear cover is hidden in this view. This preference applies when the cover is visible again.');
});
 const labels={wireframe:'Wireframe',solidWireframe:'Solid + wire',transparent:'Transparent',transparentBackplate:'Clear backplate',hideStrap:'Strap hidden'};
 const active=Object.keys(labels).filter(key=>inspectionDisplay[key]);
 const more=document.querySelector('.atelier-more');
 if(more){more.textContent=active.length?`Studio tools · ${active.length}`:'Studio tools';more.dataset.inspectionActive=String(active.length>0);more.setAttribute('aria-label',active.length?`Studio tools. Active inspection: ${active.map(key=>labels[key]).join(', ')}`:'Appearance, components and diagnostics');more.title=active.length?`Active: ${active.map(key=>labels[key]).join(', ')}`:'Appearance, components and diagnostics';}
 const reset=$('atelier-inspection-reset');if(reset)reset.disabled=!ready||!active.length;
}

let panelOpener=null;
// BEGIN narrow panel layout measurement.
const panelMedia=matchMedia('(max-width:680px)');
let panelLayoutFrame=0,panelLayoutActive=false,lastPanelHeight=-1;
function measurePanelLayout(){
 panelLayoutFrame=0;if(!panelLayoutActive)return;
 const open=panelMedia.matches&&!$('context').hidden;
 const marker=String(open);if(document.body.dataset.panelOpen!==marker)document.body.dataset.panelOpen=marker;
 const height=open?Math.ceil($('context').getBoundingClientRect().height):0;
 if(height!==lastPanelHeight){lastPanelHeight=height;document.body.style.setProperty('--atelier-panel-height',`${height}px`);}
}
function schedulePanelLayout(){if(panelLayoutActive&&!panelLayoutFrame)panelLayoutFrame=requestAnimationFrame(measurePanelLayout);}
const panelLayoutObserver=new ResizeObserver(schedulePanelLayout);
function startPanelLayout(){if(panelLayoutActive)return;panelLayoutActive=true;panelLayoutObserver.observe($('context'));panelMedia.addEventListener('change',schedulePanelLayout);schedulePanelLayout();}
function stopPanelLayout(){panelLayoutActive=false;panelLayoutObserver.disconnect();panelMedia.removeEventListener('change',schedulePanelLayout);if(panelLayoutFrame)cancelAnimationFrame(panelLayoutFrame);panelLayoutFrame=0;}
window.addEventListener('pagehide',stopPanelLayout);
window.addEventListener('pageshow',event=>{if(event.persisted)startPanelLayout();});
startPanelLayout();
// END narrow panel layout measurement.

function closeContext(){if($('context').hidden)return;$('context').hidden=true;navigation.close();beginTaskStatus();schedulePanelLayout();syncNavigation();schedule();if(panelOpener?.isConnected&&!panelOpener.disabled)panelOpener.focus();else $('assembly-canvas').focus();}
const button=(text,id)=>`<button data-proxy="${id}">${text}</button>`;
const check=(text,id)=>`<label><input type="checkbox" data-check="${id}">${text}</label>`;
const templates={
 inside:()=>`<p class="panel-intro">Choose a mechanism, or select a part directly on the watch.</p><div class="tool-row"><button data-camera="balance">Balance</button><button data-camera="train">Gears</button><button data-camera="winding">Winding</button></div><div class="tool-stack inside-switches">${check('Follow the power','power-path')}${check('Slow motion','slow-motion')}</div><div class="tool-row">${button('Overview','interior-overview')}<button data-mode="components">Find a part</button>${button('Restore watch','show-all')}</div>`,
 explode:()=>`<p>Explore the watch layer by layer, including its working movement.</p><div class="slider-heading"><label for="atelier-explosion">Assembly separation</label><output id="atelier-explosion-value">${Math.round(explodeAmount*100)}%</output></div><input id="atelier-explosion" aria-describedby="atelier-explosion-note" type="range" min="0" max="100" value="${Math.round(explodeAmount*100)}" step="1" ${explodeAvailable?'':'disabled'}><div class="slider-labels"><span>Assembled</span><span>Exploded</span></div><div class="tool-row"><button id="atelier-explode-full" aria-label="Explode fully" ${explodeAvailable?'':'disabled'}><span class="explode-wide-label">Explode fully</span><span class="explode-compact-label" aria-hidden="true">Full</span></button><button id="atelier-reassemble" aria-label="Reassemble" ${explodeAvailable?'':'disabled'}><span class="explode-wide-label">Reassemble</span><span class="explode-compact-label" aria-hidden="true">Assemble</span></button></div><p class="tool-note" id="atelier-explosion-note" data-available="${explodeAvailable}">${explodeAvailable?'Drag to adjust. Mainplate, gear train, winding works, balance and bridges separate with their own bearings and fasteners. Motion pauses until reassembled.':'Exploded-view integration is not available yet. No parts will move.'}</p>`,
 time:()=>`<p id="atelier-crown-state"></p><p id="atelier-crown-help"></p><div class="tool-stack">${button('Pull out to set time','crown-pull')}</div><div class="tool-row">${button('Turn left','crown-left')}${button('Turn right','crown-right')}</div><div class="tool-row">${button('Focus crown','crown-focus')}<button type="button" data-reseat-crown>Reseat crown</button></div><p class="tool-note" id="atelier-crown-direct">Use these precise controls to wind or set time. Direct crown dragging is being integrated.</p>`,
 capture:()=>`<p class="capture-intro">Save this view or restore saved settings.</p><p id="atelier-detail-status" class="tool-note" role="status" tabindex="-1" hidden></p><button id="atelier-retry-detail" hidden>Retry detail</button><div class="tool-stack capture-actions">${button('Save PNG image','capture-scene')}${button('Save 8s video','record-scene')}${button('Save view · JSON','export-config')}<button id="atelier-import">Load view · JSON</button></div><p class="tool-note capture-support">Downloads stay on this device. Rendering builds every video frame and may take longer than 8 seconds. Older browsers use live recording.</p>`,
 quality:()=>`<p class="panel-intro">Choose detail for stills or smoother motion for interaction.</p><div class="tool-row quality-actions"><button data-quality="efficient">Smooth</button><button data-quality="balanced">Balanced</button><button data-quality="detail">Sharp</button><button data-quality="studio">Studio</button></div><p id="atelier-render-state" class="tool-note"></p>`,
 tour:()=>`<p>Six perspectives, from the complete watch to its mechanism. Drag to take control.</p><div class="tool-stack">${button('Start tour','tour')}</div><div class="tool-row">${button('Previous','tour-previous')}${button('Next','tour-next')}</div><p id="atelier-tour-state" class="tool-note"></p>`,
 components:()=>`<label for="atelier-search">Find a component</label><input id="atelier-search" type="search" placeholder="Crown, springbar, OM10…"><div class="tool-row"><button data-scope="all">All</button><button data-scope="exterior">Exterior</button><button data-scope="movement">Movement</button></div><p id="atelier-count" class="tool-note"></p><ul id="atelier-component-list" class="tool-list" aria-label="Components"></ul><div class="tool-row">${button('Restore watch','show-all')}${button('Clear selection','clear')}</div>`,
 selection:()=>`${navigation.snapshot().selectionReturn?'<button type="button" class="selection-back" data-return-selection>← Back to '+(titles[navigation.snapshot().selectionReturn.tool]||'the watch')+'</button>':''}<p id="atelier-part-role"></p><p id="atelier-part-support" class="tool-note"></p><div class="tool-row">${button('Isolate','isolate')}${button('Deselect','clear')}</div><div class="tool-row">${button('Restore watch','show-all')}<button data-mode="components">Find another part</button></div>`,
 settings:()=>`<section class="inspection-section" aria-labelledby="inspection-display-title"><h3 id="inspection-display-title">Inspection display</h3><div id="atelier-inspection-host"></div><button id="atelier-inspection-reset" type="button">Restore normal display</button></section><div class="tool-stack studio-switches">${check('Show glass','crystals')}${check('Movement only','movement-only')}</div><div class="tool-row"><button data-mode="components">Find a part</button><button data-mode="motion">Motion tools</button><button data-mode="tour">Guided tour</button></div><div class="tool-row studio-views" role="group" aria-label="Camera views"><button data-camera="three-quarter">Portrait</button><button data-camera="back">Reverse</button><button data-camera="side">Profile</button><button data-camera="lug">Lugs</button><button data-camera="buckle">Buckle</button></div><div id="atelier-design-retry" class="tool-row" hidden><button data-proxy="retry-proposal">Retry open-work design</button></div><div class="tool-row"><button data-mode="engineering">Engineering comparisons &amp; diagnostics</button></div>`,
 engineering:()=>`<p>Earlier geometry and inspection materials. Keep both selected for the current design.</p><div class="tool-stack">${check('Selected Left Crescent design (off: original solid dial)','open-work')}${check('Selected studio materials (off: clay inspection)','finish')}</div><div class="tool-row">${button('Measure','start-measurement')}${button('Refresh','refresh-diagnostics')}</div><pre id="atelier-diagnostics"></pre><a href="ATTRIBUTION.md" target="_blank" rel="noopener">Geometry, attribution &amp; license</a><p class="tool-note">Visual motion study; not a manufacturing or physical validation.</p>`,
 motion:()=>`<div class="tool-stack">${check('Mechanism motion','animate-movement')}${check('Hand motion','animate')}${check('Slow motion','slow-motion')}</div><label for="atelier-scrub">Inspect a moment</label><input id="atelier-scrub" type="range" min="0" max="60" step="0.01" value="0"><p id="atelier-scrub-value"></p><div class="tool-row">${button('Reset motion pose','reset-hands')}${button('Inspect mechanism','inspect-motion')}</div>`
};
const titles={inside:'Inside the watch',explode:'Separate layers',time:'Wind & set time',capture:'Save & restore.',quality:'Image quality',tour:'A guided closer look.',components:'Find a component.',selection:'Selected component',settings:'Studio tools',engineering:'Engineering comparisons',motion:'The rhythm within.'};
// BEGIN active task status.
// A task switch is not a new runtime announcement. Do not carry the previous
// task's last action into a newly opened panel; fresh runtime messages still win.
const taskStatusMessages={
 explore:'Drag to orbit, pinch or scroll to zoom, or select a part to inspect.',
 inside:'Explore the mechanism or choose a closer view.',
 explode:'Drag Assembly separation to reveal the layers. Reassemble returns them together.',
 time:'Turn the seated crown to wind, or pull it out to set the hands.',
 capture:'Save an image, record video, or save and restore this view as JSON.',
 quality:'Choose a quality preset.',
 tour:'Start the guided tour, or step between its perspectives.',
 components:'Find a component by name or choose a component group.',
 selection:'Inspect the selected part, isolate it, or restore the complete watch.',
 settings:'Adjust appearance, find components, or open motion tools.',
 engineering:'Compare historical geometry and materials, or inspect rendering diagnostics.',
 motion:'Control playback or inspect a moment in the mechanism.'
};
let taskStatusBaseline=null;
const taskStatusObserver=new MutationObserver(()=>{taskStatusBaseline=null;});
taskStatusObserver.observe($('viewer-status'),{subtree:true,childList:true,characterData:true});
function beginTaskStatus(){
 // Discard announcements queued before this switch, not new task actions.
 taskStatusObserver.takeRecords();taskStatusBaseline=$('viewer-status').textContent;
}
function activeTaskStatus(message){
 if(!ready||failed||presentationState.phase!=='ready')return message;
 return taskStatusBaseline!==null&&message===taskStatusBaseline?(taskStatusMessages[navigation.snapshot().tool||navigation.snapshot().experience]||message):message;
}
// END active task status.
function liveTarget(id){const target=$(id);return ready&&target&&!target.matches(':disabled')?target:null;}
function proxy(id){const t=liveTarget(id);if(!t)return false;t.click();queueMicrotask(sync);return true;}
function reseatCrown(){if($('crown-pull').getAttribute('aria-pressed')==='true')return proxy('crown-pull');return false;}
// BEGIN full-stage capture handoff.
let captureHandoffPending=false,exportNoticeActive=false,exportNoticeMessage=null;
function showExportNotice(message){
 let notice=$('atelier-export-notice');
 if(!notice){notice=document.createElement('p');notice.id='atelier-export-notice';notice.setAttribute('aria-hidden','true');
  // Visual counterpart of the existing live status, without reserving canvas space.
  notice.style.cssText='position:absolute;z-index:4;left:12px;right:12px;bottom:calc(126px + env(safe-area-inset-bottom,0px));margin:0;padding:8px 12px;border-radius:9px;background:#20231ff2;color:#eeeae1;font:12px/1.4 Arial;pointer-events:none;';
  document.querySelector('.atelier').append(notice);
 }
 notice.textContent=message;notice.hidden=!exportNoticeActive||!$('context').hidden;
}
let captureFrameSerial=0;
function waitForCaptureLayout(){
 return new Promise((resolve,reject)=>{
  let poll=0,previous='',stable=0,done=false,requestedSignature=null;
  const requestId=++captureFrameSerial;
  const finish=error=>{if(done)return;done=true;clearTimeout(poll);clearTimeout(timeout);window.removeEventListener('pagehide',cancel);document.removeEventListener('atelier:capture-frame-rendered',rendered);error?reject(error):resolve();};
  const cancel=()=>finish(new Error('Capture cancelled because the viewer closed.'));
  const timeout=setTimeout(()=>finish(new Error('The full watch view did not finish resizing. Please try again.')),60000);
  const dimensions=()=>{const r=$('stage').getBoundingClientRect(),canvas=$('assembly-canvas');return [r.width,r.height,canvas.width,canvas.height];};
  const valid=d=>d.every(v=>v>0)&&Math.abs(d[2]*d[1]-d[3]*d[0])<=d[0]+d[1];
  const closed=()=>$('context').hidden&&(!panelMedia.matches||document.body.dataset.panelOpen==='false');
  const rendered=event=>{
   if(event.detail?.requestId!==requestId||!requestedSignature)return;
   if(!$('context').hidden){finish(new Error('Capture cancelled because another tool was opened.'));return;}
   const d=dimensions(),signature=d.join(':');
   if(closed()&&valid(d)&&signature===requestedSignature&&event.detail.dimensions?.join(':')===signature)finish();
   else{requestedSignature=null;stable=0;previous='';}
  };
  window.addEventListener('pagehide',cancel,{once:true});document.addEventListener('atelier:capture-frame-rendered',rendered);
  const check=()=>{
   if(done)return;
   if(!$('context').hidden){finish(new Error('Capture cancelled because another tool was opened.'));return;}
   const d=dimensions(),signature=d.join(':');
   // Timer samples establish geometry stability without depending on GPU frame
   // cadence. A matching real composer-render acknowledgement is still required.
   stable=valid(d)&&closed()&&signature===previous?stable+1:0;previous=signature;
   if(requestedSignature&&signature!==requestedSignature)requestedSignature=null;
   if(stable>=2&&!requestedSignature){requestedSignature=signature;document.dispatchEvent(new CustomEvent('atelier:request-capture-frame',{detail:{requestId}}));}
   if(!done)poll=setTimeout(check,50);
  };
  check();
 });
}
async function captureAtFullStage(id){
 if(captureHandoffPending||!liveTarget(id))return;
 // Preserve any legacy stop/cancel mapping: these actions must be immediate.
 const target=liveTarget(id);
 if(id==='record-scene'&&(target.getAttribute('aria-pressed')==='true'||/^(cancel|stop)\b/i.test(target.textContent.trim()))){proxy(id);return;}
 if(captureDetail?.required&&!captureDetail.ready){syncCaptureDetail();updateText('status',captureDetail.message);return;}
 captureHandoffPending=true;exportNoticeActive=true;exportNoticeMessage='Preparing the full watch view…';showExportNotice(exportNoticeMessage);updateText('status',exportNoticeMessage);
 closeContext();
 try{await waitForCaptureLayout();exportNoticeMessage=null;taskStatusBaseline=null;if(!proxy(id))throw new Error('Capture is not available. Please try again when the watch is ready.');}
 catch(error){exportNoticeMessage=error.message;showExportNotice(exportNoticeMessage);updateText('status',exportNoticeMessage);}
 finally{captureHandoffPending=false;}
}
// END full-stage capture handoff.
function change(id,value){const t=liveTarget(id);if(!t)return;if(t.type==='checkbox')t.checked=value;else t.value=value;t.dispatchEvent(new Event('change',{bubbles:true}));sync();}
function camera(name){const target=bridge.querySelector(`[data-view="${name}"]`);if(ready&&target&&!target.matches(':disabled')){target.click();sync();}}
function setMode(next,{activate=true,navigate=true}={}){
 if(activate&&!ready&&['explore','inside','explode','time','capture','tour','quality','motion'].includes(next))return;
 if(activate&&ready&&['explore','inside','explode'].includes(next)&&$('crown-pull').getAttribute('aria-pressed')==='true')proxy('crown-pull');
 if(activate&&['explore','inside','time'].includes(next)&&explodeAmount>0)sendExplosion(0);
 if(navigate)navigation.open(next);
 mode=next;beginTaskStatus();$('context').dataset.tool=next;$('context').hidden=next==='explore';schedulePanelLayout();syncNavigation();
 if(next==='explore'){if(activate&&ready){proxy('clear');proxy('show-all');camera('face');}return;}
 $('context-title').textContent=titles[next];
 // Keep the original inspection controls alive as panels are replaced.
 inspectionControls.remove();tools.innerHTML=templates[next]?.()||'';
 $('atelier-inspection-host')?.append(inspectionControls);
 if(activate&&ready){if(next==='inside')camera('interior');if(next==='time')proxy('crown-focus');if(next==='explode')sendExplosion(1);}
 sync();
}
function syncCaptureDetail(){
 const pending=!!captureDetail?.required&&!captureDetail.ready;
 const note=$('atelier-detail-status'),retry=$('atelier-retry-detail');
 if(note){note.hidden=!pending&&!detailRetryRequested;note.textContent=pending?(captureDetail.phase==='failed'?'Full leather detail could not load. Your current view is preserved. Retry to enable image and video saving.':'Loading full leather detail for image and video saving…'):(detailRetryRequested?'Full leather detail ready. Image and video saving are available.':'');}
 if(retry){retry.hidden=!captureDetail?.retryAvailable&&!(detailRetryRequested&&pending);retry.disabled=!ready||captureDetail?.phase!=='failed';retry.textContent=captureDetail?.phase==='upgrading'?'Retrying…':'Retry detail';}
}
document.addEventListener('atelier:capture-detail-state',event=>{captureDetail=event.detail;sync();if(captureDetail?.ready&&document.activeElement===$('atelier-detail-status'))$('context').querySelector('[data-proxy="capture-scene"]')?.focus();});
function updateText(id,value){const el=$(id);if(el&&el.textContent!==value)el.textContent=value;}
function sync(){syncErrorDetails();if(!$('retry').hidden&&$('inspection-controls').disabled)failed=true;$('atelier-retry').hidden=!failed&&!['degraded','asset-error'].includes(presentationState.phase);if(failed||!presentationState.interactive)$('studio-poster').hidden=false;ready=!$('inspection-controls').disabled&&!failed&&presentationState.interactive;syncCaptureDetail();document.body.dataset.presentation=presentationState.phase;$('assembly-canvas').inert=!ready;document.body.dataset.ready=String(ready);firstUseGuide.update(ready&&$('context').hidden);document.body.dataset.failed=String(failed);document.body.dataset.comparison=String(ready&&(!$('open-work').checked||!$('finish').checked||$('mode-label').textContent==='ORIGINAL PART / TEMPORARY COMPARISON'));updateText('atelier-interaction-note',failed||presentationState.phase==='asset-error'?'3D interaction unavailable':'Select a part on the watch to inspect it');updateText('atelier-state-label',failed?'3D unavailable':presentationState.phase==='asset-error'?'Selected design unavailable':ready?(presentationState.phase==='degraded'?'Selected watch · additional assets unavailable':($('mode-label').textContent==='ORIGINAL PART / TEMPORARY COMPARISON'?'Engineering comparison · original part':!$('open-work').checked?'Engineering comparison · original solid dial':!$('finish').checked?'Engineering comparison · clay materials':'Live 3D · Aerial / Left Crescent')):'Preparing selected design');const presentationMessage=activeTaskStatus(ready||failed?$('viewer-status').textContent:presentationState.message);updateText('status',presentationMessage);updateText('atelier-panel-status',presentationMessage);$('atelier-panel-status').dataset.taskHint=String(ready&&!failed&&presentationState.phase==='ready'&&taskStatusBaseline!==null&&$('viewer-status').textContent===taskStatusBaseline);if(exportNoticeActive)showExportNotice(exportNoticeMessage??presentationMessage);if(!ready&&!failed)updateText('load-message',presentationState.message);updateText('atelier-motion-state',ready?($('crown-pull').getAttribute('aria-pressed')==='true'?'Setting time':$('animate-movement').checked||$('animate').checked?'Running':'Paused'):failed||presentationState.phase==='asset-error'?'Unavailable':'Loading');
 const running=$('play-motion').getAttribute('aria-pressed')==='true';updateText('motion-label',running?'Pause':'Play');if($('motion-icon').dataset.running!==String(running)){$('motion-icon').dataset.running=String(running);$('motion-icon').innerHTML=running?'<svg viewBox="0 0 24 24"><path d="M9 6v12M15 6v12"/></svg>':'<svg viewBox="0 0 24 24"><path d="m8 5 11 7-11 7Z"/></svg>';} $('motion').disabled=!liveTarget('play-motion');$('motion').setAttribute('aria-pressed',String(running));$('atelier-slow').disabled=!ready;$('atelier-slow').setAttribute('aria-pressed',String($('slow-motion').checked));$('home').disabled=!ready;syncInspectionDisplay();
 document.querySelectorAll('[data-mode]').forEach(button=>{if(['explore','inside','explode','time','capture','tour','quality','motion'].includes(button.dataset.mode))button.disabled=!ready;});
 document.querySelector('.quality-value').textContent=({efficient:'Smooth',detail:'Sharp',studio:'Studio',balanced:'Balanced'})[$('render-quality').value]||'Sharp';
 tools.querySelectorAll('[data-reseat-crown]').forEach(b=>{b.disabled=!liveTarget('crown-pull')||$('crown-pull').getAttribute('aria-pressed')!=='true';});
 tools.querySelectorAll('[data-proxy]').forEach(b=>{const t=$(b.dataset.proxy);b.disabled=!liveTarget(b.dataset.proxy);if(!t)return;if(['capture-scene','record-scene'].includes(b.dataset.proxy)&&captureDetail?.required&&!captureDetail.ready&&!(b.dataset.proxy==='record-scene'&&(t.getAttribute('aria-pressed')==='true'||/^(cancel|stop)\b/i.test(t.textContent.trim()))))b.disabled=true;if(['crown-pull','tour','record-scene'].includes(b.dataset.proxy))b.textContent=t.textContent;if(t.hasAttribute('aria-pressed'))b.setAttribute('aria-pressed',t.getAttribute('aria-pressed'));else b.removeAttribute('aria-pressed');});
 tools.querySelectorAll('[data-check]').forEach(x=>{x.checked=$(x.dataset.check).checked;x.disabled=!liveTarget(x.dataset.check);});tools.querySelectorAll('[data-camera]').forEach(b=>{b.disabled=!ready;const source=bridge.querySelector(`[data-view="${b.dataset.camera}"]`);b.setAttribute('aria-pressed',source?.getAttribute('aria-pressed')||'false');});tools.querySelectorAll('[data-quality]').forEach(b=>{b.disabled=!ready;b.setAttribute('aria-pressed',String(b.dataset.quality===$('render-quality').value));});
 updateText('atelier-crown-state',$('crown-state').textContent);updateText('atelier-crown-help',$('crown-help').textContent);updateText('atelier-render-state',$('render-status').textContent);updateText('atelier-tour-state',$('tour-step').textContent);updateText('atelier-part-role',$('part-role').textContent);updateText('atelier-part-support',$('part-support').textContent);updateText('atelier-diagnostics',$('diagnostics-report').textContent);updateText('atelier-scrub-value',$('scrub-value').textContent);
 if(mode==='selection')updateText('context-title',$('part-name').textContent||titles.selection);
 if(mode==='components'){updateText('atelier-count',$('search-count').textContent);const list=$('atelier-component-list'),source=$('component-list');if(list.dataset.signature!==source.innerHTML){list.innerHTML=source.innerHTML;list.querySelectorAll('button').forEach(b=>{b.removeAttribute('id');b.disabled=!ready;});list.dataset.signature=source.innerHTML;}tools.querySelectorAll('[data-scope]').forEach(b=>{b.disabled=!ready;b.setAttribute('aria-pressed',String(b.dataset.scope===$('component-scope').value));});$('atelier-search').disabled=!ready;if(document.activeElement!==$('atelier-search'))$('atelier-search').value=$('component-search').value;}
 if($('atelier-design-retry'))$('atelier-design-retry').hidden=!$('retry-proposal');if($('atelier-explosion'))$('atelier-explosion').disabled=!ready||!explodeAvailable;if($('atelier-reassemble'))$('atelier-reassemble').disabled=!ready||!explodeAvailable;if($('atelier-explode-full'))$('atelier-explode-full').disabled=!ready||!explodeAvailable;if($('atelier-import'))$('atelier-import').disabled=!ready;if($('atelier-scrub'))$('atelier-scrub').disabled=!ready;
 const selected=!$('selection').hidden,identity=selected?$('part-name').textContent:'';const newSelection=selected&&(!selectedBefore||identity!==selectedIdentity);const clearedSelection=!selected&&selectedBefore;selectedBefore=selected;selectedIdentity=identity;if(clearedSelection&&mode==='selection'&&!$('context').hidden)returnFromSelection();if(newSelection){navigation.select();setMode('selection',{activate:false,navigate:false});}if(crownDragAvailable)updateText('atelier-crown-direct','Drag the crown up or down to turn it. Click or tap the dot to pull or push. Hold and drag to turn; these buttons also work with touch and keyboard.');
}
document.addEventListener('click',event=>{const el=event.target.closest('button');if(!el||bridge.contains(el))return;if(el.dataset.inspection){if(ready)document.dispatchEvent(new CustomEvent('atelier:inspection',{detail:{key:el.dataset.inspection,value:!inspectionDisplay[el.dataset.inspection]}}));return;}if(el.dataset.mode){const next=el.dataset.mode;if(!$('context').contains(el))panelOpener=el;if(next==='explode'&&explodeAmount===0){setMode(next,{activate:true});return;}if(next===mode&&!$('context').hidden){closeContext();return;}const resume=next===navigation.snapshot().experience;setMode(next,{activate:!resume||next==='explore'});if(event.detail===0&&next!=='explore')$('close').focus();return;}if(el.hasAttribute('data-return-selection')){returnFromSelection();return;}if(el.id==='atelier-inspection-reset'){if(ready)for(const key of ['wireframe','solidWireframe','transparent','transparentBackplate','hideStrap'])if(inspectionDisplay[key])document.dispatchEvent(new CustomEvent('atelier:inspection',{detail:{key,value:false}}));return;}if(el.hasAttribute('data-reseat-crown')){reseatCrown();return;}if(el.dataset.proxy){if(['capture-scene','record-scene'].includes(el.dataset.proxy)){void captureAtFullStage(el.dataset.proxy);return;}proxy(el.dataset.proxy);if(el.dataset.proxy==='clear')$('assembly-canvas').focus();return;}if(el.dataset.camera){camera(el.dataset.camera);return;}if(el.dataset.quality){change('render-quality',el.dataset.quality);return;}if(el.dataset.scope){change('component-scope',el.dataset.scope);return;}if(el.dataset.key){const b=[...$('component-list').querySelectorAll('button')].find(x=>x.dataset.key===el.dataset.key);if(ready)b?.click();sync();if(mode!=='selection'){navigation.select();setMode('selection',{activate:false,navigate:false});}if(event.detail===0)$('close').focus();return;}if(el.id==='atelier-retry-detail'){detailRetryRequested=true;$('atelier-detail-status')?.focus({preventScroll:true});document.dispatchEvent(new CustomEvent('atelier:retry-capture-detail'));return;}if(el.id==='atelier-import')$('import-config').click();if(el.id==='atelier-reassemble')sendExplosion(0);if(el.id==='atelier-explode-full')sendExplosion(1);});
tools.addEventListener('change',e=>{if(e.target.dataset.check)change(e.target.dataset.check,e.target.checked);});
tools.addEventListener('input',e=>{if(e.target.id==='atelier-explosion')sendExplosion(Number(e.target.value)/100,{instant:true});if(e.target.id==='atelier-search'){const t=liveTarget('component-search');if(t){t.value=e.target.value;t.dispatchEvent(new Event('input',{bubbles:true}));sync();}}if(e.target.id==='atelier-scrub'){const t=liveTarget('scrub-time');if(t){t.value=e.target.value;t.dispatchEvent(new Event('input',{bubbles:true}));sync();}}});
$('atelier-retry').onclick=()=>location.reload();
$('motion').onclick=()=>proxy('play-motion');$('atelier-slow').onclick=()=>change('slow-motion',!$('slow-motion').checked);$('home').onclick=()=>{proxy('reset');setMode('explore',{activate:false});$('assembly-canvas').focus();};$('close').onclick=closeContext;
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!e.target.closest('#runtime-bridge')&&!$('context').hidden){e.preventDefault();e.stopImmediatePropagation();closeContext();return;}if(e.key==='Home'&&!['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)){e.preventDefault();$('home').click();}});
function sendExplosion(amount,{instant=false}={}){if(!ready||!explodeAvailable)return;explodeAmount=Math.max(0,Math.min(1,amount));document.dispatchEvent(new CustomEvent('atelier:explode',{detail:{amount:explodeAmount,instant}}));if($('atelier-explosion'))$('atelier-explosion').value=String(explodeAmount*100);updateText('atelier-explosion-value',`${Math.round(explodeAmount*100)}%`);}
document.addEventListener('atelier:mode',e=>{if(e.detail?.mode==='time')setMode('time',{activate:false});});
document.addEventListener('atelier:capabilities',e=>{explodeAvailable=e.detail?.explode===true;crownDragAvailable=e.detail?.crownDrag===true;if(mode==='explode')setMode('explode',{activate:false});if(e.detail?.crownDrag)updateText('atelier-crown-direct','Drag the crown up or down to turn it. Click or tap the dot to pull or push. Hold and drag to turn; these buttons also work with touch and keyboard.');});
// BEGIN restore-state synchronization (also exercised by the focused Node tests).
function resolveRestoredAtelierMode(detail){
 if(Number(detail.amount)>0)return 'explode';
 if(detail.crownPulled||detail.view==='crown')return 'time';
 if(detail.selected)return 'selection';
 if(detail.isolated)return 'components';
 if(detail.interior)return 'inside';
 return 'explore';
}
function handleAtelierExplosionState(event){
 const detail=event.detail||{};
 explodeAmount=Math.max(0,Math.min(1,Number(detail.amount)||0));
 if($('atelier-explosion'))$('atelier-explosion').value=String(Math.round(explodeAmount*100));
 updateText('atelier-explosion-value',`${Math.round(explodeAmount*100)}%`);
 if(detail.reason!=='restore')return;
 const restoreFocus=$('context').contains(document.activeElement)||document.activeElement===$('import-config')||document.activeElement===document.body;
 // Adopt the already-restored selection before sync() observes it. Never select,
 // reseat the crown, reset the explosion, or move the imported camera here.
 selectedBefore=!$('selection').hidden;selectedIdentity=selectedBefore?$('part-name').textContent:'';
 const nextMode=resolveRestoredAtelierMode({...detail,amount:explodeAmount});
 panelOpener=document.querySelector(`.task-dock [data-mode="${nextMode}"]`)||document.querySelector('.atelier-more');
 navigation.restore({experience:Number(detail.amount)>0?'explode':detail.crownPulled||detail.view==='crown'?'time':detail.interior?'inside':'explore',tool:nextMode==='explore'?null:nextMode});
 setMode(nextMode,{activate:false,navigate:false});
 if(restoreFocus)$(nextMode==='explore'?'assembly-canvas':'close').focus();
}
document.addEventListener('atelier:explode-state',handleAtelierExplosionState);
// END restore-state synchronization.

document.addEventListener('atelier:presentation-state',event=>{
 presentationState=event.detail;
 const identity=document.querySelector('.atelier-loading-identity span');
 if(identity)identity.textContent=presentationState.phase==='asset-error'?'Selected design unavailable — reload to retry':'Preparing the selected watch';
 if(presentationState.phase==='error')failed=true;
 // Runtime alone reveals the rendered canvas after a successful composed frame.
 schedule();
});
let scheduled=false;const schedule=()=>{if(!scheduled){scheduled=true;requestAnimationFrame(()=>{scheduled=false;sync();});}};
new MutationObserver(schedule).observe(bridge,{subtree:true,childList:true,attributes:true,characterData:true});document.addEventListener('studio-state-change',schedule);bridge.addEventListener('change',schedule);sync();
try{await import('./assembly-review.js?v=atelier-local-1');document.dispatchEvent(new CustomEvent('atelier:request-presentation-state'));document.dispatchEvent(new CustomEvent('atelier:request-capabilities'));document.dispatchEvent(new CustomEvent('atelier:request-capture-detail'));schedule();}catch(error){console.error(error);failed=true;runtimeFailure=error;$('loading').hidden=false;$('load-message').textContent='3D graphics could not start in this browser. Reload to try again.';$('viewer-status').textContent='3D unavailable. Try a WebGL-capable browser.';$('assembly-canvas').setAttribute('aria-busy','false');$('studio-poster').hidden=false;sync();}

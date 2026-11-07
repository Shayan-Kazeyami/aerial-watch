import {test,expect} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {installStreamProbe,readStreamProbe} from './install-stream-probe.mjs';
const target=process.env.WATCH_QA_URL||'http://127.0.0.1:8765/atelier-preview.html?quality=efficient';
const expectedSourceDigest=process.env.WATCH_EXPECTED_SOURCE_DIGEST||'9d5499951d55619883ae6a30b1bf86a6db1a2af5835554528a42b8018a5a9c94';
const capSHA='f7876b6be8b445a8e72db355fd1dd2705bec13dc19754884ac765c90f8ee7ea2';
const guardedRejection=/Could not record: The browser (?:produced an incomplete or invalid video clip|captured too little motion for a usable clip)/;
async function ready(page){await page.waitForFunction(()=>{const s=window.assemblyInspect?.(),c=s?.comparisonLoading;return s&&!s.loading&&!s.failed&&s.presentation?.phase==='ready'&&s.presentation.interactive&&!s.presentation.pending.length&&!c?.loading&&!c?.failure&&(!c?.needed||(c.formReady&&c.architectureReady));},null,{timeout:240000});}
async function capturePanel(page){if(!await page.locator('#context').isVisible()||await page.locator('#context').getAttribute('data-tool')!=='capture')await page.locator('.task-dock [data-mode="capture"]').click();await expect(page.locator('#context')).toBeVisible();await expect(page.locator('#context')).toHaveAttribute('data-tool','capture');}
async function state(page){return page.evaluate(()=>{const s=window.assemblyInspect(),c=document.getElementById('assembly-canvas');return {at:performance.now(),quality:s.renderQuality,animation:s.animation,interiorAnimation:s.interiorAnimation,mechanismElapsed:s.mechanismElapsed,illustrativeElapsed:s.illustrativeElapsed,canvas:{width:c.width,height:c.height,clientWidth:c.clientWidth,clientHeight:c.clientHeight},recordDisabled:document.getElementById('record-scene').disabled,status:document.getElementById('viewer-status').textContent,notice:document.getElementById('atelier-export-notice')?.textContent};});}
function decode(path,elapsedMs){
 const ffprobe=JSON.parse(execFileSync('ffprobe',['-v','error','-show_format','-show_streams','-count_frames','-of','json',path],{encoding:'utf8',timeout:60000}));
 const frames=JSON.parse(execFileSync('ffprobe',['-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time,pkt_duration_time','-of','json',path],{encoding:'utf8',timeout:60000}));
 const md5=execFileSync('ffmpeg',['-v','error','-i',path,'-map','0:v:0','-an','-f','framemd5','-'],{encoding:'utf8',timeout:90000,maxBuffer:8*1024*1024});
 const video=ffprobe.streams.find(s=>s.codec_type==='video'),times=frames.frames.map(x=>Number(x.best_effort_timestamp_time)).filter(Number.isFinite),hashes=md5.split('\n').filter(l=>l.trim()&&!l.startsWith('#')).map(l=>l.split(',').at(-1).trim());
 const spanSeconds=times.length?times.at(-1)-times[0]:0,distinctFrameHashes=new Set(hashes).size,meanDecodedCadence=spanSeconds>0?(times.length-1)/spanSeconds:0;
 return {ffprobe,frames,md5,video,times,spanSeconds,decodedFrames:hashes.length,distinctFrameHashes,meanDecodedCadence,nativeCaptureElapsedMs:elapsedMs};
}
test('real native stream guard contract: invalid or sparse clips withheld, resources released, one explicit requestFrame attempt',async({page},info)=>{
 test.setTimeout(720000);page.setDefaultTimeout(45000);
 const evidence={scope:'Actual native canvas stream and MediaRecorder, EXPLICIT requestFrame experiment, one attempt. Guard/error recovery acceptance is NOT usable-video success. Hosted SwiftShader is not physical S24, hardware performance or WebGPU acceptance.',attempts:[],errors:[],downloads:[],guardContractVerified:false,usableRecordingVerified:false};
 const downloads=[];page.on('download',d=>downloads.push(d));page.on('pageerror',e=>evidence.errors.push({type:'pageerror',message:e.message}));page.on('console',m=>{if(m.type()==='error')evidence.errors.push({type:'console-error',message:m.text()});});
 await installStreamProbe(page,{requestFrames:true}); // Explicit diagnostic, not a production change.
 try{
  await page.goto(target,{waitUntil:'domcontentloaded'});await ready(page);await page.locator('#home').click();await ready(page);
  // Read real exported runtime identity before recording. This is a JSON download, not a clip.
  await capturePanel(page);const identityPending=page.waitForEvent('download',{timeout:90000});await page.locator('#atelier-tools [data-proxy="export-config"]').click();const identityDownload=await identityPending;expect(await identityDownload.failure()).toBeNull();const identityPath=info.outputPath('runtime-identity.json');await identityDownload.saveAs(identityPath);const identity=JSON.parse(await readFile(identityPath,'utf8'));expect(identity.sourceAtCapture.status).toBe('verified');expect(identity.sourceAtCapture.digest).toBe(expectedSourceDigest);expect(identity.capRefinement.active).toBe(true);expect(identity.capRefinement.candidatePositionSHA256).toBe(capSHA);evidence.runtimeIdentity={cap:identity.capRefinement,source:identity.sourceAtCapture,renderer:identity.renderer,options:identity.options};
  evidence.adapter=await page.evaluate(()=>{const c=document.getElementById('assembly-canvas'),g=c.getContext('webgl2')||c.getContext('webgl'),x=g?.getExtension('WEBGL_debug_renderer_info');return {userAgent:navigator.userAgent,unmaskedRenderer:x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):null,support:{captureStream:typeof c.captureStream==='function',mediaRecorder:typeof MediaRecorder==='function',webm:typeof MediaRecorder==='function'&&MediaRecorder.isTypeSupported('video/webm')}};});
  expect(evidence.adapter.support.captureStream).toBe(true);expect(evidence.adapter.support.mediaRecorder).toBe(true);expect(evidence.adapter.support.webm).toBe(true);
  await page.locator('#close').click();if(await page.locator('#motion').getAttribute('aria-pressed')!=='true')await page.locator('#motion').click();await expect(page.locator('#motion')).toHaveAttribute('aria-pressed','true');
  for(let attempt=0;attempt<1;attempt++){
   await capturePanel(page);const proxy=page.locator('#atelier-tools [data-proxy="record-scene"]');await expect(proxy).toBeEnabled();const before=await state(page);expect(before.animation||before.interiorAnimation).toBe(true);
   const start=await readStreamProbe(page),recorderOffset=start.recorders.length,streamOffset=start.streams.length,downloadOffset=downloads.length;const result={attempt,before};evidence.attempts.push(result);
   await proxy.click();
   // Require a real native recorder start. A resize/preparation timeout is NOT a passing recording guard test.
   await expect.poll(async()=>{const p=await readStreamProbe(page);return p.recorders.slice(recorderOffset).some(r=>r.events.some(e=>e.name==='start'));},{timeout:60000,message:'Native MediaRecorder must start'}).toBe(true);
   await expect.poll(async()=>{const p=await readStreamProbe(page),st=await state(page);return p.recorders.slice(recorderOffset).some(r=>r.events.some(e=>e.name==='stop'&&e.state==='inactive'))&&!st.recordDisabled&&(downloads.length>downloadOffset||guardedRejection.test(st.status)||guardedRejection.test(st.notice||''));},{timeout:90000,message:'Real recorder must settle to a guarded rejection or actual download'}).toBe(true);
   await expect.poll(async()=>{const p=await readStreamProbe(page),tracks=p.streams.slice(streamOffset).flatMap(s=>s.tracks);return tracks.length>0&&tracks.every(t=>t.samples.at(-1)?.readyState==='ended');},{timeout:10000,message:'All native canvas video tracks must end'}).toBe(true);
   result.after=await state(page);const p=await readStreamProbe(page);result.streams=p.streams.slice(streamOffset);result.recorders=p.recorders.slice(recorderOffset);expect(p.mode).toBe('EXPERIMENT explicit track.requestFrame every250ms');expect(result.streams).toHaveLength(1);expect(result.recorders).toHaveLength(1);for(const t of result.streams.flatMap(s=>s.tracks)){expect(t.requests).toBeGreaterThan(0);expect(t.samples.at(-1).readyState).toBe('ended');}
   expect(result.after.quality).toBe(before.quality);expect(result.after.canvas).toEqual(before.canvas);expect(result.after.animation).toBe(before.animation);expect(result.after.interiorAnimation).toBe(before.interiorAnimation);
   result.playbackAdvanced=result.after.mechanismElapsed>before.mechanismElapsed||result.after.illustrativeElapsed>before.illustrativeElapsed;expect(result.playbackAdvanced).toBe(true);
   const clips=downloads.slice(downloadOffset);expect(clips.length).toBeLessThanOrEqual(1);
   if(clips.length===0){
    expect(guardedRejection.test(result.after.status)||guardedRejection.test(result.after.notice||'')).toBe(true);await expect(page.locator('#atelier-export-notice')).toBeVisible();await expect(page.locator('#atelier-export-notice')).toContainText(guardedRejection);
    result.outcome='GUARDED_REJECTION_NO_DOWNLOAD';result.usableRecording='UNVERIFIED';await page.screenshot({path:info.outputPath('guarded-rejection-'+attempt+'.png'),timeout:45000});
    // Keep watching through a bounded idle turn so a late invalid download is not missed.
    await page.waitForTimeout(1000);expect(downloads.length).toBe(downloadOffset);
   }else{
    const d=clips[0];expect(await d.failure()).toBeNull();const path=info.outputPath('native-attempt-'+attempt+'.webm');await d.saveAs(path);const bytes=await readFile(path);result.outcome='DOWNLOAD_PENDING_DECODE_AND_CADENCE';result.download={path,bytes:bytes.length};evidence.downloads.push(result.download);expect([...bytes.subarray(0,4)]).toEqual([26,69,223,163]);
    const native=result.recorders[0],started=native.events.find(e=>e.name==='start'),stopped=native.events.find(e=>e.name==='stop');const decoded=decode(path,stopped.at-started.at);await writeFile(info.outputPath('decode-'+attempt+'.json'),JSON.stringify({...decoded,md5:undefined},null,2));await writeFile(info.outputPath('frames-'+attempt+'.md5'),decoded.md5);result.decoded={frames:decoded.decodedFrames,spanSeconds:decoded.spanSeconds,meanDecodedCadence:decoded.meanDecodedCadence,distinctFrameHashes:decoded.distinctFrameHashes,nativeCaptureElapsedMs:decoded.nativeCaptureElapsedMs};
    expect(decoded.video).toBeTruthy();expect(decoded.video.width).toBe(before.canvas.width);expect(decoded.video.height).toBe(before.canvas.height);expect(decoded.decodedFrames).toBeGreaterThan(1);expect(decoded.distinctFrameHashes).toBeGreaterThan(1);expect(decoded.meanDecodedCadence).toBeGreaterThanOrEqual(8);expect(decoded.spanSeconds*1000).toBeGreaterThanOrEqual(decoded.nativeCaptureElapsedMs*.75);
    result.outcome='ACTUAL_DOWNLOAD_DECODED_MOTION_AND_CADENCE';result.usableRecording='VERIFIED_FOR_THIS_SOFTWARE_RUN_ONLY';
   }
   await capturePanel(page);await expect(page.locator('#atelier-tools [data-proxy="record-scene"]')).toBeEnabled();result.buttonRestored=true;
  }
  expect(evidence.errors).toEqual([]);evidence.guardContractVerified=true;evidence.usableRecordingVerified=evidence.attempts.every(a=>a.outcome==='ACTUAL_DOWNLOAD_DECODED_MOTION_AND_CADENCE');
  if(!evidence.usableRecordingVerified)test.info().annotations.push({type:'incomplete',description:'Guard safely rejected native output; usable recording remains unverified. This is not overall video acceptance.'});
 }finally{
  evidence.finalStreamProbe=await readStreamProbe(page).catch(()=>null);evidence.finalState=await state(page).catch(()=>null);evidence.finalURL=page.url();await writeFile(info.outputPath('recording-guard-evidence.json'),JSON.stringify(evidence,null,2));
 }
});

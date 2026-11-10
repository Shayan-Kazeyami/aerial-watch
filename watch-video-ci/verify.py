import asyncio, json, pathlib, os, hashlib, subprocess, traceback
from playwright.async_api import async_playwright
HOME='https://shayan-kazeyami.github.io/aerial-watch/'
RID='36f0aca93a5c9e1cf01e0237aabcc0c71ee96fbfc2cc64394b74b35c32cf75e8'
MODE=os.environ.get('MODE','headed')
OUT=pathlib.Path('webm-evidence');OUT.mkdir(exist_ok=True)
R={'target':HOME,'release':RID,'mode':MODE,'errors':[],'checks':[]}
def save():
 (OUT/'report.json').write_text(json.dumps(R,indent=2));print('REPORT '+json.dumps(R),flush=True)
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=False,channel='chromium',args=['--no-sandbox','--disable-dev-shm-usage','--use-angle='+('gl' if MODE=='mesa' else 'swiftshader'),'--enable-unsafe-swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows'])
  try:
   ctx=await browser.new_context(viewport={'width':640,'height':480},accept_downloads=True,device_scale_factor=1)
   await ctx.add_init_script("""(()=>{window.__recordQA={raf:0,events:[],captures:[]};const q=window.__recordQA,raf=requestAnimationFrame.bind(window);window.requestAnimationFrame=fn=>raf(t=>{q.raf++;fn(t)});const cap=HTMLCanvasElement.prototype.captureStream;HTMLCanvasElement.prototype.captureStream=function(f){q.captures.push({width:this.width,height:this.height,rate:f,raf:q.raf,t:performance.now()});return cap.call(this,f)};const start=MediaRecorder.prototype.start,stop=MediaRecorder.prototype.stop;MediaRecorder.prototype.start=function(...a){q.events.push({type:'start',raf:q.raf,t:performance.now(),mime:this.mimeType});this.addEventListener('dataavailable',e=>{q.events.push({type:'data',bytes:e.data.size,raf:q.raf,t:performance.now()});q.blob=e.data});this.addEventListener('stop',()=>q.events.push({type:'stopped',raf:q.raf,t:performance.now()}));return start.apply(this,a)};MediaRecorder.prototype.stop=function(...a){q.events.push({type:'stop-request',raf:q.raf,t:performance.now()});return stop.apply(this,a)}})()""")
   page=await ctx.new_page();page.set_default_timeout(90000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
   await page.goto(HOME+'preview-b/releases/'+RID+'/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&verify=webm-'+MODE,wait_until='domcontentloaded',timeout=90000)
   frame=page;await frame.locator('body[data-ready="true"]').wait_for(timeout=240000)
   inner=page;R['frame']=inner.url;R['browser']=browser.version
   R['before']=await inner.evaluate('(()=>{const s=assemblyInspect();return {quality:s.renderQuality,viewport:s.viewport,presentation:s.presentation,GPU:s.GPU,performance:s.performance,clock:s.clock}})()');R['checks'].append('same live immutable viewer opened top-level at 640x480 with Smooth quality');save()
   await frame.locator('.task-dock [data-mode=capture]').click()
   try:
    async with page.expect_download(timeout=90000) as pending:
     await frame.locator('[data-proxy=record-scene]').click()
    dl=await pending.value;path=OUT/'aerial-watch.webm';await dl.save_as(path)
    R['download']={'name':dl.suggested_filename,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    probe=subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=60);assert probe.returncode==0,probe.stderr;R['ffprobe']=json.loads(probe.stdout)
    decode=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True,timeout=120);assert decode.returncode==0,decode.stderr;R['decode']={'returncode':decode.returncode,'stderr':decode.stderr}
    video=next(s for s in R['ffprobe']['streams'] if s['codec_type']=='video');assert int(video['nb_read_frames'])>=64,video
    frames=subprocess.run(['ffmpeg','-y','-v','error','-i',str(path),'-vf','fps=1','-frames:v','8',str(OUT/'frame-%02d.png')],capture_output=True,text=True,timeout=120);assert frames.returncode==0,frames.stderr
    R['checks'].append('real Save video downloaded and ffmpeg decoded at least 64 frames');R['passed']=True
   except Exception as e:R['passed']=False;R['recordingFailure']=repr(e)
   R['diagnostic']=await inner.evaluate('(()=>{const q=window.__recordQA;return {raf:q.raf,events:q.events,captures:q.captures,status:document.getElementById("viewer-status").textContent,recordDisabled:document.getElementById("record-scene").disabled,visibility:document.visibilityState}})()')
   if not R['passed']:
    blob=await inner.evaluate('async()=>window.__recordQA.blob?Array.from(new Uint8Array(await window.__recordQA.blob.arrayBuffer())):null')
    if blob:(OUT/'rejected.webm').write_bytes(bytes(blob))
   assert not R['errors'],R['errors'];assert R['passed'],R.get('recordingFailure')
  except Exception as e:
   R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   save()
   try:await asyncio.wait_for(browser.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

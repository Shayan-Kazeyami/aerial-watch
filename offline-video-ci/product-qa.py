import asyncio,json,pathlib,hashlib,time,traceback,av
from PIL import Image
from playwright.async_api import async_playwright
O=pathlib.Path('offline-output');BUILD=json.loads((O/'build.json').read_text());SCOPE=__import__('os').environ.get('QA_SCOPE','desktop');R={'build':BUILD,'scope':SCOPE,'errors':[],'checks':[]}
def save():
 (O/(SCOPE+'-report.json')).write_text(json.dumps(R,indent=2));print('REPORT '+json.dumps(R),flush=True)
def record(name):R['checks'].append(name);save()
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   mobile=SCOPE=='mobile';ctx=await browser.new_context(viewport={'width':430 if mobile else 640,'height':700 if mobile else 480},accept_downloads=True,is_mobile=mobile,has_touch=mobile)
   await ctx.add_init_script("""(()=>{const native=VideoEncoder.isConfigSupported.bind(VideoEncoder);VideoEncoder.isConfigSupported=config=>window.__holdVideoSetup?new Promise(resolve=>{window.__releaseVideoSetup=()=>native(config).then(resolve)}):native(config)})()""")
   page=await ctx.new_page();page.set_default_timeout(120000);page.on('pageerror',lambda e:R['errors'].append(str(e)));downloads=[];page.on('download',lambda d:downloads.append(d))
   url='http://127.0.0.1:8765/'+BUILD['releasePath']+'/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa'
   await page.goto(url,wait_until='domcontentloaded');await page.locator('body[data-ready="true"]').wait_for(timeout=240000);await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"')
   actual=await page.evaluate('fetch("./quality-study/viewer-revision.json").then(r=>r.json())');assert actual['digest']==BUILD['revision'];R['browser']=browser.version;R['source']=url;record('expected immutable candidate loaded')
   async def start():
    await page.locator('.task-dock [data-mode=capture]').click();assert await page.locator('[data-proxy=record-scene]').text_content()=='Render 8s video';await page.locator('[data-proxy=record-scene]').click()
   async def inactive():await page.wait_for_function('!assemblyInspect().videoExport.active && !document.getElementById("record-scene").disabled',timeout=90000)
   if await page.locator('#motion').get_attribute('aria-pressed')=='true':await page.locator('#motion').click()
   before=await page.evaluate('assemblyInspect()');assert not before['animation'] and not before['interiorAnimation']
   await page.evaluate('window.__holdVideoSetup=true');await start();await page.locator('.aerial-video-dialog[open]').wait_for();assert await page.locator('.aerial-video-dialog button').is_enabled();await page.locator('.aerial-video-dialog button').click();await inactive();await page.evaluate('window.__holdVideoSetup=false;window.__releaseVideoSetup()');await page.wait_for_timeout(100)
   after=await page.evaluate('assemblyInspect()');assert before['camera']==after['camera'] and before['target']==after['target'] and before['mechanismElapsed']==after['mechanismElapsed'];assert not downloads;assert await page.locator('.aerial-video-dialog').get_attribute('open') is None
   assert await page.evaluate('document.activeElement===document.querySelector(".task-dock [data-mode=capture]")');record('Cancel remains available during stalled encoder setup; exact paused state and keyboard focus restore')
   await start();await page.wait_for_function('assemblyInspect().videoExport.progress?.completed>=2',timeout=120000);await page.keyboard.press('Escape');await inactive();after=await page.evaluate('assemblyInspect()');assert before['camera']==after['camera'] and before['mechanismElapsed']==after['mechanismElapsed'];assert not downloads;record('Escape cancels partial render without download and restores the paused pose')
   await start();await page.wait_for_function('assemblyInspect().videoExport.progress?.completed>=1',timeout=120000);await page.set_viewport_size({'width':440 if mobile else 660,'height':700 if mobile else 480});await inactive();assert not downloads;record('resizing cancels safely with no mixed-size video')
   await page.set_viewport_size({'width':430 if mobile else 640,'height':700 if mobile else 480});await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"')
   if mobile:
    await page.locator('#home').click();assert await page.locator('.task-dock [data-mode=explore]').get_attribute('aria-pressed')=='true';record('mobile Reset works after repeated cancellation');R['passed']=True;assert not R['errors'];return
   # A delayed saved-view file read must finish before export is allowed to start.
   await page.evaluate("""(()=>{const native=File.prototype.text;File.prototype.text=function(){return new Promise(resolve=>window.__releaseImport=()=>native.call(this).then(resolve))}})()""")
   await page.locator('#import-config').set_input_files({'name':'pending-view.json','mimeType':'application/json','buffer':b'{}'})
   await start();await page.wait_for_function('document.getElementById("viewer-status").textContent.includes("Wait for the saved view")');assert not await page.evaluate('assemblyInspect().videoExport.active');await page.evaluate('__releaseImport()');await page.wait_for_function('document.getElementById("import-config").value===""');record('pending saved-view import cannot race a video render')
   await page.locator('#motion').click();assert await page.locator('#motion').get_attribute('aria-pressed')=='true';before=await page.evaluate('assemblyInspect()');R['beforeFull']=before;save()
   started=time.monotonic()
   async with page.expect_download(timeout=1800000) as pending:
    await start()
    for _ in range(360):
     await page.wait_for_timeout(5000)
     state=await page.evaluate('assemblyInspect().videoExport');print('VIDEO_PROGRESS '+json.dumps(state),flush=True)
     if not state['active']:break
   dl=await pending.value;path=O/'aerial-eight-second-motion.webm';await dl.save_as(path);R['renderSeconds']=time.monotonic()-started;await inactive();after=await page.evaluate('assemblyInspect()');R['afterFull']=after
   assert before['camera']==after['camera'] and before['target']==after['target'];assert before['animation']==after['animation'] and before['interiorAnimation']==after['interiorAnimation'];assert not after['videoExport']['active']
   container=av.open(str(path));stream=container.streams.video[0];frames=list(container.decode(video=0));assert len(frames)==240
   R['decoder']={'name':'PyAV / FFmpeg','codec':stream.codec_context.name,'width':stream.width,'height':stream.height,'frames':len(frames),'duration':container.duration/av.time_base,'timestamps':[float(f.pts*f.time_base) for f in frames]};assert abs(R['decoder']['duration']-8)<.01;assert all(abs(t-i/30)<.0011 for i,t in enumerate(R['decoder']['timestamps']))
   hashes=[]
   for i,frame in enumerate(frames):
    rgb=frame.reformat(format='rgb24');raw=bytes(rgb.planes[0]);stride=rgb.planes[0].line_size;packed=b''.join(raw[y*stride:y*stride+rgb.width*3] for y in range(rgb.height));hashes.append(hashlib.sha256(packed).hexdigest())
    if i in [0,60,120,180,239]:Image.frombytes('RGB',(rgb.width,rgb.height),packed).save(O/f'frame-{i:03d}.png')
   R['uniqueDecodedFrames']=len(set(hashes));assert len(set(hashes))>=230;(O/'frame-hashes.json').write_text(json.dumps(hashes));container.seek(6*av.time_base);seekframe=next(container.decode(video=0));R['seekTimestamp']=float(seekframe.pts*seekframe.time_base);assert abs(R['seekTimestamp']-6)<.05;container.close()
   R['download']={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};assert len(downloads)==1;assert not R['errors'],R['errors'];record('actual UI produced a complete seekable eight-second 240-frame watch video and restored live controls');R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   save()
   try:await asyncio.wait_for(browser.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

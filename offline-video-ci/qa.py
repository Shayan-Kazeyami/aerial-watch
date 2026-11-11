import asyncio,json,pathlib,subprocess,hashlib,time,traceback,av
from PIL import Image
from playwright.async_api import async_playwright
O=pathlib.Path('offline-output');RID='36f0aca93a5c9e1cf01e0237aabcc0c71ee96fbfc2cc64394b74b35c32cf75e8'
R={'identity':json.loads((O/'identity.json').read_text()),'errors':[]}
def save():
 (O/'report.json').write_text(json.dumps(R,indent=2));print('REPORT '+json.dumps(R),flush=True)
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   ctx=await browser.new_context(viewport={'width':640,'height':480},accept_downloads=True);page=await ctx.new_page();page.set_default_timeout(120000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
   url=f'http://127.0.0.1:8765/preview-b/releases/{RID}/qa-offline.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa'
   await page.goto(url,wait_until='domcontentloaded');await page.locator('body[data-ready="true"]').wait_for(timeout=240000)
   await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"');R['browser']=browser.version;R['source']=url;R['before']=await page.evaluate('assemblyInspect()');save()
   started=time.monotonic()
   async with page.expect_download(timeout=600000) as pending:
    result=await page.evaluate('__offlineQA.start(2000)')
   dl=await pending.value;path=O/'aerial-offline-motion.webm';await dl.save_as(path);R['renderSeconds']=time.monotonic()-started;R['run']=result
   assert result['before']['camera']==result['after']['camera'];assert result['before']['target']==result['after']['target'];assert not result['after']['busy']
   container=av.open(str(path));stream=container.streams.video[0];frames=list(container.decode(video=0));assert len(frames)==60
   R['decoder']={'name':'PyAV / FFmpeg','codec':stream.codec_context.name,'width':stream.width,'height':stream.height,'frames':len(frames),'duration':container.duration/av.time_base,'timestamps':[float(f.pts*f.time_base) for f in frames]}
   assert abs(R['decoder']['duration']-2)<.01
   assert all(abs(t-i/30)<.0011 for i,t in enumerate(R['decoder']['timestamps']))
   hashes=[]
   for i,frame in enumerate(frames):
    rgb=frame.reformat(format='rgb24');raw=bytes(rgb.planes[0]);stride=rgb.planes[0].line_size;packed=b''.join(raw[y*stride:y*stride+rgb.width*3] for y in range(rgb.height));hashes.append(hashlib.sha256(packed).hexdigest())
    if i in [0,30,59]:Image.frombytes('RGB',(rgb.width,rgb.height),packed).save(O/f'frame-{i:03d}.png')
   R['uniqueDecodedFrames']=len(set(hashes));assert len(set(hashes))>=50;(O/'frame-hashes.json').write_text(json.dumps(hashes));container.close()
   R['download']={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};assert not R['errors'],R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   save()
   try:await asyncio.wait_for(browser.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

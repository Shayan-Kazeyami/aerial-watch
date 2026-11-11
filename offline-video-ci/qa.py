import asyncio,json,pathlib,subprocess,hashlib,time,traceback
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
   probe=subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=120);assert probe.returncode==0,probe.stderr;R['ffprobe']=json.loads(probe.stdout)
   v=next(s for s in R['ffprobe']['streams'] if s['codec_type']=='video');assert int(v['nb_read_frames'])==60;assert abs(float(R['ffprobe']['format']['duration'])-2)<.01
   decode=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','framemd5','-'],capture_output=True,text=True,timeout=120);assert decode.returncode==0,decode.stderr
   (O/'frames.md5').write_text(decode.stdout);hashes=[line.split(',')[-1].strip() for line in decode.stdout.splitlines() if not line.startswith('#')];R['uniqueDecodedFrames']=len(set(hashes));assert len(set(hashes))>=50
   extract=subprocess.run(['ffmpeg','-y','-v','error','-i',str(path),'-vf','select=eq(n\\,0)+eq(n\\,30)+eq(n\\,59)','-vsync','0',str(O/'frame-%02d.png')],capture_output=True,text=True,timeout=120);assert extract.returncode==0,extract.stderr
   R['download']={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};assert not R['errors'],R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:
   save()
   try:await asyncio.wait_for(browser.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

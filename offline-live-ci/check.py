import asyncio,json,pathlib,hashlib,traceback
from playwright.async_api import async_playwright
RID='4567e2c67548a8c32114cc76deeb8ae19491d0c4a7731c6d0dcfb33c974f3511'
REV='37778368c0b48542f8a4ff8d7bd1837bcbd7dd6badc34bef5bf8a23230c3eedd'
O=pathlib.Path('live-video-output');O.mkdir(exist_ok=True);R={'releaseId':RID,'revision':REV,'errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':640,'height':480});page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa',wait_until='domcontentloaded')
   await page.wait_for_function('document.getElementById("watch-viewer").src.includes("'+RID+'")');await page.frame_locator('#watch-viewer').locator('body[data-ready="true"]').wait_for(timeout=240000);frame=page.frame(url=lambda u:RID in u);assert frame
   await frame.locator('body[data-ready="true"]').wait_for(timeout=240000)
   proof=await frame.evaluate('''async()=>{const r=await(await fetch('./quality-study/viewer-revision.json')).json();const files=await Promise.all(['assembly-video-frame.js','assembly-offline-video.js','assembly-video-export.js','assembly-review.js','assembly-framing.js'].map(async p=>{const b=await(await fetch(p)).arrayBuffer();return {path:p,sha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('')};}));return {r,files};}''');assert proof['r']['digest']==REV
   by={x['path']:x['sha256'] for x in proof['r']['files']}
   for f in proof['files']:assert by[f['path']]==f['sha256']
   R['contentVerified']=proof['files'];R['source']=frame.url
   await frame.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"')
   await frame.locator('.task-dock [data-mode=capture]').click();assert await frame.locator('[data-proxy=record-scene]').text_content()=='Render 8s video';await frame.locator('[data-proxy=record-scene]').click();await frame.locator('.aerial-video-dialog[open]').wait_for();await frame.locator('.aerial-video-dialog button').click();await frame.wait_for_function('!assemblyInspect().videoExport.active && !document.getElementById("record-scene").disabled')
   R['cancelStatus']=await frame.locator('#viewer-status').text_content();assert 'cancelled' in R['cancelStatus'];assert await frame.evaluate('document.activeElement===document.querySelector(".task-dock [data-mode=capture]")')
   await page.screenshot(path=str(O/'live-video-view.png'));R['passed']=True;assert not R['errors'],R['errors']
  except Exception as e:R['passed']=False;R['failure']=repr(e);R['traceback']=traceback.format_exc();raise
  finally:(O/'report.json').write_text(json.dumps(R,indent=2));print('LIVE_REPORT',json.dumps(R),flush=True);await b.close()
asyncio.run(main())

import asyncio,json,pathlib,subprocess,os,hashlib
from playwright.async_api import async_playwright
from PIL import Image,ImageStat
P=pathlib.Path(__file__).parent;O=P/'watch-output';O.mkdir(exist_ok=True);RID='af604e9469ba87b091ebeed8c74865c6aa7afa3acd052e23538f427f19ffa81c';DIGEST='d93a0fa871d17c6f39a1cd93f12a843f1fe05b9631f970af286451e83f5c2b00';R={'errors':[],'exports':[],'release':RID,'scope':'exact sealed watch, software Chromium, native exports; no phone/GPU claim'}
async def main():
 server=subprocess.Popen(['python','-m','http.server','8766','--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright()as pw:
   b=await pw.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':640,'height':600},device_scale_factor=1,reduced_motion='reduce');page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
   await page.goto(f'http://127.0.0.1:8766/preview-b/releases/{RID}/atelier-preview.html?quality=efficient&assets=meshopt&normalStream=1',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=360000)
   c=json.loads((P/'config.json').read_text());c['options']['quality']='efficient';await page.locator('#import-config').set_input_files({'name':'paused.json','mimeType':'application/json','buffer':json.dumps(c).encode()});await page.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'");await page.locator('.atelier-first-use').wait_for(state='hidden',timeout=15000)
   await page.wait_for_function("()=>{document.querySelector('#refresh-diagnostics').click();return JSON.parse(document.querySelector('#diagnostics-report').textContent).progressiveNormal==='full'}",timeout=240000)
   async def diag():return await page.evaluate("()=>{document.querySelector('#refresh-diagnostics').click();return JSON.parse(document.querySelector('#diagnostics-report').textContent)}")
   async def saved(name,selector):
    await page.wait_for_function('(s)=>!document.querySelector(s).disabled',arg=selector)
    async with page.expect_download(timeout=240000)as d:
     await page.locator(selector).evaluate('(e)=>e.click()')
     await page.wait_for_function("()=>/download requested|Could not save/.test(document.querySelector('#viewer-status').textContent)",timeout=180000)
     status=await page.locator('#viewer-status').inner_text();R['lastCaptureStatus']=status;assert 'Could not save' not in status,status
    await(await d.value).save_as(O/name)
   async def video_start():
    await page.locator('#record-scene').evaluate('(e)=>e.click()');await page.locator('.aerial-video-choice').wait_for(state='visible');await page.locator('.aerial-video-choice [value=compact]').check();await page.locator('.aerial-video-choice button').click()
   R['preCapture']=await diag();(O/'REPORT.json').write_text(json.dumps(R,indent=2));print('full-detail ready, capturing',flush=True);await saved('before.png','#capture-scene');before=await diag();assert before['sourceAtCapture']['digest']==DIGEST;R['before']=before
   await video_start();await page.wait_for_function("document.querySelector('.aerial-video-status progress').value>0");await page.locator('.aerial-video-cancel').click();await page.wait_for_function("!document.querySelector('.aerial-video-dialog').open&&!document.querySelector('#record-scene').disabled");R['cancelRestored']=True;print('cancellation restored',flush=True)
   for i in range(2):
    async with page.expect_download(timeout=900000)as d:await video_start()
    f=O/f'watch-{i}.webm';await(await d.value).save_as(f);await page.wait_for_function("!document.querySelector('.aerial-video-dialog').open&&!document.querySelector('#record-scene').disabled");after=await diag();assert after['clock']['running']==before['clock']['running'];assert after['clock']['mechanism']==before['clock']['mechanism'];assert after['camera']==before['camera'];R['exports'].append({'file':f.name,'bytes':f.stat().st_size,'restored':True});print('video completed',i,flush=True)
   await saved('after.png','#capture-scene');await saved('view.json','#export-config');after=json.loads((O/'view.json').read_text());assert after['sourceAtCapture']['digest']==DIGEST
   a=Image.open(O/'before.png');a.load();z=Image.open(O/'after.png');z.load();assert a.tobytes()==z.tobytes();assert max(ImageStat.Stat(a.convert('RGB')).stddev)>2;R['pngPixelsUnchanged']=True;assert not R['errors'];R['passed']=True
   (O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
 finally:
  (O/'REPORT.json').write_text(json.dumps(R,indent=2));server.terminate()
asyncio.run(main())

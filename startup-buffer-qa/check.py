import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
OUT=pathlib.Path('startup-buffer-output');OUT.mkdir(exist_ok=True)
URL=os.environ['WATCH_URL'];BASE=URL.replace(URL.split('/releases/')[1].split('/')[0],'ff188ba605b3868d174bec75b643470c86fb164c706c5ff0b2d4ee89c2472947');R={'candidate':URL,'baseline':BASE,'errors':[],'states':{},'measurement':'Chromium SwiftShader mobile430x932 DPR3 Smooth. Buffer byte accounting, not process RSS or physical-phone time.'}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  try:
   for name,url in [('before',BASE),('after',URL)]:
    page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=3,is_mobile=True,has_touch=True);page.set_default_timeout(180000)
    async def instrument(route):
     resp=await route.fetch();await route.fulfill(response=resp,body=await resp.text()+'\n'+pathlib.Path('startup-buffer-qa/append.js').read_text())
    await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
    await page.goto(url,wait_until='domcontentloaded',timeout=120000);await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000)
    await page.evaluate('caseQA.init()');await page.evaluate('startupReset()');R[name]=await page.evaluate('startupSnapshot()')
    for state in ['assembled','front-close','exploded']:
     if state=='exploded':
      await page.evaluate('caseQA.restore()');await page.locator('.task-dock [data-mode=explode]').tap(force=True);await page.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating',timeout=180000)
     await page.wait_for_function('caseQA.settled()',timeout=180000);await page.evaluate('(p)=>caseQA.pose(p)','front-close' if state=='front-close' else None);data=await page.evaluate('caseQA.set(true)');(OUT/(state+'-'+name+'.json')).write_text(json.dumps(data));await page.screenshot(path=str(OUT/(state+'-'+name+'.png')),clip=await page.locator('#assembly-canvas').bounding_box(),animations='disabled',timeout=180000)
    await page.close()
   for state in ['assembled','front-close','exploded']:
    a=Image.open(OUT/(state+'-before.png')).convert('RGB');z=Image.open(OUT/(state+'-after.png')).convert('RGB');diff=ImageChops.difference(a,z);mean=sum(ImageStat.Stat(diff).mean)/3;changed=sum(max(v)>2 for v in diff.getdata());R['states'][state]={'meanDifference255':mean,'pixelsOver2':changed,'pixels':a.width*a.height};diff.save(OUT/(state+'-diff.png'));assert mean<.15,(state,mean)
   buffers=[l['buffering'] for l in R['after']['loads'] if l.get('buffering')];assert any(x['avoidedFinalCopy'] for x in buffers),buffers
   R['bufferAccounting']={'knownLengthAssets':sum(x['avoidedFinalCopy'] for x in buffers),'measuredAssets':len(buffers),'sumAvoidedStagingBytes':sum(max(0,2*x['bodyBytes']-x['peakOwnedBytes']) for x in buffers),'note':'Sum per-asset savings, not simultaneous total peak. Excludes parser/decoder/browser/GPU memory.'};assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

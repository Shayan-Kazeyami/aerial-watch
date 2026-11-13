import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
P=pathlib.Path('strap-retopology-qa');O=pathlib.Path('rim-remesh-evidence');O.mkdir(exist_ok=True)
RID='214740598c3327efb618f559ce587911d3893bd97a060a53172277877480a8b2';URL=f'http://127.0.0.1:8765/preview-b/releases/{RID}/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&tickBatch=1'
R={'baseline':RID,'states':{},'errors':[],'setup':'Matched actual Chromium SwiftShader full-watch renders; not physical phone performance'}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await b.new_page(viewport={'width':1000,'height':900},device_scale_factor=1);page.set_default_timeout(120000)
  async def instrument(route):
   resp=await route.fetch();await route.fulfill(response=resp,body=await resp.text()+'\n'+(P/'append.js').read_text())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded',timeout=120000);await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000)
   R['init']=await page.evaluate('rimQA.init()');print('INIT',R['init'],flush=True)
   for state in ['assembled','part','left','upper','lower']:
    await page.evaluate('rimQA.freeze()');await page.wait_for_function('rimQA.settled()',timeout=180000);await page.evaluate('(s)=>rimQA.pose(s)',state);data={}
    for name,candidate in [('before',False),('after',True)]:
     data[name]=await page.evaluate('(c)=>rimQA.set(c)',candidate);await page.locator('#assembly-canvas').screenshot(path=str(O/(state+'-'+name+'.png')),animations='disabled',timeout=120000)
     if state!='assembled':await page.evaluate('(c)=>rimQA.set(c,true)',candidate);await page.locator('#assembly-canvas').screenshot(path=str(O/(state+'-'+name+'-wire.png')),animations='disabled',timeout=120000)
    assert data['before']['camera']==data['after']['camera']
    aa=Image.open(O/(state+'-before.png')).convert('RGB');z=Image.open(O/(state+'-after.png')).convert('RGB');diff=ImageChops.difference(aa,z);stat=ImageStat.Stat(diff);mean=sum(stat.mean)/3;diff.save(O/(state+'-diff.png'));R['states'][state]={'meanDifference255':mean,**data};print(state,mean,flush=True)
   assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True);await b.close()
asyncio.run(main())

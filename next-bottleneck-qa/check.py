import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('bottleneck-evidence');O.mkdir(exist_ok=True)
RID='b38ddef36d153be511c40fc6d51795308a50440635edf1c97c39a725120cfdd3'
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(300000)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def intercept(route):
   response=await route.fetch();await route.fulfill(response=response,body=(await response.text())+'\n'+pathlib.Path('next-bottleneck-qa/probe.js').read_text())
  await page.route('**/assembly-review.js',intercept)
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/?probe=b38ddef3',wait_until='domcontentloaded')
   await page.wait_for_timeout(10000);f=next(f for f in page.frames if RID in f.url)
   await f.locator('body[data-ready=true]').wait_for();await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"')
   await f.evaluate('bottleneckQA.freeze()');await page.wait_for_timeout(3000)
   data=[]
   for profile in ['efficient','studio']:
    for explode,finish in [(0,True),(1,True),(0,False)]:
     for batch in [True,False]:
      cfg=dict(profile=profile,explode=explode,finish=finish,batch=batch)
      result=await f.evaluate('(cfg)=>bottleneckQA.sample(cfg)',cfg);data.append(result);print(json.dumps({**cfg,'render':result['render'],'batchState':result['batch']}),flush=True)
      (O/'results.json').write_text(json.dumps(data,indent=2))
   (O/'errors.json').write_text(json.dumps(errors));assert not errors
  finally:
   try:await asyncio.wait_for(b.close(),15)
   except:pass
asyncio.run(run())

import asyncio,json,pathlib,base64,os
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
OUT=pathlib.Path('tick-output');OUT.mkdir(exist_ok=True)
RID='30cb294bff1ad0f4d3fa10f5937c4610877e382d4cca2aab5cae777ddbc1e5e7'
URL='http://127.0.0.1:8765/preview-b/releases/'+RID+'/atelier-preview.html?tickBatch=1&quality=efficient'
R={'release':RID,'setup':'Chromium SwiftShader mobile430x932 DPR3 Smooth WebGL2','states':{},'errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=3,is_mobile=True,has_touch=True);page.set_default_timeout(180000)
  async def instrument(route):
   response=await route.fetch();await route.fulfill(response=response,body=await response.text()+'\n'+pathlib.Path('tick-batch-qa/append.js').read_text())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded',timeout=120000);await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000)
   await page.evaluate('tickQA.freeze()')
   async def compare(state):
    data={}
    for name,on in [('before',False),('after',True)]:
     d=await page.evaluate('(on)=>tickQA.set(on)',on);data[name]=d
     await page.locator('#assembly-canvas').screenshot(path=str(OUT/(state+'-'+name+'.png')),animations='disabled',timeout=120000);(OUT/(state+'-'+name+'.json')).write_text(json.dumps(d,indent=2))
    im1=Image.open(OUT/(state+'-before.png')).convert('RGB');im2=Image.open(OUT/(state+'-after.png')).convert('RGB');diff=ImageChops.difference(im1,im2);stats=ImageStat.Stat(diff);changed=sum(1 for pixel in diff.getdata() if max(pixel)>2)
    a=data['before']['inventory'];z=data['after']['inventory'];data['summary']={'beforeCalls':a['rendererInfo']['render']['calls'],'afterCalls':z['rendererInfo']['render']['calls'],'beforeSubmitted':a['rendererInfo']['render']['triangles'],'afterSubmitted':z['rendererInfo']['render']['triangles'],'beforeVisible':a['totals']['visibleObjects'],'afterVisible':z['totals']['visibleObjects'],'pixelMeanAbsoluteDifference':sum(stats.mean)/3,'pixelsDifferenceOver2':changed,'pixels':im1.width*im1.height}
    assert a['totals']['visibleRangeTrianglesBeforeCulling']==z['totals']['visibleRangeTrianglesBeforeCulling'];assert a['totals']['visibleObjects']-z['totals']['visibleObjects']==58;assert data['summary']['afterCalls']<data['summary']['beforeCalls'];assert sum(stats.mean)/3<.1,(state,stats.mean)
    ticks=await page.evaluate('tickQA.names()');assert len(ticks)==60 and all(t['raycast'] and not t['visible']for t in ticks);R['states'][state]=data['summary'];print(state,data['summary'],flush=True)
   await compare('assembled')
   await page.locator('.task-dock [data-mode=explode]').tap(force=True);await page.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating',timeout=180000);await compare('exploded')
   await page.locator('#atelier-explosion').evaluate("e=>{e.value='37';e.dispatchEvent(new Event('input',{bubbles:true}))}");assert abs(await page.evaluate('assemblyInspect().explosion.amount')-.37)<.001;await compare('partial')
   await page.locator('#home').tap(force=True);await page.wait_for_function('assemblyInspect().explosion.amount===0',timeout=180000);await compare('reset')
   assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

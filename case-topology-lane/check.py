import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
OUT=pathlib.Path('case-topology-output');OUT.mkdir(exist_ok=True)
URL=os.environ['WATCH_URL'];R={'url':URL,'setup':'Chromium SwiftShader; mobile430x932 DPR3 Smooth; fixed cameras, paused animation; not phone FPS','states':{},'errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=3,is_mobile=True,has_touch=True);page.set_default_timeout(120000)
  async def instrument(route):
   resp=await route.fetch();await route.fulfill(response=resp,body=await resp.text()+'\n'+pathlib.Path('case-topology-lane/append.js').read_text())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded',timeout=120000);await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000)
   R['init']=await page.evaluate('caseQA.init()');assert R['init']['after']<R['init']['before']
   async def compare(state,pose=None):
    await page.evaluate('caseQA.freeze()');await page.wait_for_function('caseQA.settled()',timeout=180000);await page.evaluate('(pose)=>caseQA.pose(pose)',pose);data={}
    for name,candidate in [('before',False),('after',True)]:
     data[name]=await page.evaluate('(c)=>caseQA.set(c)',candidate);(OUT/(state+'-'+name+'.json')).write_text(json.dumps(data[name],indent=2));await page.locator('#assembly-canvas').screenshot(path=str(OUT/(state+'-'+name+'.png')),animations='disabled',timeout=120000)
    assert data['before']['camera']==data['after']['camera'],state+' camera drift'
    a=Image.open(OUT/(state+'-before.png')).convert('RGB');z=Image.open(OUT/(state+'-after.png')).convert('RGB');diff=ImageChops.difference(a,z);stat=ImageStat.Stat(diff);mean=sum(stat.mean)/3;changed=sum(max(p)>2 for p in diff.getdata());diff.save(OUT/(state+'-diff.png'))
    r={'meanAbsoluteDifference255':mean,'pixelsDifferenceOver2':changed,'pixels':a.width*a.height,'beforeCalls':data['before']['inventory']['rendererInfo']['render']['calls'],'afterCalls':data['after']['inventory']['rendererInfo']['render']['calls'],'beforeTriangles':data['before']['inventory']['rendererInfo']['render']['triangles'],'afterTriangles':data['after']['inventory']['rendererInfo']['render']['triangles']};R['states'][state]=r;print(state,r,flush=True);
   await compare('assembled');await compare('front-close','front-close');await compare('side','side');await compare('side-close','side-close');await compare('side-wire','side-wire');await compare('crown','crown');await compare('crown-close','crown-close');await compare('crown-wire','crown-wire');assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

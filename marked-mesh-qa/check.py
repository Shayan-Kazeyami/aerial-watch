import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
OUT=pathlib.Path('marked-output');OUT.mkdir(exist_ok=True)
URL=os.environ['WATCH_URL'];R={'url':URL,'setup':'Chromium SwiftShader; mobile430x932 DPR3 Smooth; fixed cameras, paused animation; not phone FPS','states':{},'errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=3,is_mobile=True,has_touch=True);page.set_default_timeout(120000)
  async def instrument(route):
   resp=await route.fetch();await route.fulfill(response=resp,body=await resp.text()+'\n'+pathlib.Path('marked-mesh-qa/append.js').read_text())
  await page.route('**/assembly-review.js*',instrument);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto(URL,wait_until='domcontentloaded',timeout=120000);await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000)
   R['init']=await page.evaluate('markedQA.init()');assert all(r['after']<r['before'] for r in R['init'])
   async def compare(state,pose=None):
    await page.evaluate('markedQA.freeze()');await page.wait_for_function('markedQA.settled()',timeout=180000);await page.evaluate('(pose)=>markedQA.pose(pose)',pose);data={}
    for name,candidate in [('before',False),('after',True)]:
     data[name]=await page.evaluate('(c)=>markedQA.set(c)',candidate);(OUT/(state+'-'+name+'.json')).write_text(json.dumps(data[name],indent=2));await page.locator('#assembly-canvas').screenshot(path=str(OUT/(state+'-'+name+'.png')),animations='disabled',timeout=120000)
    assert data['before']['camera']==data['after']['camera'],state+' camera drift'
    a=Image.open(OUT/(state+'-before.png')).convert('RGB');z=Image.open(OUT/(state+'-after.png')).convert('RGB');diff=ImageChops.difference(a,z);stat=ImageStat.Stat(diff);mean=sum(stat.mean)/3;changed=sum(max(p)>2 for p in diff.getdata());diff.save(OUT/(state+'-diff.png'))
    r={'meanAbsoluteDifference255':mean,'pixelsDifferenceOver2':changed,'pixels':a.width*a.height,'beforeCalls':data['before']['calls'],'afterCalls':data['after']['calls'],'beforeTriangles':data['before']['triangles'],'afterTriangles':data['after']['triangles']};R['states'][state]=r;print(state,r,flush=True);assert mean<.35,(state,mean)
   await compare('assembled');await compare('front-close','close');await compare('lug-upper','lug-upper');await compare('lug-upper-side','lug-upper-side');await compare('lug-lower','lug-lower');await compare('lug-lower-side','lug-lower-side');await compare('lug-upper-left','lug-upper-side-left');await compare('lug-lower-left','lug-lower-side-left');await page.evaluate('markedQA.restore()')
   await page.locator('.task-dock [data-mode=explode]').tap(force=True);await page.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating',timeout=180000);await compare('exploded')
   await page.evaluate('markedQA.restore()');await page.wait_for_function('markedQA.settled()',timeout=180000)
   await page.locator('.task-dock [data-mode=explode]').tap(force=True);await page.locator('#atelier-explosion').evaluate("e=>{e.value='37';e.dispatchEvent(new Event('input',{bubbles:true}))}");assert abs(await page.evaluate('assemblyInspect().explosion.amount')-.37)<.001
   await page.locator('#home').tap(force=True);await page.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating',timeout=180000);await compare('reset')
   start=await page.evaluate('markedQA.motion().mechanism');await page.locator('#play-motion').evaluate('e=>e.click()');await page.wait_for_function('(s)=>markedQA.motion().mechanism>s+.1',arg=start,timeout=180000);await page.evaluate('markedQA.freeze()');R['movementAndExplosion']=True;assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);raise
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

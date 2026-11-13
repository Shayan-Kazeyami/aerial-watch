import asyncio,json,pathlib
from playwright.async_api import async_playwright
P=pathlib.Path('webgpu-controls-qa');O=pathlib.Path('header-evidence');O.mkdir(exist_ok=True);rid=(P/'release-id.txt').read_text().strip();R={'release':rid,'viewports':{},'errors':[]}
async def run():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':740,'height':360},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(300000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  try:
   await page.goto('http://127.0.0.1:8765/?paused=1');f=page.frames[-1];await f.locator('body[data-ready=true]').wait_for();await f.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"')
   for w,h in [(568,320),(740,360),(932,430),(430,932)]:
    await page.set_viewport_size({'width':w,'height':h});await page.wait_for_timeout(300)
    cases=[]
    for text in ['WebGL2','WebGL2 · fallback','WebGPU lost']:
     await f.locator('#atelier-backend-indicator').evaluate('(el,t)=>el.textContent=t',text)
     result=await f.evaluate('''()=>{const ids=['#home','.masthead .quality','.atelier-more'],a=ids.map(s=>{let e=document.querySelector(s),r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {selector:s,x:r.x,y:r.y,w:r.width,h:r.height,hit:e.contains(hit)||e===hit}});return a}''')
     assert all(a['hit']and a['w']>=44 and a['h']>=44 for a in result),(w,text,result)
     for i,a in enumerate(result):
      for c in result[i+1:]:assert min(a['x']+a['w'],c['x']+c['w'])<=max(a['x'],c['x'])or min(a['y']+a['h'],c['y']+c['h'])<=max(a['y'],c['y']),(w,text,result)
     cases.append({'indicator':text,'controls':result})
    await f.locator('#atelier-backend-indicator').evaluate("el=>el.textContent='WebGL2'")
    await f.locator('.task-dock [data-mode=explode]').tap();await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating');await f.locator('#home').tap();await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating');assert not await f.locator('#context').is_visible();R['viewports'][str(w)]={'hitTargets':cases,'explodeReset':True};await page.screenshot(path=str(O/f'{w}.png'))
   R['passed']=not R['errors'];assert R['passed']
  except Exception as e:R['failure']=str(e);raise
  finally:(O/'report.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(run())

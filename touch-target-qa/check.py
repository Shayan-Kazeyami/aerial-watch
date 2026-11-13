import asyncio,json,pathlib
from playwright.async_api import async_playwright
OUT=pathlib.Path('touch-target-output');OUT.mkdir(exist_ok=True)
URL='https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/7455e9604154e6db2a17531090f9dd8fae4fb003b8dac67b393eeac538ab94e7/atelier-preview.html'
R={'url':URL,'tests':[],'errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  page=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,reduced_motion='reduce')
  page.on('pageerror',lambda e:R['errors'].append(str(e)))
  await page.goto(URL,wait_until='domcontentloaded',timeout=120000)
  await page.locator('body[data-ready=true]').wait_for(timeout=300000)
  await page.evaluate("""window.trace=[];for(const name of ['pointerdown','pointerup','touchstart','touchend','click','atelier:explode','atelier:explode-state'])document.addEventListener(name,e=>trace.push({type:name,target:e.target.tagName,detail:name.startsWith('atelier:')?e.detail:null}),true)""")
  cdp=await page.context.new_cdp_session(page)
  async def tap(x,y):
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
   await page.wait_for_timeout(80)
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
   await page.wait_for_timeout(1500)
  await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':150,'y':300}]})
  await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':190,'y':315}]})
  await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  await page.wait_for_timeout(500)
  for label,pos in [('icon-center',.5),('button-edge',.08)]:
   await page.evaluate('trace=[]')
   box=await page.locator('.task-dock [data-mode=explode]').bounding_box()
   x=box['x']+box['width']*pos;y=box['y']+box['height']/2
   target=await page.evaluate('([x,y])=>document.elementFromPoint(x,y).outerHTML',[x,y])
   await tap(x,y)
   R['tests'].append({'label':label,'hit':target,'trace':await page.evaluate('trace'),'panel':await page.locator('#context').get_attribute('data-tool')})
   await page.locator('#home').click();await page.wait_for_timeout(500)
  await page.screenshot(path=str(OUT/'production.png'),timeout=120000)
  print(json.dumps(R),flush=True);(OUT/'report.json').write_text(json.dumps(R,indent=2))
  await b.close()
asyncio.run(main())

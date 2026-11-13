import asyncio,json,pathlib
from playwright.async_api import async_playwright
R=[];OUT=pathlib.Path('touch-target-output');OUT.mkdir(exist_ok=True)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch()
  for dwell in [0,100]:
   page=await b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
   await page.set_content("""<meta name="viewport" content="width=device-width"><style>canvas{width:390px;height:600px;touch-action:none}button{width:100px;height:62px;touch-action:manipulation}svg{width:20px;height:20px;fill:none;stroke:black}</style><canvas></canvas><button><svg viewBox="0 0 24 24"><path d="m4 9 8 4 8-4M4 15l8 4 8-4M12 2v5m-3-3 3-3 3 3M12 20v3"/></svg></button><script>window.trace=[];for(const type of ['pointerdown','pointerup','touchstart','touchend','click'])document.addEventListener(type,e=>trace.push({type,target:e.target.tagName,time:performance.now()}),true);document.querySelector('canvas').addEventListener('pointerdown',e=>e.target.setPointerCapture(e.pointerId));</script>""")
   cdp=await page.context.new_cdp_session(page)
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':150,'y':300}]})
   if dwell:await page.wait_for_timeout(dwell)
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':190,'y':315}]})
   if dwell:await page.wait_for_timeout(dwell)
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await page.wait_for_timeout(500)
   box=await page.locator('button').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2;await page.evaluate('trace=[]')
   await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});await page.wait_for_timeout(80);await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await page.wait_for_timeout(1500)
   R.append({'dwell':dwell,'trace':await page.evaluate('trace')});print(json.dumps(R[-1]),flush=True);await page.close()
  (OUT/'fixture.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())

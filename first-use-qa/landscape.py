import asyncio,json,pathlib
from playwright.async_api import async_playwright
OUT=pathlib.Path('landscape-output');OUT.mkdir(exist_ok=True)
R={'checks':[],'errors':[]}
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for width,height in [(844,390),(568,320)]:
    page=await browser.new_page(viewport={'width':width,'height':height},device_scale_factor=2,is_mobile=True,has_touch=True,reduced_motion='reduce')
    page.set_default_timeout(30000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
    await page.goto(pathlib.Path('first-use-qa/url.txt').read_text().strip())
    await page.locator('body[data-ready=true]').wait_for(timeout=300000)
    await page.wait_for_timeout(1200)
    await page.screenshot(path=str(OUT/f'{width}-initial.png'))
    canvas=page.locator('#assembly-canvas');rect=await canvas.bounding_box()
    assert rect['height']>=height-120,rect
    targets=['.quality','#home','.atelier-more']+[f'.task-dock [data-mode={m}]' for m in ['explore','inside','explode','time','capture']]
    for s in targets:
     b=await page.locator(s).bounding_box();assert b and b['width']>=44 and b['height']>=44,(s,b)
     assert b['x']>=0 and b['y']>=0 and b['x']+b['width']<=width+1 and b['y']+b['height']<=height+1,(s,b)
     assert await page.locator(s).evaluate('(e)=>{let b=e.getBoundingClientRect();let hit=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);return e===hit||e.contains(hit)}'),s
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    await page.locator('.task-dock [data-mode=explode]').tap()
    await page.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    assert await canvas.bounding_box()==rect
    await page.screenshot(path=str(OUT/f'{width}-explode.png'))
    await page.locator('#close').tap();assert await canvas.bounding_box()==rect
    await page.locator('.atelier-more').tap();await page.locator('#context').wait_for(state='visible');assert await canvas.bounding_box()==rect
    await page.screenshot(path=str(OUT/f'{width}-tools.png'))
    await page.locator('#close').tap()
    await page.locator('#home').tap();await page.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating')
    await page.locator('.quality').tap();await page.locator('#context').wait_for(state='visible');assert await canvas.bounding_box()==rect
    await page.screenshot(path=str(OUT/f'{width}-quality.png'))
    await page.locator('#close').tap()
    R['checks'].append({'viewport':[width,height],'canvas':rect,'allTargetsAtLeast44':True,'unobstructedTargets':True,'stablePanels':True,'explodeReset':True})
    await page.close()
   assert not R['errors'];R['passed']=True
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   await browser.close()
asyncio.run(main())

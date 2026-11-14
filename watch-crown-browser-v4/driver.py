import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
Q=Path(__file__).resolve().parent;arm=sys.argv[1];assert arm in ['baseline','candidate'];RID=json.loads((Q/'QA_CLOSURE.json').read_text())[arm]['rid']
async def main():
 r={'arm':arm,'passed':False,'errors':[],'steps':[],'scope':'real keyboard/control direction only; no physical device/release approval'};browser=None
 try:
  async with async_playwright() as p:
   try:
    browser=await asyncio.wait_for(p.chromium.launch(headless=True,chromium_sandbox=True),45);page=await browser.new_page(viewport={'width':1280,'height':900});page.on('pageerror',lambda e:r['errors'].append(str(e)));page.set_default_timeout(30000)
    await page.goto('http://127.0.0.1:8873/?quality=balanced&normalStream=1&paused=1&backend=webgl2',wait_until='domcontentloaded',timeout=120000)
    await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=600000);f=next(x for x in page.frames if '/'+RID+'/' in x.url)
    await f.wait_for_function('__crownParityQA?.ready()',timeout=600000)
    initial=await f.evaluate('__crownParityQA.snapshot()');r['initial']=initial
    async def settled():
     await f.wait_for_function('__crownParityQA.ready()',timeout=30000);s=await f.evaluate('__crownParityQA.snapshot()');assert s['timeOrigin']==initial['timeOrigin'] and s['canvas']==initial['canvas'] and not s['disposed'];return s
    async def turn(label,action):
     before=await settled();await action();after=await settled();delta=after['crown']['degrees']-before['crown']['degrees'];r['steps'].append({'label':label,'before':before,'after':after,'delta':delta});return delta
    for pulled in [False,True]:
     await f.locator('.task-dock [data-mode="time"]').click();await settled();s=await f.evaluate('__crownParityQA.snapshot()')
     if s['crown']['pulled']!=pulled:await f.locator('#context[data-tool="time"] #atelier-tools [data-proxy="crown-pull"]').click();await settled()
     assert (await settled())['crown']['pulled']==pulled
     assert abs(await turn('panel-left',lambda:f.locator('#context[data-tool="time"] #atelier-tools [data-proxy="crown-left"]').click())+15)<1e-7
     assert abs(await turn('panel-right',lambda:f.locator('#context[data-tool="time"] #atelier-tools [data-proxy="crown-right"]').click())-15)<1e-7
     await f.locator('#close').click();await settled();button=f.locator('.crown-hotspot');await button.wait_for(state='visible');await button.focus()
     assert await button.evaluate('(e)=>e===document.activeElement')
     for key,value in [('ArrowLeft',-15 if arm=='candidate' else 15),('ArrowRight',15 if arm=='candidate' else -15),('ArrowUp',15),('ArrowDown',-15)]:
      assert abs(await turn(key,lambda k=key:page.keyboard.press(k))-value)<1e-7
     await page.keyboard.press('Escape');assert await f.locator('#assembly-canvas').evaluate('(e)=>e===document.activeElement')
    await asyncio.wait_for(page.screenshot(path=str(Q/(arm+'.png'))),120);assert not r['errors'];r['passed']=True
   finally:
    if browser:await asyncio.wait_for(browser.close(),30)
 finally:(Q/('RESULT-'+arm+'.json')).write_text(json.dumps(r,indent=2)+'\n')
asyncio.run(asyncio.wait_for(main(),1100))

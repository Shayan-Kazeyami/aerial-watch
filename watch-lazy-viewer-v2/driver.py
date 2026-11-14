import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
Q=Path(__file__).resolve().parent;arm,mode=sys.argv[1:];assert arm in ['baseline','candidate'] and mode in ['normal','fault'];RID='c9d2d1a59b4efacb6d4b44824baefd047dab96351b0086fa8bfe1032168c31bc'
async def main():
 report={'arm':arm,'mode':mode,'passed':False,'errors':[],'artificialFault':mode=='fault'};browser=None
 try:
  async with async_playwright() as p:
   try:
    browser=await asyncio.wait_for(p.chromium.launch(headless=True,chromium_sandbox=True),45)
    page=await browser.new_page(viewport={'width':1280,'height':900});page.on('pageerror',lambda e:report['errors'].append(str(e)));page.set_default_timeout(30000)
    await page.goto('http://127.0.0.1:8765/?quality=balanced&normalStream=1&paused=1&backend=webgl2',wait_until='domcontentloaded',timeout=120000)
    await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=600000)
    f=next(x for x in page.frames if '/'+RID+'/' in x.url)
    await f.wait_for_function('window.__lazyViewerQA?.ready()',timeout=600000)
    report['before']=await f.evaluate('__lazyViewerQA.snapshot()');assert not report['before']['solid'] and not report['before']['open']
    for kind in ['solid','open']:
     result=await asyncio.wait_for(f.evaluate('([k,fault])=>__lazyViewerQA.exercise(k,fault)',[kind,mode=='fault']),30);report[kind]=result
     if mode=='normal':assert result['error'] is None and result['retained'] and result['attached'] and result['reused']
     elif arm=='candidate':assert 'disposed' in result['error'] and not result['retained'] and not result['attached']
     else:assert result['error'] is None and result['retained'] and result['attached']
    await asyncio.wait_for(page.screenshot(path=str(Q/f'{arm}-{mode}.png')),120)
    assert not report['errors'];report['passed']=True
   finally:
    if browser:await asyncio.wait_for(browser.close(),30)
 finally:(Q/f'RESULT-{arm}-{mode}.json').write_text(json.dumps(report,indent=2)+'\n')
asyncio.run(asyncio.wait_for(main(),1000))

import asyncio,json,time
from pathlib import Path
from playwright.async_api import async_playwright
Q=Path(__file__).resolve().parent;E=Q/'evidence';E.mkdir(exist_ok=False)
async def main():
 report={'passed':False,'scope':'isolated loading browser API QA; not viewer or heap approval'};browser=None
 try:
  async with async_playwright() as p:
   try:
    browser=await asyncio.wait_for(p.chromium.launch(headless=True,chromium_sandbox=True),45)
    report['browser']=browser.version
    page=await browser.new_page(viewport={'width':1100,'height':800});page.set_default_timeout(30000)
    await page.goto('http://127.0.0.1:8765/',timeout=30000)
    await page.wait_for_function('window.done===true',timeout=180000)
    report['fixture']=await page.evaluate('window.result')
    assert report['fixture']['passed'],report['fixture']
    await asyncio.wait_for(page.screenshot(path=str(E/'results.png'),full_page=True),30)
   except BaseException as e:
    report['failure']=repr(e);raise
   finally:
    if browser:
     try:await asyncio.wait_for(browser.close(),30);report['normalClose']=True
     except BaseException as e:report['cleanupFailure']=repr(e);raise
  report['passed']=True
 finally:(E/'REPORT.json').write_text(json.dumps(report,indent=2))
asyncio.run(asyncio.wait_for(main(),300))

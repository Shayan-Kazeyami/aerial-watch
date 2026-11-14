"""Explicit browser entry point. Not run during preparation or tests."""
import asyncio,json,time
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
Q=Path(__file__).resolve().parent
async def main():
 out=Q/'evidence';out.mkdir(exist_ok=True);report={'acceptance':False,'events':[]};browser=None
 async def action(name,call,seconds=30):
  start=time.monotonic()
  try:return await asyncio.wait_for(call,seconds)
  finally:report['events'].append({'name':name,'seconds':time.monotonic()-start})
 try:
  async with async_playwright() as p:
   browser=await action('launch',p.chromium.launch(headless=True));report['browser']=browser.version
   try:
    async with asyncio.timeout(300):
     page=await browser.new_page(viewport={'width':768,'height':768},device_scale_factor=1);page.set_default_timeout(30000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     await action('navigate',page.goto('http://127.0.0.1:8765/index.html',timeout=30000));await action('ready',page.wait_for_function('window.ready===true',timeout=30000));report['meta']=await page.evaluate('window.meta')
     for i in range(5):
      for tilt in [0,.5]:
       await action(f'pair-{i}-{tilt}',page.evaluate('([i,t])=>window.runPair(i,t)',[i,tilt]))
       for which in ['source','candidate','return']:
        await action('show',page.evaluate('([i,w])=>window.show(i,w)',[i,which]));await action('capture',page.locator('canvas').screenshot(path=str(out/f'{i}-{tilt}-{which}.png'),timeout=60000),60)
        with Image.open(out/f'{i}-{tilt}-{which}.png') as im:
         assert im.size==(768,768),'PNG dimensions'
         assert any(lo!=hi for lo,hi in im.convert('RGB').getextrema()),'blank PNG'
        report.setdefault('validPNGs',[]).append(f'{i}-{tilt}-{which}.png')
     report['results']=await page.evaluate('window.results');report['lifecycle']=await action('lifecycle',page.evaluate('window.finish()'));report['pageErrors']=errors
     assert len(report['results'])==10 and len(report['validPNGs'])==30 and not errors;report['fixturePassed']=True
   except BaseException as e:
    report['primaryFailure']=repr(e);raise
   finally:
    try:await action('normal-close',browser.close());report['normalClosePassed']=True
    except BaseException as e:
     report['cleanupFailure']=repr(e)
     if 'primaryFailure' not in report:raise
  report['acceptance']=bool(report.get('fixturePassed')and report.get('normalClosePassed'));report['limits']='Isolated recorded-renderer only; manual image review and actual viewer/UI gates remain held.'
 except BaseException as e:report['failure']=repr(e);raise
 finally:(out/'REPORT.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':asyncio.run(main())

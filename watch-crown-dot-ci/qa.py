import asyncio,json,pathlib
from playwright.async_api import async_playwright
O=pathlib.Path('watch-crown-dot-output');O.mkdir(exist_ok=True)
async def main():
 report=[]
 async with async_playwright() as p:
  for url in ['https://shayan-kazeyami.github.io/aerial-watch/','https://shayan-kazeyami.github.io/aerial-watch/?quality=efficient']:
   b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':1000,'height':800});r={'url':url,'errors':[],'failed':[]};report.append(r);page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('requestfailed',lambda q:r['failed'].append({'url':q.url,'failure':q.failure}));page.on('response',lambda s:r['failed'].append({'status':s.status,'url':s.url}) if s.status>=400 else None)
   try:
    await page.goto(url,wait_until='domcontentloaded');await page.wait_for_function("document.querySelector('iframe')?.contentWindow?.assemblyInspect?.().presentation.interactive",timeout=180000);r['ready']=True;r['state']=await page.evaluate("document.querySelector('iframe').contentWindow.assemblyInspect()");print('READY',url,flush=True)
   except Exception as e:r['ready']=False;r['error']=str(e);r['body']=await page.locator('body').inner_text();r['frames']=[{'url':f.url,'text':await f.locator('body').inner_text()} for f in page.frames];print('FAIL',json.dumps(r),flush=True)
   finally:(O/'live-report.json').write_text(json.dumps(report,indent=2));await b.close()
  assert all(x['ready'] for x in report),report
asyncio.run(main())

import asyncio,json,pathlib,base64
from playwright.async_api import async_playwright
O=pathlib.Path('qa-video-lifetime/evidence');O.mkdir(parents=True,exist_ok=True)
R={'scope':'Actual WebGL2 pixels / WebCodecs / native dialog; controlled small GL scene, not full watch or heap measurement','arms':{}}
async def arm(browser,name):
 page=await browser.new_page(viewport={'width':640,'height':480});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 await page.goto('http://127.0.0.1:8873/qa-video-lifetime/'+name+'/index.html');await page.wait_for_function('window.qaReady===true')
 first=await page.evaluate('success()')
 (O/(name+'-first.webm')).write_bytes(base64.b64decode(first.pop('videoBase64')))
 assert first['frameCount']==12 and first['state']['time']==7 and not first['active'] and not first['dialogOpen']
 await page.evaluate('startCancel()')
 await page.wait_for_function("qaCaptureState().renders>12")
 await page.locator('.aerial-video-dialog[open] button').click()
 await page.wait_for_function('window.cancelResult!==null')
 cancelled=await page.evaluate('cancelResult')
 assert cancelled['name']=='AbortError' and cancelled['state']['time']==7 and not cancelled['active'] and not cancelled['dialogOpen']
 retry=await page.evaluate('success()')
 (O/(name+'-retry.webm')).write_bytes(base64.b64decode(retry.pop('videoBase64')))
 assert retry['frameCount']==12 and retry['state']['time']==7 and not retry['active'] and not retry['dialogOpen']
 if name=='candidate':assert first['releases']==1 and cancelled['releases']==2 and retry['releases']==3 and len(retry['allocations'])==6
 else:assert first['releases']==retry['releases']==0 and len(retry['allocations'])==2
 # Actual canvas image retained after restoration; same final GL scene for both.
 await page.screenshot(path=str(O/(name+'-restored.png')))
 disposed=await page.evaluate('disposeExport()');assert disposed['dialogCount']==0
 assert not errors,errors
 R['arms'][name]={'first':first,'cancelled':cancelled,'retry':retry,'disposed':disposed,'errors':errors}
 await page.close()
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for name in ['original','candidate']:await arm(browser,name)
   R['pass']=True
  except Exception as e:R['pass']=False;R['failure']=repr(e);raise
  finally:
   (O/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True);await browser.close()
asyncio.run(main())

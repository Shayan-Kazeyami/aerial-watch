import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True)
OLD='bf858771be73667b8a9ca3a459090e671786783fbfb5faf471522c580b8f0710';NEW='27faa19b1525130f1ce8f1aacdbe87783d7a8809e39ace77d19316c0d77e3765'
PUBLIC=os.environ.get('PUBLIC')=='1';R={'public':PUBLIC,'rows':[],'errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  try:
   for rid in ([NEW] if PUBLIC else [OLD,NEW]):
    for w,h in [(390,844),(932,430)]:
     page=await b.new_page(viewport={'width':w,'height':h},reduced_motion='reduce');page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)))
     root='https://shayan-kazeyami.github.io/aerial-watch/' if PUBLIC else 'http://127.0.0.1:8765/'
     await page.goto(root+('' if PUBLIC else 'preview-b/releases/'+rid+'/atelier-preview.html')+'?quality=efficient',wait_until='domcontentloaded')
     if PUBLIC:
      await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=360000);f=next(x for x in page.frames if rid in x.url)
     else:f=page;await page.locator('body[data-ready=true]').wait_for(timeout=360000)
     await f.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
     await f.locator('.atelier-more').click();button=f.locator('[data-inspection=hideStrap]');await button.wait_for(state='visible');title=await button.get_attribute('title');assert ('Reset view changes only the camera.' in title)==(rid==NEW)
     stage=await f.locator('#stage').bounding_box();await button.click();await f.wait_for_function('assemblyInspect().inspectionDisplay.hideStrap===true')
     await f.locator('#home').click();assert await f.evaluate('assemblyInspect().inspectionDisplay.hideStrap===true');assert await f.locator('#stage').bounding_box()==stage
     assert 'Restore' in await button.inner_text();await button.click();await f.wait_for_function('assemblyInspect().inspectionDisplay.hideStrap===false')
     await button.click();await f.wait_for_function('assemblyInspect().inspectionDisplay.hideStrap===true');await f.locator('#atelier-inspection-reset').click();await f.wait_for_function('assemblyInspect().inspectionDisplay.hideStrap===false')
     R['rows'].append({'release':rid,'viewport':[w,h],'title':title,'resetPreservesHiddenStrap':True,'bothRestoreActionsWork':True,'passed':True});await page.screenshot(path=str(O/f'{rid[:8]}-{w}.png'));await page.close()
   assert not R['errors'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())

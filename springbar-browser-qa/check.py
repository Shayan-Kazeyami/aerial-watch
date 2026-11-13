import asyncio,json,pathlib,traceback
from playwright.async_api import async_playwright
P=pathlib.Path('springbar-browser-qa');O=pathlib.Path('springbar-browser-evidence');O.mkdir(exist_ok=True);RID='63600a544b71214dcbfceee96a3eac0dbfa48bca7d42d59425acd43bae131bfd';report={'release':RID,'setup':'Isolated route overlay, Chromium SwiftShader; memory attribution via actual gl.bufferData, not hardware FPS','variants':{}}
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for variant in ['source','candidate']:
   context=await browser.new_context(viewport={'width':1100,'height':800});page=await context.new_page();page.set_default_timeout(300000);errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda q:requests.append(q.url));r={'errors':errors,'candidateRouteHits':0};report['variants'][variant]=r
   async def instrument(route):
    res=await route.fetch();await route.fulfill(response=res,body=(await res.text()).replace('function initializeBaseline(result,metadata){','function initializeBaseline(result,metadata){window.springQAAssetDelivery=result.metrics?.assetDelivery;')+'\n'+(P/'probe.js').read_text())
   await page.route('**/assembly-review.js*',instrument)
   async def overlay(route):
    r['candidateRouteHits']+=1;await route.fulfill(path=str(P/'springbars-shared-attributes.meshopt.glb.gz'),content_type='application/gzip')
   if variant=='candidate':await page.route('**/optimized-assets/rebuild__assembly.meshopt.glb.gz*',overlay)
   try:
    await page.goto('http://127.0.0.1:8765/preview-b/releases/'+RID+'/atelier-preview.html?quality=efficient&normalStream=1',wait_until='domcontentloaded',timeout=120000);await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"');await page.evaluate('springQAFrames(8)');r['initial']=await page.evaluate('springQASnapshot()');assert not r['initial']['failed'];assert r['initial']['assetDelivery']['used']=='meshopt',r['initial']['assetDelivery'];assert not r['initial']['assetDelivery']['fallbackReason'];start=len(requests);r['poses']=[]
    for amount,pulled in [(0,False),(.25,False),(.5,True),(.75,True),(1,False),(0,False)]:
     await page.evaluate('([a,p])=>springQAPose(a,p)',[amount,pulled]);await page.evaluate('springQAFrames(8)');s=await page.evaluate('springQASnapshot()');assert s['canvas']==r['initial']['canvas'];assert s['timeOrigin']==r['initial']['timeOrigin'];r['poses'].append(s)
    r['assetRefetches']=[u for u in requests[start:] if any(u.split('?')[0].endswith(x) for x in ['.glb','.bin','.gltf','.glb.gz'])];assert not r['assetRefetches'];await page.screenshot(path=str(O/(variant+'-assembled.png')));await page.evaluate('springQAPose(1,false)');await page.evaluate('springQAFrames(8)');await page.screenshot(path=str(O/(variant+'-exploded.png')));await page.evaluate('springQAFocus()');await page.evaluate('springQAFrames(8)');await page.screenshot(path=str(O/(variant+'-springbar.png')));assert not errors;r['passed']=True
   except Exception as e:r.update(passed=False,error=repr(e),traceback=traceback.format_exc());raise
   finally:(O/'report.json').write_text(json.dumps(report,indent=2));await context.close()
  a=report['variants']['source'];b=report['variants']['candidate'];assert a['initial']['rows']==b['initial']['rows'];assert [x['rows'] for x in a['poses']]==[x['rows'] for x in b['poses']];assert b['initial']['sharedPositionAttribute'] and b['initial']['sharedNormalAttribute'] and b['initial']['distinctUVAttribute'];assert b['initial']['uploadedPositionNormalBuffers']==2;assert a['initial']['uploadedPositionNormalBuffers']==4;assert a['initial']['uploadedPositionNormalBytes']-b['initial']['uploadedPositionNormalBytes']==54384;report['verifiedActualBufferSavingsBytes']=54384;report['passed']=True;(O/'report.json').write_text(json.dumps(report,indent=2));await browser.close()
asyncio.run(asyncio.wait_for(main(),1500))

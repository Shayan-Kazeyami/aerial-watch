import asyncio,json,pathlib,traceback,os,gzip
from playwright.async_api import async_playwright
P=pathlib.Path('strap-browser-qa');O=pathlib.Path('strap-browser-evidence');O.mkdir(exist_ok=True);RID='63600a544b71214dcbfceee96a3eac0dbfa48bca7d42d59425acd43bae131bfd';report={'release':RID,'setup':'Private route overlay. Chromium SwiftShader, not phone FPS.','variants':{}}
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for variant in ['source','candidate']:
   context=await browser.new_context(viewport={'width':1100,'height':800},device_scale_factor=1);page=await context.new_page();page.set_default_timeout(180000);errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda q:requests.append(q.url));r={'errors':errors};report['variants'][variant]=r
   async def instrument(route):
    res=await route.fetch();await route.fulfill(response=res,body=(await res.text())+'\n'+(P/'probe.js').read_text())
   await page.route('**/assembly-review.js*',instrument)
   if variant=='candidate':
    await page.route('**/leather-assets/r14/leather.gltf*',lambda route:route.fulfill(path=str(P/'candidate/leather.gltf'),content_type='model/gltf+json'))
    await page.route('**/leather-assets/r14/geometry.bin*',lambda route:route.fulfill(path=str(P/'candidate/geometry.bin'),content_type='application/octet-stream'))
    await page.route('**/assembly-leather-authoring-identity.js*',lambda route:route.fulfill(path=str(P/'identity.js'),content_type='text/javascript'))
   try:
    await page.goto('http://127.0.0.1:8765/preview-b/releases/'+RID+'/atelier-preview.html?quality=efficient&normalStream=1',wait_until='domcontentloaded',timeout=120000)
    await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.getElementById("stage").dataset.cameraReady==="true"',timeout=300000)
    await page.wait_for_function('leatherQASnapshot().proof?.status==="verified"',timeout=300000)
    r['initial']=await page.evaluate('leatherQAFrames(4)');assert not r['initial']['failed'];expected='06a72fb672bb249fe86d19af6b4934c94869dd56b46283b8d1858ae1b91b4815' if variant=='candidate' else '97377092fcfc6f5a7e934e083f71a1d5e99c9d2007a1b5c3ba38a2b6a6dc61e3';assert r['initial']['proof']['actualSha256']==expected,r['initial']['proof']
    await page.wait_for_function('''()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent).progressiveNormal==='full'}''',timeout=300000)
    r['diagnostics']=await page.evaluate('''()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent)}''');start=len(requests);r['poses']=[]
    for amount,pulled in [(0,False),(.25,False),(.5,True),(.75,True),(1,False),(0,False)]:
     await page.evaluate('([a,p])=>leatherQAPose(a,p)',[amount,pulled]);s=await page.evaluate('leatherQAFrames(4)');assert s['canvas']==r['initial']['canvas'];assert s['timeOrigin']==r['initial']['timeOrigin'];assert [x['matrix'] for x in s['rows']]==[x['matrix'] for x in r['initial']['rows']],'Strap attachment matrices changed';r['poses'].append(s)
    r['assetRefetches']=[u for u in requests[start:] if any(u.split('?')[0].endswith(x) for x in ['.glb','.bin','.gltf'])];assert not r['assetRefetches'];await page.screenshot(path=str(O/(variant+'-assembled.png')))
    contacts=await page.evaluate('leatherQAContactData()');(O/(variant+'-hardware.json.gz')).write_bytes(gzip.compress(json.dumps(contacts).encode()));assert len(contacts['hardware'])>0
    await page.evaluate('leatherQAPose(1,false)');await page.evaluate('leatherQAFrames(4)');await page.screenshot(path=str(O/(variant+'-exploded.png')));assert not errors;assert all(any(t['ready'] for t in x['maps']) for x in r['initial']['rows'] if x['material'].startswith('leather /'))
    r['passed']=True
   except Exception as e:r.update(passed=False,error=repr(e),traceback=traceback.format_exc());raise
   finally:(O/'report.json').write_text(json.dumps(report,indent=2));await context.close()
  await browser.close()
asyncio.run(asyncio.wait_for(main(),1500))

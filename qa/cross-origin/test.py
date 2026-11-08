import asyncio,json,pathlib,traceback
from playwright.async_api import async_playwright
from PIL import Image
out=pathlib.Path('cross-origin-output');out.mkdir(exist_ok=True);r={'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','backend':'Chromium SwiftShader','phases':{},'errors':[]};save=lambda:(out/'report.json').write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640},accept_downloads=True);page=await c.new_page();r['browser']=b.version;page.on('pageerror',lambda e:r['errors'].append(str(e)));scripts=[];page.on('request',lambda x:scripts.append(x.url) if 'assembly-review.js' in x.url else None)
  async def instrument(route):
   response=await route.fetch();s=await response.text();s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});';await route.fulfill(response=response,body=s)
  await page.route('**/assembly-review.js*',instrument)
  async def phase(name,fn,timeout=180):
   r['phases'][name]={'status':'running'};save()
   try:r['phases'][name]={'status':'passed','detail':await asyncio.wait_for(fn(),timeout)}
   except Exception as e:r['phases'][name]={'status':'failed','exception':repr(e),'traceback':traceback.format_exc()}
   save()
  async def ready():
   await page.wait_for_function("document.querySelector('iframe') !== null",timeout=30000);host=await (await page.query_selector('iframe')).content_frame();await host.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await host.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);assert any(r['release'] in x for x in scripts);proof=await q.evaluate('__proof()');assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830;return q,proof
  try:
   await page.goto('http://127.0.0.1:8766/qa/cross-origin/wrapper.html',wait_until='domcontentloaded');r['hostOrigin']=await page.evaluate('location.origin');q,proof=await asyncio.wait_for(ready(),360);r['viewerOrigin']=await q.evaluate('location.origin');assert r['hostOrigin']!=r['viewerOrigin'];r['proof']=proof;r['phases']['initial_ready']={'status':'passed','detail':{'hostOrigin':r['hostOrigin'],'viewerOrigin':r['viewerOrigin'],'quality':(await q.evaluate('assemblyInspect()'))['renderQuality']}};assert (await q.evaluate('assemblyInspect()'))['renderQuality']=='efficient';save()
   async def keyboard():
    await page.locator('iframe').focus();outer=await page.evaluate("document.activeElement.tagName");assert outer=='IFRAME';await q.locator('[data-mode=time]').focus();await page.keyboard.press('Enter');await q.wait_for_timeout(500);opened=await q.evaluate('document.activeElement.id');assert opened=='close';await page.keyboard.press('Escape');await q.wait_for_timeout(500);returned=await q.evaluate('document.activeElement.dataset.mode');assert returned=='time';return {'hostFocus':outer,'openFocus':opened,'returnMode':returned}
   await phase('keyboard_focus',keyboard,120)
   async def exports():
    await q.locator('[data-mode=capture]').first.click(timeout=40000);await q.wait_for_function("!document.querySelector('[data-proxy=capture-scene]').disabled",timeout=90000)
    async with page.expect_download(timeout=150000) as d:await q.locator('[data-proxy=capture-scene]').click(timeout=40000)
    dl=await d.value;png=out/'capture.png';await dl.save_as(png)
    with Image.open(png) as im:im.verify()
    with Image.open(png) as im:im.load();dim=list(im.size);mode=im.mode;alpha=im.getchannel('A').getextrema() if 'A'in im.getbands() else None
    r['png']={'bytes':png.stat().st_size,'dimensions':dim,'mode':mode,'alpha':alpha};save();await q.locator('[data-mode=capture]').first.click(timeout=40000);await q.wait_for_function("!document.querySelector('[data-proxy=export-config]').disabled",timeout=90000)
    async with page.expect_download(timeout=120000) as d:await q.locator('[data-proxy=export-config]').click(timeout=40000)
    dl=await d.value;j=out/'view.json';await dl.save_as(j);data=json.loads(j.read_text());await q.locator('#import-config').set_input_files(str(j));await q.wait_for_function("document.getElementById('import-config').value==='' && document.getElementById('viewer-status').textContent.includes('restored')",timeout=90000);return {'png':r['png'],'jsonBytes':j.stat().st_size,'importStatus':await q.locator('#viewer-status').text_content(),'jsonView':data['view']}
   await phase('actual_png_and_json',exports,420)
   async def recreate():
    before=len(scripts);await page.evaluate("""()=>{let f=document.querySelector('iframe'),parent=f.parentNode,next=f.nextSibling,copy=f.cloneNode(false);f.remove();parent.insertBefore(copy,next)}""");newq,newproof=await asyncio.wait_for(ready(),360);i=await newq.evaluate('assemblyInspect()');assert len(scripts)>before and i['renderQuality']=='efficient';return {'newScriptRequests':len(scripts)-before,'quality':i['renderQuality'],'interactive':i['presentation']['interactive'],'geometrySHA':newproof['leather']['geometryVerification']['actualSha256'],'hybridActive':newproof['hybrid']['active']}
   await phase('remove_recreate_ready',recreate,420)
  except Exception as e:r['setup_error']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();
  try:await asyncio.wait_for(c.close(),15)
  except:pass
  try:await asyncio.wait_for(b.close(),15)
  except:pass
asyncio.run(main())

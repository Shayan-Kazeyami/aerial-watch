import asyncio,json,os,pathlib,traceback
from playwright.async_api import async_playwright
from PIL import Image
case=os.environ['CASE'];out=pathlib.Path('cross-origin-export-output');out.mkdir(exist_ok=True);r={'case':case,'release':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','status':'starting','errors':[],'console':[]};save=lambda:(out/(case+'.json')).write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640},accept_downloads=True);page=await c.new_page();r['browser']=b.version;page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('console',lambda m:r['console'].append({'type':m.type,'text':m.text}) if m.type in ('warning','error') else None);scripts=[];page.on('request',lambda x:scripts.append(x.url) if 'assembly-review.js' in x.url else None)
  async def instrument(route):
   response=await route.fetch();s=await response.text();s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});';await route.fulfill(response=response,body=s)
  await page.route('**/assembly-review.js*',instrument);q=None
  try:
   await page.goto('http://127.0.0.1:8766/qa/cross-origin/wrapper.html',wait_until='domcontentloaded');host=await (await page.query_selector('iframe')).content_frame();await host.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await host.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);assert any(r['release'] in x for x in scripts);proof=await q.evaluate('__proof()');assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830;r['proof']=proof;r['origins']={'host':await page.evaluate('location.origin'),'viewer':await q.evaluate('location.origin')};assert r['origins']['host']!=r['origins']['viewer'];r['status']='ready';save()
   await q.locator('[data-mode=capture]').first.click(timeout=60000);sel='capture-scene' if case=='png' else 'export-config';await q.wait_for_function('(sel)=>!document.querySelector(`[data-proxy="${sel}"]`).disabled',arg=sel,timeout=90000);r['status']='capture-ready';save()
   async with page.expect_download(timeout=180000) as d:await q.locator('[data-proxy="'+sel+'"]').click(timeout=60000)
   dl=await d.value;file=out/(case+'.png' if case=='png' else case+'.json');await dl.save_as(file)
   if case=='png':
    with Image.open(file) as im:im.verify()
    with Image.open(file) as im:im.load();r['file']={'bytes':file.stat().st_size,'format':im.format,'dimensions':list(im.size),'mode':im.mode,'alpha':im.getchannel('A').getextrema() if 'A'in im.getbands() else None}
   else:
    data=json.loads(file.read_text());await q.locator('#import-config').set_input_files(str(file));await q.wait_for_function("document.getElementById('import-config').value==='' && document.getElementById('viewer-status').textContent.includes('restored')",timeout=90000);r['file']={'bytes':file.stat().st_size,'view':data['view'],'importStatus':await q.locator('#viewer-status').text_content()}
   r['status']='passed'
  except Exception as e:
   r['status']='failed';r['exception']=repr(e);r['traceback']=traceback.format_exc()
   if q:
    try:r['diagnostics']=await asyncio.wait_for(q.evaluate('''()=>({status:document.getElementById('status').textContent,viewerStatus:document.getElementById('viewer-status').textContent,inspect:assemblyInspect(),button:document.querySelector('[data-proxy=capture-scene]')?.outerHTML})'''),20)
    except Exception as ex:r['diagnosticError']=repr(ex)
  finally:save()
  try:await asyncio.wait_for(c.close(),15)
  except:pass
  try:await asyncio.wait_for(b.close(),15)
  except:pass
asyncio.run(main())

import asyncio,json,pathlib,traceback
from playwright.async_api import async_playwright
out=pathlib.Path('live-export-output');out.mkdir(exist_ok=True);r={'target':'https://shayan-kazeyami.github.io/aerial-watch/','expectedRelease':'a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473','results':[],'errors':[]};save=lambda:(out/'report.json').write_text(json.dumps(r,indent=2));save()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640},accept_downloads=True)
  await c.add_init_script('''(()=>{const create=URL.createObjectURL.bind(URL),revoke=URL.revokeObjectURL.bind(URL);window.__exports={created:[],revoked:[]};URL.createObjectURL=(o)=>{let u=create(o);if(o instanceof Blob&&(/png|json/i).test(o.type))window.__exports.created.push({url:u,type:o.type,size:o.size});return u};URL.revokeObjectURL=(u)=>{window.__exports.revoked.push(u);return revoke(u)}})();''');q=await c.new_page();q.on('pageerror',lambda e:r['errors'].append(str(e)));requests=[];q.on('request',lambda req:requests.append(req.url) if 'assembly-review.js' in req.url else None)
  async def proof(route):
   response=await route.fetch();s=await response.text();s+='\nwindow.__proof=()=>({leather:leatherCandidateDiagnostics(leatherGeometryProof),hybrid:hybridCaseSnapshot()});';await route.fulfill(response=response,body=s)
  await q.route('**/assembly-review.js*',proof)
  try:
   await q.goto(r['target']+'?quality=efficient&leather=craft14',wait_until='domcontentloaded',timeout=60000);page=q;await page.wait_for_function("document.querySelector('#watch-viewer')?.contentWindow?.location.href.includes('atelier-preview.html')",timeout=60000);q=await (await page.query_selector('#watch-viewer')).content_frame();await q.wait_for_function('window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden',timeout=300000);r['requests']=requests;assert any(r['expectedRelease'] in x for x in requests),requests
   proof=await q.evaluate('__proof()');r['proof']=proof;assert proof['leather']['geometryVerification']['actualSha256']=='8da7de21efcceacadcf21e0fa9cd866b678ecc8d49d0fdbd947d485004e2e5c7' and proof['leather']['geometryVerification']['actualBytes']==8579970 and proof['hybrid']['active'] and proof['hybrid']['triangles']==501830;save()
   for n in range(2):
    await q.locator('[data-mode=capture]').first.click(timeout=20000);await q.wait_for_timeout(4000)
    async with page.expect_download(timeout=120000) as d:await q.locator('[data-proxy=capture-scene]').click(timeout=20000)
    dl=await d.value;path=out/f'capture-{n}.png';await dl.save_as(path);assert path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n';r['results'].append({'type':'png','bytes':path.stat().st_size});save()
    await q.locator('[data-mode=capture]').first.click(timeout=20000);await q.wait_for_timeout(4000)
    async with page.expect_download(timeout=120000) as d:await q.locator('[data-proxy=export-config]').click(timeout=20000)
    dl=await d.value;path=out/f'view-{n}.json';await dl.save_as(path);data=json.loads(path.read_text());assert data;await q.locator('#import-config').set_input_files(str(path));await q.wait_for_timeout(4000);r['results'].append({'type':'json','bytes':path.stat().st_size,'status':await q.locator('#viewer-status').text_content()});save()
   await q.wait_for_timeout(65000);r['cleanup']=await q.evaluate('''()=>({tracked:window.__exports,remainingAnchors:[...document.querySelectorAll('a[href^="blob:"]')].map(a=>a.href)})''');e=r['cleanup']['tracked'];assert len(e['created'])>=4 and all(x['url'] in e['revoked'] for x in e['created']);assert not [a for a in r['cleanup']['remainingAnchors'] if a in [x['url'] for x in e['created']]];assert not r['errors'];r['status']='passed'
  except Exception as e:r['status']='failed';r['exception']=repr(e);r['traceback']=traceback.format_exc()
  finally:save();await c.close();await b.close()
asyncio.run(main())

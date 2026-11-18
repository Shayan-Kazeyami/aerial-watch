import asyncio,json,pathlib,hashlib,base64
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True);RID='efb9c41b5a3531812fb64b960841c35d98cfe75799bd7bb774e852527cc029b3';ROOT='https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/'+RID+'/'
R={'release':RID,'scope':'Unmodified current public release Studio closeup survey, cloud Chromium software WebGL. No proposed change or defect claim yet.','errors':[],'poses':[],'servedModules':{}}
async def main():
 async with async_playwright()as pw:
  browser=await pw.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=await browser.new_context(viewport={'width':1280,'height':800},device_scale_factor=1,reduced_motion='reduce');page=await ctx.new_page();page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)));responses=[]
  page.on('response',lambda r:responses.append(r)if any(r.url.split('?')[0].endswith('/'+n)for n in ['assembly-review.js','atelier-preview.js','assembly-leather-details.js','assembly-ktx-leather-r14.js'])else None)
  try:
   manifest=await(await ctx.request.get(ROOT+'deployment-manifest.json')).json();local={x['path']:x for x in manifest['localFiles']};assert manifest['releaseId']==RID
   await page.goto(ROOT+'atelier-preview.html?quality=studio&assets=meshopt&normalStream=1',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=360000)
   await page.wait_for_function("()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent).progressiveNormal==='full'}",timeout=240000)
   for response in responses:
    name=response.url.split('?')[0].split('/')[-1];digest=hashlib.sha256(await response.body()).hexdigest();assert digest==local[name]['sha256'],name;R['servedModules'][name]={'url':response.url,'sha256':digest}
   assert len(R['servedModules'])>=3
   config=json.loads((P/'config.json').read_text());poses=[('upper-front',[0,22,42],[0,22,0]),('upper-oblique',[22,24,40],[4,22,0]),('crown-close',[43,-12,22],[22,0,3])]
   for name,pos,target in poses:
    config['camera']['position']=pos;config['camera']['target']=target
    await page.locator('#import-config').set_input_files({'name':name+'.json','mimeType':'application/json','buffer':json.dumps(config).encode()});await page.wait_for_function("assemblyInspect().mechanismElapsed===0&&!assemblyInspect().animation&&!assemblyInspect().interiorAnimation");await page.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'");await page.locator('.atelier-first-use').wait_for(state='hidden',timeout=15000);await page.wait_for_timeout(1500)
    state=await page.evaluate('assemblyInspect()');assert state['renderQuality']=='studio';(O/(name+'-A1.png')).write_bytes(base64.b64decode((await page.locator('#assembly-canvas').evaluate("c=>c.toDataURL('image/png')")).split(',')[1]));await page.wait_for_timeout(800);(O/(name+'-A2.png')).write_bytes(base64.b64decode((await page.locator('#assembly-canvas').evaluate("c=>c.toDataURL('image/png')")).split(',')[1]))
    diag=await page.evaluate("()=>{document.getElementById('refresh-diagnostics').click();return JSON.parse(document.getElementById('diagnostics-report').textContent)}")
    row={'name':name,'config':json.loads(json.dumps(config)),'state':state,'resourceTotals':await page.evaluate('assemblyResourceInspect().totals'),'canvas':await page.locator('#assembly-canvas').evaluate('(c)=>({css:[c.clientWidth,c.clientHeight],buffer:[c.width,c.height],dpr:devicePixelRatio})')};R['poses'].append(row);(O/(name+'-diagnostics.json')).write_text(json.dumps(diag,indent=2));print(name,'captured',flush=True)
   assert not R['errors'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await browser.close()
asyncio.run(main())

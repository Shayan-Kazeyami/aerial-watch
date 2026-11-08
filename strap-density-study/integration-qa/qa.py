import asyncio,json,pathlib,base64,os
from playwright.async_api import async_playwright
OUT=pathlib.Path('strap-integration-output');OUT.mkdir(exist_ok=True)
RECEIPT=json.loads(pathlib.Path(os.environ.get('STRAP_RELEASE_RECEIPT','strap-output/sealed-release.json')).read_text())
ROOT=os.environ.get('STRAP_RELEASE_ROOT',RECEIPT['releasePath']);DOC=json.loads((pathlib.Path(RECEIPT['releasePath'])/'leather-assets/r14/leather.gltf').read_text());EXPECTED={'bodyTriangles':sum(DOC['accessors'][p['indices']]['count']//3 for mi in [0,2]for p in DOC['meshes'][mi]['primitives']),'sha256':RECEIPT['geometryIdentity']['sha256'],'bytes':RECEIPT['geometryIdentity']['bytes']}
END=os.environ.get('STRAP_QA_END','upper-right');READY='window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden'

async def run():
 report={'errors':[],'console':[],'states':[],'release':ROOT,'end':END}
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);q=await b.new_page(viewport={'width':800,'height':640},device_scale_factor=1)
  q.on('pageerror',lambda e:report['errors'].append(str(e)));q.on('console',lambda m:report['console'].append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
  async def instrument(route):
   r=await route.fetch();s=await r.text();s=s.replace('composer.render();','strapQaApply();composer.render();');s+='\n'+pathlib.Path('strap-density-study/integration-qa/qa-hook.js').read_text();await route.fulfill(response=r,body=s)
  await q.route('**/assembly-review.js*',instrument)
  try:
   await q.goto('http://127.0.0.1:8765/'+ROOT+'/atelier-preview.html?quality=efficient&leather=craft14',wait_until='domcontentloaded');await q.wait_for_function('('+READY+') || (window.assemblyInspect && assemblyInspect().failed)',timeout=300000)
   report['setup']=await q.evaluate('__strapQaSetup()');i=report['setup']['inspect'];assert not i['failed'];assert i['hybridCase']['active'] and i['hybridCase']['triangles']==501830;assert sum(x['triangles']for x in report['setup']['bodies'])==EXPECTED['bodyTriangles'],report['setup']['bodies'];assert report['setup']['leather']['ready'];proof=report['setup']['leather']['diagnostics']['geometryVerification'];assert proof['status']=='verified' and proof['actualSha256']==EXPECTED['sha256'] and proof['actualBytes']==EXPECTED['bytes'],proof;report['browser']=b.version
   await q.evaluate('__strapWhole()');whole=await q.evaluate('__strapQaCapture()');assert whole['effectiveQuality']=='efficient';(OUT/f'{END}-whole.png').write_bytes(base64.b64decode(whole.pop('png').split(',')[1]));report['whole']=whole
   prefix=END.replace('-','/')
   await q.evaluate('(p)=>__strapQaLit(...p.split("/"))',prefix)
   await q.evaluate('(v)=>{__strapQaView(v,"native");__strapQaQuality("balanced")}',prefix+'/context')
   for kind in ['context','close','body','neck']:
    if kind=='neck':await q.evaluate('(p)=>{__strapQaRake(...p.split("/"));}',prefix)
    state=await q.evaluate('(v)=>__strapQaView(v,"native")',prefix+'/'+kind);report['states'].append(state);cap=await q.evaluate('__strapQaCapture()');assert cap['effectiveQuality']=='balanced';(OUT/f'{END}-{kind}.png').write_bytes(base64.b64decode(cap.pop('png').split(',')[1]));(OUT/f'{END}-{kind}.json').write_text(json.dumps(cap,indent=2))
   report['controls']=await q.evaluate('__strapControls()');assert report['controls']['sameGeometry'] and report['controls']['sameMaterials'];assert report['controls']['hybrid']['active']
   report['final']=await q.evaluate('assemblyInspect()');assert report['final']['hybridCase']['active'];assert not report['errors'];report['passed']=True
  finally:
   (OUT/f'{END}-report.json').write_text(json.dumps(report,indent=2));await b.close()
asyncio.run(run())

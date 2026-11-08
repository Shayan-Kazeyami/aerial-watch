import asyncio,json,pathlib
from playwright.async_api import async_playwright
ROOT='preview-b/releases/949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8'
OUT=pathlib.Path('integration-output');OUT.mkdir(exist_ok=True)
READY='window.assemblyInspect && !assemblyInspect().loading && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden'
async def run():
 report={'errors':[],'console':[],'states':[]};page=None
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  async def open_mode(mode):
   nonlocal page
   q=await b.new_page(viewport={'width':1000,'height':800},device_scale_factor=1);page=q;q.on('console',lambda m: report['console'].append({'mode':mode,'type':m.type,'text':m.text}) if m.type in ['warning','error'] else None);q.on('pageerror',lambda e:report['errors'].append({'mode':mode,'error':str(e)}));await q.goto('http://127.0.0.1:8765/'+ROOT+'/atelier-preview.html?caseStudy='+mode+'&quality=low',wait_until='domcontentloaded');await q.wait_for_function('('+READY+') || (window.assemblyInspect && assemblyInspect().failed)',timeout=300000);snapshot=await q.evaluate('assemblyInspect()');assert not snapshot['failed'],snapshot;return q
  try:
   page=await open_mode('hybrid-study');report['initial']=await page.evaluate('assemblyInspect()');a=report['initial']['hybridCase'];assert a['active'] and a['ownsGeometry'] and a['triangles']==501830 and a['rawReferenceSHA256']=='15c26797577ca7643247f1e4fa05d9f789d75f58a9c6d84fb7ec0727dd685be2' and a['glbSHA256']=='a3b4c2a9081366a1e2c0109299ce1cbc2a384006bd925555a512aac39f5130d6' and a['transportSHA256']=='6d6e911eb12e81641a7e9d0a196aee78029f290b131af7904aa5dda37084cc3f' and a['delivery']=='meshopt-gzip';assert not report['initial']['parametricCase']['enabled']
   report['controls']=await page.evaluate('__hybridControls()');assert report['controls']['sameGeometry'] and report['controls']['hybrid']['active']
   report['whole']=await page.evaluate('__metalWhole()');await page.wait_for_timeout(1500);await page.screenshot(timeout=180000,path=str(OUT/'whole.png'))
   for sx in [-1,1]:
    for sy in [-1,1]:
     for sz in [-1,1]:
      r=await page.evaluate('(v)=>__metalQA(...v)',[sx,sy,sz,False,False]);report['states'].append(r);assert r['hybrid']['active'] and r['triangles']==501830;await page.wait_for_timeout(1500);await page.screenshot(timeout=180000,path=str(OUT/f'root-{sx}-{sy}-{sz}.png'))
     for plain in [False,True]:
      r=await page.evaluate('(v)=>__metalQA(...v)',[sx,sy,1,plain,True]);report['states'].append(r);await page.wait_for_timeout(1500);await page.screenshot(timeout=180000,path=str(OUT/f'bridge-{sx}-{sy}-{plain}.png'))
   report['dispose']=await page.evaluate('__hybridDispose()');d=report['dispose'];assert d['disposals']==1 and d['restoredTriangles']==37452 and d['materialPreserved'] and not d['active'] and d['sourcePositionSHA256']=='a34259a445b90d0d46bf2bc89d3947cde8a6cebd12146d29292ab5b64f9155f0';await page.close();page=None
   report['alternatives']={}
   for mode in ['source','fine-combined']:
    q=await open_mode(mode);snapshot=await q.evaluate('__integrationState()');report['alternatives'][mode]=snapshot;assert not snapshot['hybrid']['active'];assert snapshot['parametric']['enabled']==(mode=='fine-combined');assert snapshot['capActive']==(mode=='source');assert snapshot['triangles']==(37452 if mode=='source' else 761046);await q.close()
   assert not report['errors'],report['errors'];report['passed']=True
  except Exception as e:
   report['failure']=str(e)
   if page:
    try:report['failureSnapshot']=await page.evaluate('window.assemblyInspect?.()')
    except Exception:pass
   raise
  finally:
   (OUT/'report.json').write_text(json.dumps(report,indent=2));await b.close()
asyncio.run(run())

import asyncio,json,pathlib,hashlib,threading,http.server,socketserver,subprocess,os
from playwright.async_api import async_playwright
from PIL import Image
import numpy as np
import shutil
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'output';OUT.mkdir(exist_ok=True)
RID='9de584f677b276f7cc3621b904c36d0762a4e8202da81578341150828e6c3576';REL=ROOT/'preview-b/releases'/RID
PROBE=(ROOT/'next-bottleneck-qa/probe.js').read_text()+'\n'+(HERE/'probe.js').read_text()
EXPECTED=hashlib.sha256((REL/'assembly-review.js').read_bytes()).hexdigest();assert EXPECTED=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee'
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
 def log_message(self,*a):pass
server=socketserver.TCPServer(('127.0.0.1',8765),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
report={'ci_commit':os.getenv('GITHUB_SHA'),'releaseId':RID,'original_viewer_sha256':EXPECTED,'probe_sha256':hashlib.sha256(PROBE.encode()).hexdigest(),'instrumented_diagnostic_only':True,'deployed':False,'physical_gpu_verified':False,'errors':[],'calendar':[]};census=[]
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2))
def spring(s):
 gs={g['id']:g for g in s['geometries']};return {r['userData']['sourceIndex']:{'mesh':r,'geometry':gs[r['geometry']]} for r in s['rows'] if any(c['name']=='source'for c in r['collections']) and r['userData'].get('sourceIndex')in[148,159]}
def pixels(a,b):
 x=np.asarray(Image.open(a)).astype(float);y=np.asarray(Image.open(b)).astype(float);d=np.abs(x-y);return {'mean':float(d.mean()),'max':float(d.max()),'fraction_over_8':float((d.max(axis=2)>8).mean())}
async def main():
 async with async_playwright()as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('chromium-browser') or None,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport={'width':430,'height':932},device_scale_factor=1,is_mobile=True,has_touch=True);page.set_default_timeout(240000)
  page.on('pageerror',lambda e:report['errors'].append(str(e)));requests=[];page.on('request',lambda r:requests.append(r.url))
  async def intercept(route):
   response=await route.fetch();text=await response.text();assert hashlib.sha256(text.encode()).hexdigest()==EXPECTED
   await route.fulfill(response=response,body=text+'\n'+PROBE)
  await page.route('**/assembly-review.js*',intercept)
  try:
   await page.goto(f'http://127.0.0.1:8765/preview-b/releases/{RID}/atelier-preview.html?quality=efficient',wait_until='domcontentloaded')
   await page.locator('body[data-ready=true]').wait_for();await page.wait_for_function('typeof runtime421Snapshot==="function"');await page.evaluate('runtime421Freeze()');await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"');await page.wait_for_timeout(1000)
   await page.evaluate('bottleneckQA.sample({batch:true,profile:"efficient",explode:0})')
   for label in ['assembled','exploded','balance-layer']:
    if label=='exploded':
     await page.locator('.task-dock [data-mode=explode]').click(force=True);await page.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    if label=='balance-layer':
     await page.locator('#atelier-layer-focus').select_option('balance');await page.wait_for_function('assemblyInspect().layerFocus.selected==="balance"');await page.wait_for_timeout(1000)
    s=await page.evaluate('label=>runtime421Snapshot(label)',label);assert RID in s['url'] and s['threeRevision']=='187' and s['webgl2'];assert not s['clock']['running']['hands']and not s['clock']['running']['mechanism'];assert not s['inspection']['animation'] and not s['inspection']['interiorAnimation'];census.append(s)
    await page.locator('#assembly-canvas').screenshot(path=str(OUT/(label+'.png')),style='.crown-hotspot,.crown-halo,.atelier-first-use{visibility:hidden!important}')
   await page.locator('#atelier-layer-overview').click(force=True);await page.wait_for_function('!assemblyInspect().layerFocus.selected');await page.evaluate('runtime421Freeze()');await page.evaluate('bottleneckQA.sample({batch:true,profile:"efficient",explode:1})');await page.evaluate('runtime421WaitStableCamera()')
   assert census[0]['batch']['batches']>0,'No actual batching built'
   for idx,seconds in enumerate([0,33659.351376120474,0]):
    initial=await page.evaluate('s=>runtime421Calendar(s)',seconds);samples=[]
    for toggle,on in enumerate([True,False,True]):
     await page.evaluate('on=>runtime421ToggleBatch(on)',on)
     s=await page.evaluate('label=>runtime421Snapshot(label)',f'calendar-{idx}-{toggle}');samples.append(s)
     assert s['batch']['enabled'] is on,{'requested_enabled':on,'observed_batch':s['batch']}
     await page.locator('#assembly-canvas').screenshot(path=str(OUT/f'calendar-{idx}-{toggle}.png'),style='.crown-hotspot,.crown-halo,.atelier-first-use{visibility:hidden!important}')
    first=spring(samples[0]);assert set(first)=={148,159}
    for state in samples:
     assert not any(state['clock']['running'].values()) and state['clock']['hands']==0 and state['clock']['mechanism']==0
     assert not state['inspection']['animation'] and not state['inspection']['interiorAnimation']
     assert state['crown']==samples[0]['crown']
    comparisons=[]
    for toggle in [1,2]:
     other=spring(samples[toggle]);assert samples[0]['camera']==samples[toggle]['camera'] and samples[0]['projection']==samples[toggle]['projection']
     for source_id in [148,159]:
      assert first[source_id]['mesh']['worldMatrix']==other[source_id]['mesh']['worldMatrix']
      for attr in ['position','normal']:assert first[source_id]['geometry']['attributes'][attr]['sha256']==other[source_id]['geometry']['attributes'][attr]['sha256']
      assert first[source_id]['geometry']['index']==other[source_id]['geometry']['index']
     d=pixels(OUT/f'calendar-{idx}-0.png',OUT/f'calendar-{idx}-{toggle}.png');comparisons.append(d);assert d['mean']<.1 and d['fraction_over_8']<.001,d
    report['calendar'].append({'seconds':seconds,'direct_state':initial['state'],'snapshots':samples,'comparisons':comparisons})
   starts=spring(report['calendar'][0]['snapshots'][0]);peaks=spring(report['calendar'][1]['snapshots'][0]);returns=spring(report['calendar'][2]['snapshots'][0]);deformation=[]
   for sid in [148,159]:
    hashes=[x[sid]['geometry']['attributes']['position']['sha256']for x in [starts,peaks,returns]];assert hashes[0]!=hashes[1]and hashes[0]==hashes[2],(sid,hashes)
    deformation.append({'sourceIndex':sid,'full_position_sha256':hashes,'nonvacuous_deformation':True,'exact_return':True,'observed_suppression':[x[sid]['mesh']['batchSuppressedSource']for x in [starts,peaks,returns]]})
   report['deformation']=deformation;report['calendar_mutation_pixel_signal']=pixels(OUT/'calendar-0-0.png',OUT/'calendar-1-0.png');report['return_pixels']=pixels(OUT/'calendar-0-0.png',OUT/'calendar-2-0.png')
   assert report['return_pixels']['mean']<.1 and report['return_pixels']['fraction_over_8']<.001
   report['early_frames']=await page.evaluate('runtime421EarlyFrames()');report['requests']=requests;assert not report['errors'],report['errors'];report['passed']=True
  except Exception as error:
   report['passed']=False;report['failure']=repr(error);raise
  finally:
   write('CENSUS.json',census);write('REPORT.json',report);await browser.close()
try:asyncio.run(main());subprocess.run(['python',str(HERE/'map_census.py')],check=True)
finally:server.shutdown()

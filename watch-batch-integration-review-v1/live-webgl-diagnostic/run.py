"""Standalone branch-only diagnostic. Does not edit app/source assets."""
import asyncio,json,pathlib,threading,http.server,socketserver,sys
from playwright.async_api import async_playwright
from PIL import Image
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE.parent/'watch-current'
OUT=pathlib.Path(sys.argv[2]).resolve() if len(sys.argv)>2 else HERE/'evidence';OUT.mkdir(parents=True,exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
 def log_message(self,*a):pass
server=socketserver.TCPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
report={'scope':'isolated real-WebGL diagnostic, not actual watch cohort or physical GPU performance','runs':[]}
def diff(a,b):
 d=np.abs(a.astype(float)-b.astype(float));return{'mean':float(d.mean()),'fraction_over8':float((d.max(2)>8).mean()),'max':float(d.max()),'pass':bool(d.mean()<.1 and (d.max(2)>8).mean()<.001)}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':512,'height':384});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.route('**/__diagnostic__',lambda route:route.fulfill(body=(HERE/'diagnostic.html').read_text(),content_type='text/html'))
  try:
   await page.goto(f'http://127.0.0.1:{server.server_address[1]}/__diagnostic__');await page.wait_for_function('window.diagnosticReady===true');images={}
   for release in ['baseline','candidate']:
    for state in ['unchanged','detached','other_scene','reparent_transformed','position_revision']:
     r={'release':release,'state':state,'context':await page.evaluate('([r,s])=>setupDiagnostic(r,s)',[release,state]),'samples':[]};report['runs'].append(r)
     assert r['context']['revision']=='187' and r['context']['webgl2'] and r['context']['batch']['meshes']==8,r
     for i,on in enumerate([True,False,True]):
      r['samples'].append(await page.evaluate('(v)=>renderDiagnostic(v)',on));f=OUT/f'{release}-{state}-{i}.png';await page.locator('canvas').screenshot(path=str(f));images[(release,state,i)]=np.asarray(Image.open(f))
     r['on_off']=diff(images[(release,state,0)],images[(release,state,1)]);r['repeat']=diff(images[(release,state,0)],images[(release,state,2)])
     r['changed_from_unmodified_control']=diff(images[(release,'unchanged',1)],images[(release,state,1)])
   report['cross_unbatched']={s:diff(images[('baseline',s,1)],images[('candidate',s,1)]) for s in ['unchanged','detached','other_scene','reparent_transformed','position_revision']}
   assert all(x['on_off']['pass'] and x['repeat']['pass'] for x in report['runs'] if x['release']=='candidate')
   assert all(x['repeat']['pass'] for x in report['runs'])
   assert all(not x['on_off']['pass'] for x in report['runs'] if x['release']=='baseline' and x['state'] in ['detached','other_scene','position_revision'])
   assert all(not x['changed_from_unmodified_control']['pass'] for x in report['runs'] if x['state']!='unchanged'),'Vacuous mutation'
   assert all(x['pass'] for x in report['cross_unbatched'].values())
   assert not errors,errors
   assert all(s['webglError']==0 and all(s['restoredVisibility']) for x in report['runs'] for s in x['samples'])
   report['passed']=True
  finally:report['errors']=errors;(OUT/'REPORT.json').write_text(json.dumps(report,indent=2));await b.close()
try:asyncio.run(main())
finally:server.shutdown()

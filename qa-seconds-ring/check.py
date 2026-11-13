from playwright.sync_api import sync_playwright
from PIL import Image,ImageStat,ImageChops
import json,os,base64,io,hashlib
from pathlib import Path
D=Path('qa-seconds-ring');O=D/'evidence';O.mkdir(exist_ok=True)
rid='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
r={'release':rid,'complete':False,'errors':[],'runs':{},'routes':[]}
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 try:
  for mode in ['reference','packed-raw','packed-meshopt']:
   ctx=b.new_context(viewport={'width':800,'height':800},device_scale_factor=1);p=ctx.new_page();p.set_default_timeout(300000);p.on('pageerror',lambda e:r['errors'].append(str(e)));req=[];p.on('request',lambda q:req.append(q.url))
   if mode!='reference':
    def route(q):
     r['routes'].append({'mode':mode,'url':q.request.url});q.fulfill(path=str(D/('optimized-assets/face.meshopt.glb' if mode=='packed-meshopt' else 'face-svg04-seconds-candidate.glb')))
    p.route('**/optimized-assets/premium-face__face-svg04.meshopt.glb*' if mode=='packed-meshopt' else '**/premium-face/face-svg04.glb*',route)
   asset='meshopt' if mode=='packed-meshopt' else 'raw'
   url=f'http://127.0.0.1:8768/preview-b/releases/{rid}/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets={asset}&light=softbox&antialias=smaa&tickBatch=1'
   p.goto(url,wait_until='domcontentloaded',timeout=60000);p.wait_for_function('window.__ringQA?.status().ready',timeout=300000);setup=p.evaluate('__ringQA.setup()');p.evaluate('__ringQA.freezePose()');p.wait_for_timeout(1000);p.evaluate('__ringQA.lock()')
   if mode=='reference':p.evaluate('__ringQA.set(true)')
   geo=p.evaluate('__ringQA.geometry()');assert geo['vertices']==3088 and geo['indices']==9216
   rr={'geometry':geo,'setup':setup,'states':[],'requests':req};r['runs'][mode]=rr
   for kind in ['close','assembled','exploded']:
    if kind!='close':p.evaluate('(k)=>__ringQA.context(k)',kind)
    f=p.evaluate('__ringQA.frame()');raw=base64.b64decode(f.pop('png').split(',')[1]);(O/f'{mode}-{kind}.png').write_bytes(raw);im=Image.open(io.BytesIO(raw)).convert('RGB');assert max(ImageStat.Stat(im).stddev)>5 and len(im.getcolors(maxcolors=10000000)or[])>100,'blank canvas';f['kind']=kind;rr['states'].append(f);print(mode,kind,flush=True)
    if kind=='close':
     hit=p.evaluate('__ringQA.pickProbe()');p.mouse.click(hit['x'],hit['y']);message=p.locator('#viewer-status').text_content();assert geo['name'] in message,(hit,message);rr['picking']={'hit':hit,'announcement':message}
    (O/'report.json').write_text(json.dumps(r,indent=2))
   if mode!='reference':assert any(x['mode']==mode for x in r['routes'])
   if mode=='packed-meshopt':assert not any('/premium-face/face-svg04.glb' in u for u in req),'compressed face fell back to original raw'
   ctx.close()
  ref=r['runs']['reference']
  for mode in ['packed-raw','packed-meshopt']:
   c=r['runs'][mode];assert c['geometry']==ref['geometry']
   for a,z in zip(ref['states'],c['states']):
    assert a['kind']==z['kind']
    for k in ['camera','target','zoom','world','projection']:assert a['status'][k]==z['status'][k],(mode,k)
    for k in ['calls','triangles']:assert a['render'][k]==z['render'][k]
    aa=Image.open(O/f"reference-{a['kind']}.png").convert('RGB');bb=Image.open(O/f"{mode}-{a['kind']}.png").convert('RGB');diff=ImageChops.difference(aa,bb);means=ImageStat.Stat(diff).mean;c.setdefault('pixelDiffs',[]).append({'kind':a['kind'],'mean':means,'max':diff.getextrema()});assert max(means)<.1,(mode,a['kind'],means)
  assert not r['errors'];r['complete']=True
 except Exception as e:r['error']=repr(e);print('QA FAILURE',repr(e),flush=True)
 finally:(O/'report.json').write_text(json.dumps(r,indent=2));b.close()
if not r['complete']:raise SystemExit(1)

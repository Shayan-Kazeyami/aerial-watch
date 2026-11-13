from playwright.sync_api import sync_playwright
from PIL import Image,ImageStat
import json,os,base64,io
O='qa-seconds-ring/evidence';os.makedirs(O,exist_ok=True)
release='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
url=f'http://127.0.0.1:8768/preview-b/releases/{release}/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&tickBatch=1'
r={'release':release,'url':url,'complete':False,'capture':'synchronous actual composer canvas, no UI','errors':[],'states':[]}
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':800,'height':800},device_scale_factor=1);page.set_default_timeout(300000);page.on('pageerror',lambda e:r['errors'].append(str(e)))
 try:
  page.goto(url,wait_until='domcontentloaded',timeout=60000);page.wait_for_function('window.__ringQA?.status().ready',timeout=300000)
  r['setup']=page.evaluate('__ringQA.setup()');page.wait_for_timeout(2000);r['locked']=page.evaluate('__ringQA.lock()')
  for kind in ['close','assembled','exploded']:
   if kind!='close':page.evaluate('(kind)=>__ringQA.context(kind)',kind)
   captures=[]
   for name,enabled in [('original',False),('candidate',True),('repeat',False)]:
    page.evaluate('(v)=>__ringQA.set(v)',enabled)
    f=page.evaluate('__ringQA.frame()');raw=base64.b64decode(f.pop('png').split(',')[1]);open(f'{O}/{kind}-{name}.png','wb').write(raw);im=Image.open(io.BytesIO(raw)).convert('RGB');stats=ImageStat.Stat(im);assert len(im.getcolors(maxcolors=10000000) or [])>100 and max(stats.stddev)>5,'blank actual canvas';captures.append((f,im.tobytes()));r['states'].append({'kind':kind,'name':name,**f});open(O+'/report.json','w').write(json.dumps(r,indent=2));print(kind,name,flush=True)
   a,c,z=captures
   assert a[1]==z[1],kind+' original repeat drift'
   for field in ['camera','target','zoom','world','projection']:assert a[0]['status'][field]==c[0]['status'][field]==z[0]['status'][field],kind+' '+field
   for field in ['triangles','calls']:assert a[0]['render'][field]==c[0]['render'][field]==z[0]['render'][field]
  assert not r['errors'];r['complete']=True
 except Exception as e:r['error']=repr(e);print('QA FAILURE',repr(e),flush=True)
 finally:open(O+'/report.json','w').write(json.dumps(r,indent=2));b.close()
if not r['complete']:raise SystemExit(1)

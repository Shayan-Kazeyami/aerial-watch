from playwright.sync_api import sync_playwright
from PIL import Image,ImageStat
import json,os,time
os.makedirs('qa-seconds-ring/evidence',exist_ok=True)
release='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
url=f'http://127.0.0.1:8768/preview-b/releases/{release}/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&tickBatch=1'
r={'release':release,'url':url,'complete':False,'capture':'browser screenshot canvas; native AO unchanged'}
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1200,'height':900},device_scale_factor=1)
 page.on('pageerror',lambda e: print('PAGE ERROR',str(e),flush=True))
 try:
  page.goto(url,wait_until='domcontentloaded',timeout=60000);page.wait_for_function('window.__ringQA?.status().ready',timeout=300000)
  r['setup']=page.evaluate('window.__ringQA.setup()');assert r['setup']['visible'] and r['setup']['rootvisible'];page.wait_for_timeout(6000);r['before']=page.evaluate('window.__ringQA.lock()');page.wait_for_timeout(2000)
  canvas=page.locator('#stage canvas').first
  canvas.screenshot(path='qa-seconds-ring/evidence/original.png',timeout=60000)
  r['candidate']=page.evaluate('window.__ringQA.set(true)');page.wait_for_timeout(2000);canvas.screenshot(path='qa-seconds-ring/evidence/candidate.png',timeout=60000);r['after']=page.evaluate('window.__ringQA.status()')
  for field in ['camera','target','zoom','world','projection']:
   assert r['before'][field]==r['after'][field],f'camera changed: {field}'
  r['images']={}
  for name in ['original','candidate']:
   im=Image.open('qa-seconds-ring/evidence/'+name+'.png').convert('RGB'); st=ImageStat.Stat(im); colors=len(im.getcolors(maxcolors=10000000) or []);r['images'][name]={'size':im.size,'stddev':st.stddev,'unique_colors':colors};assert colors>100 and max(st.stddev)>5,'blank image'
  r['complete']=True
 except Exception as e:r['error']=repr(e);print('QA FAILURE',repr(e),flush=True)
 finally:open('qa-seconds-ring/evidence/report.json','w').write(json.dumps(r,indent=2));browser.close()
if not r['complete']:raise SystemExit(1)

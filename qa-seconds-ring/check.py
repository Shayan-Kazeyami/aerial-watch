from playwright.sync_api import sync_playwright
import json,os,time
os.makedirs('qa-seconds-ring/evidence',exist_ok=True)
release='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
url=f'http://127.0.0.1:8768/preview-b/releases/{release}/atelier-preview.html?quality=efficient&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&tickBatch=1'
r={'release':release,'url':url,'complete':False}
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1400,'height':1000},device_scale_factor=1)
 try:
  page.goto(url,wait_until='domcontentloaded',timeout=60000);page.wait_for_function('window.__ringQA?.status().ready',timeout=120000);r['before']=page.evaluate('window.__ringQA.setup()');assert r['before']['visible'] and r['before']['rootvisible'],'Ring not visible';page.wait_for_timeout(2500);page.screenshot(path='qa-seconds-ring/evidence/original.png');r['candidate']=page.evaluate('window.__ringQA.set(true)');page.wait_for_timeout(2500);page.screenshot(path='qa-seconds-ring/evidence/candidate.png');r['after']=page.evaluate('window.__ringQA.status()');r['complete']=True
 except Exception as e:r['error']=str(e);page.screenshot(path='qa-seconds-ring/evidence/error.png')
 finally:
  open('qa-seconds-ring/evidence/report.json','w').write(json.dumps(r,indent=2));browser.close()
if not r['complete']:raise SystemExit(1)

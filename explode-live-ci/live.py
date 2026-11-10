import asyncio, json, pathlib, os, urllib.request, hashlib, time
from playwright.async_api import async_playwright
RID='36f0aca93a5c9e1cf01e0237aabcc0c71ee96fbfc2cc64394b74b35c32cf75e8'
REV='319a0e010d7457d542e5c6901d62cac90d920f48bbc4b47f592649f44389739d'
HOME='https://shayan-kazeyami.github.io/aerial-watch/'
BASE=HOME+'preview-b/releases/'+RID+'/'
OUT=pathlib.Path('explode-live-output');OUT.mkdir(exist_ok=True)
SCOPE=os.environ.get('QA_SCOPE','desktop')
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache'}),timeout=45) as r:return r.read()
for _ in range(30):
 try:
  home=fetch(HOME+'?verify='+RID).decode()
  if 'watch-home-explode-36f0aca9.js' in home and RID in home:break
 except Exception:pass
 time.sleep(10)
else:raise RuntimeError('Production entry did not reach expected explosion release')
assert RID in fetch(HOME+'watch-home-explode-36f0aca9.js').decode()
m=json.loads(fetch(BASE+'deployment-manifest.json'));canonical={k:m[k] for k in ['schemaVersion','localFiles','references']}
assert hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()==RID
for name in ['assembly-explode.js','assembly-review.js','atelier-preview.js','atelier-preview.css','quality-study/viewer-revision.json']:
 f=next(f for f in m['localFiles'] if f['path']==name);b=fetch(BASE+name)
 assert len(b)==f['sizeBytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],name
assert json.loads(fetch(BASE+'quality-study/viewer-revision.json'))['digest']==REV
async def main():
 report={'scope':SCOPE,'releaseId':RID,'revision':REV,'checks':['public loader and changed-module hashes match verified release'],'errors':[],'renderer':'Chromium SwiftShader; not physical-device performance'}
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   mobile=SCOPE=='mobile';ctx=await browser.new_context(viewport={'width':430 if mobile else 1180,'height':850 if mobile else 820},device_scale_factor=1,is_mobile=mobile,has_touch=mobile);page=await ctx.new_page();page.set_default_timeout(90000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
   await page.goto(HOME+'?quality=efficient&verify='+RID,wait_until='domcontentloaded',timeout=90000)
   frame=page.frame_locator('#watch-viewer');await frame.locator('body[data-ready="true"]').wait_for(timeout=240000);await page.locator('#watch-loading').wait_for(state='hidden',timeout=60000)
   inner=next(f for f in page.frames if '/preview-b/releases/'+RID+'/' in f.url)
   assert (await inner.evaluate('assemblyInspect().presentation.interactive'))
   report['frame']=inner.url;report['quality']=await inner.evaluate('assemblyInspect().renderQuality')
   button=frame.locator('.task-dock [data-mode=explode]');await (button.tap() if mobile else button.click())
   await inner.wait_for_function('assemblyInspect().explosion.amount===1 && !assemblyInspect().explosion.animating',timeout=120000)
   layers=await inner.evaluate('assemblyInspect().explosion.layers');assert sum(l['sourceParts'] for l in layers)==166;assert len([l for l in layers if l['sourceParts']])==6
   report['checks'].append('one public click/tap explodes all six movement layers');report['layers']=layers
   await frame.locator('#atelier-explosion').fill('45');await inner.wait_for_function('assemblyInspect().explosion.amount===.45',timeout=120000)
   await frame.locator('.quality').click();await page.keyboard.press('Escape');await button.click();assert await frame.locator('#atelier-explosion').input_value()=='45';report['checks'].append('utility dismissal retains partial separation')
   await frame.locator('#atelier-reassemble').click();await inner.wait_for_function('assemblyInspect().explosion.amount===0',timeout=120000);await button.click();await inner.wait_for_function('assemblyInspect().explosion.amount===1',timeout=120000)
   assert await frame.locator('#home').is_visible();await (frame.locator('#home').tap() if mobile else frame.locator('#home').click());await inner.wait_for_function('assemblyInspect().explosion.amount===0',timeout=120000);assert await frame.locator('.task-dock [data-mode=explore]').get_attribute('aria-pressed')=='true'
   report['checks'].append('reassemble, repeated explode and visible Reset return to Explore');assert not report['errors'],report['errors'];report['passed']=True
  except Exception as e:report['passed']=False;report['failure']=repr(e);raise
  finally:
   (OUT/(SCOPE+'.json')).write_text(json.dumps(report,indent=2));print('LIVE_REPORT '+json.dumps(report),flush=True)
   try:await asyncio.wait_for(browser.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

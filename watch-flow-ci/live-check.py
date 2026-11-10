import asyncio,base64,hashlib,json,pathlib,textwrap,time,urllib.request
from playwright.async_api import async_playwright
HOME='https://shayan-kazeyami.github.io/aerial-watch/'
RID='99d5275244fdabbc301fba262d59e612e7f511121e5e79a5dae5bf936e222e75'
BASE=HOME+'preview-b/releases/'+RID+'/'
OUT=pathlib.Path('live-evidence');OUT.mkdir(exist_ok=True)
def fetch(url):
 return urllib.request.urlopen(url,timeout=45).read()
for attempt in range(30):
 try:
  home=fetch(HOME+'?verify='+RID).decode()
  if 'watch-home-loading-v4.js' in home and RID in home:break
 except Exception:pass
 time.sleep(10)
else:raise RuntimeError('Production entry has not reached expected navigation release')
loader=fetch(HOME+'watch-home-loading-v4.js').decode();assert RID in loader
m=json.loads(fetch(BASE+'deployment-manifest.json'))
canonical={k:m[k] for k in ['schemaVersion','localFiles','references']}
assert hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()==RID
verified=[]
for name in ['atelier-preview.html','atelier-preview.js','atelier-preview.css','atelier-navigation.js','assembly-review.js','assembly-crown-hotspot.js','quality-study/viewer-revision.json']:
 f=next(f for f in m['localFiles'] if f['path']==name);b=fetch(BASE+name)
 assert len(b)==f['sizeBytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],name
 verified.append(name)
print('LIVE_IDENTITIES '+json.dumps({'releaseId':RID,'verified':verified}),flush=True)
async def main():
 async with async_playwright() as p:
  for mobile in [False,True]:
   browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
   context=await browser.new_context(viewport={'width':430 if mobile else 1180,'height':850 if mobile else 820},device_scale_factor=1,is_mobile=mobile,has_touch=mobile)
   page=await context.new_page();page.set_default_timeout(60000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto(HOME+'?verify='+RID,wait_until='domcontentloaded',timeout=90000)
   await page.locator('#watch-viewer').wait_for()
   frame=page.frame_locator('#watch-viewer')
   await frame.locator('body[data-ready="true"]').wait_for(timeout=240000)
   await page.locator('#watch-loading').wait_for(state='hidden',timeout=30000)
   src=await page.locator('#watch-viewer').get_attribute('src');assert RID in src
   inner=next(f for f in page.frames if RID in f.url)
   runtime=await inner.evaluate('assemblyInspect()');assert runtime['presentation']['interactive'] and runtime['renderQuality']=='studio'
   assert await frame.locator('.inspection-tools').count()==0
   async def pose():return await inner.evaluate('({camera:assemblyInspect().camera,target:assemblyInspect().target,view:assemblyInspect().view,interior:assemblyInspect().interiorView})')
   def same(a,b):return a['view']==b['view'] and a['interior']==b['interior'] and all(abs(x-y)<1e-9 for k in ['camera','target'] for x,y in zip(a[k],b[k]))
   async def settle():
    old=await pose();stable=0
    for _ in range(90):
     await asyncio.sleep(.4);new=await pose();stable=stable+1 if same(old,new) else 0;old=new
     if stable>=3:return new
    raise RuntimeError('Camera did not settle')
   if not mobile:
    await frame.locator('.task-dock [data-mode="inside"]').click();before=await settle()
    await frame.locator('.quality').click();assert await frame.locator('.task-dock [data-mode="inside"]').get_attribute('aria-pressed')=='true'
    await page.keyboard.press('Escape');assert await frame.locator('#context').is_hidden();assert same(before,await pose())
    await frame.locator('.atelier-more').click();await frame.locator('[data-inspection="wireframe"]').click();await frame.locator('#atelier-inspection-reset').click();await frame.locator('#close').click()
   else:
    await frame.locator('.task-dock [data-mode="time"]').tap();await settle();await frame.locator('.task-dock [data-mode="time"]').tap()
    assert await frame.locator('#context').is_hidden();await frame.locator('.crown-hotspot').tap()
    await inner.wait_for_function('document.getElementById("crown-pull").getAttribute("aria-pressed")==="true"')
   await frame.locator('#home').click();await settle();assert await frame.locator('#context').is_hidden()
   assert await frame.locator('.task-dock [data-mode="explore"]').get_attribute('aria-pressed')=='true'
   if await frame.locator('#motion').get_attribute('aria-pressed')=='true':await frame.locator('#motion').click()
   assert not errors,errors
   name='mobile-live' if mobile else 'desktop-live'
   report={'surface':name,'url':page.url,'frame':src,'viewport':page.viewport_size,'quality':runtime['renderQuality'],'presentation':runtime['presentation'],'errors':errors,'checks':['published identities','root loader completes','exact Studio runtime','temporary panels retain task' if not mobile else 'direct crown tap after time panel toggle','reset restores Explore'],'renderer':'Chromium SwiftShader software rendering'}
   (OUT/(name+'.json')).write_text(json.dumps(report,indent=2));print('LIVE_REPORT '+json.dumps(report),flush=True)
   try:
    shot=await page.screenshot(type='jpeg',quality=85,timeout=90000);(OUT/(name+'.jpg')).write_bytes(shot)
    print('IMAGE_START '+name+'.jpg',flush=True)
    for line in textwrap.wrap(base64.b64encode(shot).decode(),1000):print(line)
    print('IMAGE_END '+name+'.jpg',flush=True)
   finally:await browser.close()
asyncio.run(main())

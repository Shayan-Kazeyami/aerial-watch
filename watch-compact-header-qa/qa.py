import asyncio,json,os,pathlib,hashlib
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).resolve().parent;O=P/'output';O.mkdir(exist_ok=True)
RID='a09e63edcfc275e017ff9655270f0c1c733a95d075f55c0306e84ba70d1a07a8';ROOT='https://shayan-kazeyami.github.io/aerial-watch/'
ARM=os.environ.get('ARM','candidate');R={'arm':ARM,'release':RID,'errors':[],'rows':[]}
async def main():
 async with async_playwright() as e:
  b=await e.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'])
  try:
   for width,height in [(360,800),(390,844),(430,932),(932,430)]:
    page=await b.new_page(viewport={'width':width,'height':height},reduced_motion='reduce');page.set_default_timeout(180000)
    page.on('pageerror',lambda e:R['errors'].append(str(e)))
    async def route(r):
     response=await r.fetch();raw=await response.body();assert hashlib.sha256(raw).hexdigest()=='9be7d9787c8891a76761d08571b57674bcad72fa37e2db17c425a6ee13966ed2'
     await r.fulfill(response=response,body=raw+b'\n'+(P/'header.css').read_bytes())
    if ARM=='candidate':await page.route('**/'+RID+'/atelier-preview.css*',route)
    await page.goto(ROOT+'?quality=efficient&header-proof='+ARM,wait_until='domcontentloaded')
    await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=360000)
    f=next(f for f in page.frames if RID in f.url)
    await f.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'")
    await page.wait_for_timeout(900)
    sample="""()=>{const rect=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};const ids=['.wordmark','.masthead .quality','#home','.atelier-more'];const targets=ids.map(s=>{const n=document.querySelector(s),r=rect(n),hit=document.elementFromPoint(r.x+r.w/2,r.y+r.h/2);return {selector:s,...r,hit:hit===n||n.contains(hit),text:n.innerText}});const s=assemblyInspect();return {targets,stage:rect(document.querySelector('#stage')),canvas:[document.querySelector('canvas').width,document.querySelector('canvas').height],camera:[...s.camera,...s.target],quality:s.renderQuality,overflow:document.documentElement.scrollWidth>innerWidth,backend:document.querySelector('#atelier-backend-indicator').textContent};}"""
    before=await f.evaluate(sample);row={'viewport':[width,height],'before':before};R['rows'].append(row)
    for t in before['targets']:
     assert t['hit'],(width,t)
     if t['selector']!='.wordmark' or width<height:assert t['h']>=44 and t['w']>=44,(width,t)
    if width>height:row['existingLandscapeBrandHeight']=before['targets'][0]['h']
    if ARM=='candidate' and width<height:
     ys=[t['y']for t in before['targets']];assert max(ys)-min(ys)<4,(width,ys)
     for i,a in enumerate(before['targets']):
      for c in before['targets'][i+1:]:assert a['x']+a['w']<=c['x']+.2 or c['x']+c['w']<=a['x']+.2,(width,a,c)
    assert not before['overflow']
    await page.screenshot(path=str(O/f'{width}-home.png'))
    for selector in ['.masthead .quality','.atelier-more','.task-dock [data-mode=capture]']:
     await f.locator(selector).click();await f.locator('#context').wait_for(state='visible');await page.wait_for_timeout(200)
     opened=await f.evaluate(sample);assert opened['stage']==before['stage'],(width,selector,'stage');assert opened['camera']==before['camera'],(width,selector,'camera')
     await f.locator('#close').click();assert await f.locator('#context').is_hidden()
    await f.locator('.task-dock [data-mode=explode]').click();await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    await f.locator('#atelier-layer-focus').select_option('balance');await f.wait_for_function("assemblyInspect().layerFocus.selected==='balance'")
    await f.locator('#home').click();await page.wait_for_timeout(300)
    assert await f.evaluate("assemblyInspect().layerFocus.selected==='balance'&&assemblyInspect().explosion.amount===1")
    await page.screenshot(path=str(O/f'{width}-inspect.png'))
    row['passed']=True;await page.close()
   assert not R['errors'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
if __name__=='__main__':asyncio.run(main())

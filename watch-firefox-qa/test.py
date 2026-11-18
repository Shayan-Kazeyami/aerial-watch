import asyncio,json,os,pathlib,hashlib
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).resolve().parent;O=P/'output';O.mkdir(exist_ok=True)
RID='87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2';ROOT='https://shayan-kazeyami.github.io/aerial-watch/'
ARM=os.environ.get('ARM','candidate');R={'arm':ARM,'release':RID,'errors':[],'rows':[],'scope':'Desktop Firefox with software GL, portrait/landscape viewport, not Android/physical-device performance'}
async def main():
 async with async_playwright() as e:
  b=await e.firefox.launch(headless=False)
  try:
   for width,height in [(390,844),(932,430)]:
    page=await b.new_page(viewport={'width':width,'height':height},reduced_motion='reduce');page.set_default_timeout(180000)
    page.on('pageerror',lambda e:R['errors'].append(str(e)))
    await page.goto(ROOT+'?quality=efficient&firefox-proof=1',wait_until='domcontentloaded')
    await page.frame_locator('#watch-viewer').locator('body[data-ready=true]').wait_for(timeout=360000)
    f=next(x for x in page.frames if RID in x.url)
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
    dock=await f.locator('.task-dock').evaluate('''n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,display:getComputedStyle(n).display,opacity:getComputedStyle(n).opacity,buttons:[...n.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {label:b.innerText,w:r.width,h:r.height,hit:b===hit||b.contains(hit)}})}}''')
    row['dock']=dock;assert dock['display']!='none' and float(dock['opacity'])>0 and dock['y']+dock['h']<=height+.5
    assert len(dock['buttons'])==5 and all(t['hit'] and t['w']>=44 and t['h']>=44 for t in dock['buttons']),dock
    await f.locator('.task-dock').screenshot(path=str(O/f'{width}-dock.png'))
    await page.screenshot(path=str(O/f'{width}-home.png'))
    await page.wait_for_timeout(350)
    await page.screenshot(path=str(O/f'{width}-home-repeat.png'))
    for selector in ['.masthead .quality','.atelier-more','.task-dock [data-mode=capture]']:
     await f.locator(selector).click();await f.locator('#context').wait_for(state='visible');await page.wait_for_timeout(200)
     opened=await f.evaluate(sample);assert opened['stage']==before['stage'],(width,selector,'stage');assert opened['camera']==before['camera'],(width,selector,'camera')
     transient=await f.evaluate('''()=>{const box=()=>{const r=document.querySelector('#assembly-canvas').getBoundingClientRect();return [r.x,r.y,r.width,r.height]};const before=box();document.querySelector('#close').click();return {before,after:box()}}''');assert transient['before']==transient['after'],(width,selector,transient);assert await f.locator('#context').is_hidden()
    await f.locator('.task-dock [data-mode=explode]').click();await f.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating')
    await f.locator('#atelier-layer-focus').select_option('balance');await f.wait_for_function("assemblyInspect().layerFocus.selected==='balance'")
    await f.locator('#home').click();await page.wait_for_timeout(300)
    assert await f.evaluate("assemblyInspect().layerFocus.selected==='balance'&&assemblyInspect().explosion.amount===1")
    await page.screenshot(path=str(O/f'{width}-inspect.png'))
    await f.locator('#atelier-layer-overview').click();await f.wait_for_function('!assemblyInspect().layerFocus.selected')
    assert await f.evaluate('assemblyInspect().explosion.amount===1')
    await f.locator('#home').click();assert await f.evaluate('assemblyInspect().explosion.amount===1');assert await f.locator('#context').is_visible()
    await f.locator('#atelier-reassemble').click();await f.wait_for_function('assemblyInspect().explosion.amount===0&&!assemblyInspect().explosion.animating')
    transient=await f.evaluate("()=>{const box=()=>{const r=document.querySelector('#assembly-canvas').getBoundingClientRect();return [r.x,r.y,r.width,r.height]};const before=box();document.querySelector('#close').click();return {before,after:box()}}")
    assert transient['before']==transient['after'],(width,transient);row['fullSequenceClose']=transient
    await f.locator('.atelier-more').focus();await f.locator('.atelier-more').press('Enter');await f.locator('#close').wait_for(state='visible');assert await f.locator('#close').evaluate('(e)=>e===document.activeElement')
    await f.locator('#close').press('Escape');assert await f.locator('#context').is_hidden();assert await f.locator('.atelier-more').evaluate('(e)=>e===document.activeElement')
    row['keyboardOpenCloseReturn']=True
    row['passed']=True;await page.close()
   assert not R['errors'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
if __name__=='__main__':asyncio.run(main())

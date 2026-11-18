import asyncio,json,pathlib
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True);R=[]
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for rid in ['a09e63edcfc275e017ff9655270f0c1c733a95d075f55c0306e84ba70d1a07a8','bf858771be73667b8a9ca3a459090e671786783fbfb5faf471522c580b8f0710','7125e9612de10991ebb13eb312268bae19ed3825bed3da8a508ed1ec33be2cd5']:
    page=await b.new_page(viewport={'width':430,'height':932},is_mobile=True,has_touch=True);page.set_default_timeout(180000)
    await page.goto('http://127.0.0.1:8765/preview-b/releases/'+rid+'/atelier-preview.html?quality=efficient',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=360000)
    await page.locator('.task-dock [data-mode=explode]').tap();await page.wait_for_function('assemblyInspect().explosion.amount===1&&!assemblyInspect().explosion.animating');await page.wait_for_function("document.body.dataset.panelOpen==='true'")
    r=await page.evaluate('''async()=>{const s=()=>{const r=document.querySelector('#assembly-canvas').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,panel:document.body.dataset.panelOpen,hidden:document.querySelector('#context').hidden}};const before=s();document.querySelector('#close').click();const immediate=s();await new Promise(requestAnimationFrame);const frame1=s();await new Promise(requestAnimationFrame);return {before,immediate,frame1,frame2:s()}}''');r['release']=rid;R.append(r);assert (r['before']['y']==r['immediate']['y'] and r['before']['h']==r['immediate']['h'])==(rid!='bf858771be73667b8a9ca3a459090e671786783fbfb5faf471522c580b8f0710');print(json.dumps(r),flush=True);await page.close()
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())

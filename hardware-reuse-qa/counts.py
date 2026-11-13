import asyncio,pathlib,json,hashlib,base64,os
from playwright.async_api import async_playwright
R=pathlib.Path('hardware-reuse-qa');O=R/'count-evidence';O.mkdir(exist_ok=True);RID=os.getenv('COUNT_RELEASE','63600a544b71214dcbfceee96a3eac0dbfa48bca7d42d59425acd43bae131bfd');URL=f'http://127.0.0.1:8878/preview-b/releases/{RID}/atelier-preview.html?quality=efficient&normalStream=1&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&tickBatch=1';report={'release':RID,'errors':[]};probe=(R/'probe.js').read_bytes()+b'\n'+(R/'inventory-probe.js').read_bytes()
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=await b.new_context(viewport={'width':1000,'height':1000},device_scale_factor=1);page=await ctx.new_page();page.set_default_timeout(180000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
  async def route(r):
   response=await r.fetch();body=await response.body();report['executedModuleSHA256']=hashlib.sha256(body).hexdigest();await r.fulfill(response=response,body=body+probe)
  await page.route('**/assembly-review.js*',route)
  try:
   await page.goto(URL,wait_until='domcontentloaded');await page.wait_for_function('window.__reuseQa?.ready&&window.assemblyInspect?.().presentation.interactive',timeout=240000)
   for name,params in [('assembled',dict(view='watch',explode=0)),('exploded',dict(view='watch',explode=1)),('movement',dict(view='movement',explode=0))]:
    s=await page.evaluate('(p)=>__reuseQa.show(p)',params);im=s.pop('image');(O/f'{name}.png').write_bytes(base64.b64decode(im.split(',')[1]));inventory=await page.evaluate('__triangleInventory()');report[name]={'inventory':inventory,'camera':s['camera'],'framebuffer':s['framebuffer'],'rendererInfo':s['rendererInfo']};print(name,json.dumps({k:v for k,v in inventory.items()if k!='rows'}),flush=True)
   assert not report['errors'];report['passed']=True
  finally:(O/'report.json').write_text(json.dumps(report,indent=2));await b.close()
asyncio.run(main())

import asyncio,base64,json,pathlib,hashlib
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
D=pathlib.Path('isolated-screw-sharing');O=D/'evidence';O.mkdir(exist_ok=True)
RID='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':800,'height':800},device_scale_factor=1);page.set_default_timeout(240000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  async def inject(route):
   resp=await route.fetch();await route.fulfill(response=resp,body=(await resp.text())+'\n'+(D/'probe.js').read_text())
  await page.route('**/assembly-review.js*',inject)
  try:
   await page.goto('https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/'+RID+'/atelier-preview.html',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for();await page.wait_for_function('window.screwQa && document.querySelector("#stage").dataset.cameraReady === "true"');s=await page.evaluate('screwQa.setup()');results=[]
   for i,c in enumerate([{'shared':False,'explode':0,'dispose':False},{'shared':True,'explode':0,'dispose':False},{'shared':False,'explode':0,'dispose':False},{'shared':False,'explode':1,'dispose':False},{'shared':True,'explode':1,'dispose':False},{'shared':True,'explode':1,'dispose':True}]):
    r=await page.evaluate('(c)=>screwQa.capture(c)',c);png=base64.b64decode(r.pop('png').split(',')[1]);(O/f'{i}.png').write_bytes(png);r['case']=c;results.append(r);print(i,json.dumps(r),flush=True)
   assert results[0]['rows']==results[1]['rows']==results[2]['rows'];assert results[3]['rows']==results[4]['rows']==results[5]['rows'];assert results[1]['refs']=={'position':1,'normal':1,'uv':6};assert results[0]['refs']['position']==6 and results[0]['refs']['normal']==6
   for a,c in [(0,1),(0,2),(3,4),(4,5)]:
    assert results[a]['render']['calls']==results[c]['render']['calls'] and results[a]['render']['triangles']==results[c]['render']['triangles'];i1=Image.open(O/f'{a}.png').convert('RGB');i2=Image.open(O/f'{c}.png').convert('RGB');assert max(ImageStat.Stat(i1).stddev)>2,'blank';diff=ImageChops.difference(i1,i2);assert diff.getbbox() is None,(a,c,'pixel mismatch')
   assert not errors,errors;(O/'results.json').write_text(json.dumps({'setup':s,'cases':results,'errors':errors,'exactPixels':True},indent=2))
  finally: await b.close()
asyncio.run(run())

import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
p=Path('qa-backplate-sharing');rows=[];sources=[];errors=[]
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':900,'height':700});page.on('pageerror',lambda e:errors.append(str(e)));await page.goto('http://127.0.0.1:8871/qa-backplate-sharing/harness.html');await page.wait_for_function('window.ready===true',timeout=60000)
  for route in ['raw','meshopt']:
   sources.append(await page.evaluate('(r)=>setup(r)',route))
   for view in ['front','oblique','edge']:
    for kind in ['original','candidate','original-repeat']:
     r=await page.evaluate('([kind,view])=>capture(kind,view)',[kind,view]);r['captureKind']=kind;await page.mouse.click(450,350);r['pointerPick']=await page.evaluate('window.lastPick');assert r['pointerPick']['assemblyId']=='CASEBACK-INSERT';rows.append(r);await page.locator('canvas').screenshot(path=str(p/f'{route}-{view}-{kind}.png'))
  await b.close()
 (p/'render-results.json').write_text(json.dumps({'sources':sources,'captures':rows,'errors':errors},indent=2));print(json.dumps({'sources':sources,'captures':len(rows),'errors':errors},indent=2))
asyncio.run(main())
from PIL import Image,ImageChops,ImageStat
report=json.load(open(p/'render-results.json'));assert not report['errors'];comparisons=[]
for route in ['raw','meshopt']:
 for view in ['front','oblique','edge']:
  images=[Image.open(p/f'{route}-{view}-{kind}.png').convert('RGB') for kind in ['original','candidate','original-repeat']]
  assert max(ImageStat.Stat(images[0]).stddev)>5,'blank PBR canvas'
  for kind,im in zip(['candidate','original-repeat'],images[1:]):
   diff=ImageChops.difference(images[0],im);assert not diff.getbbox(),(route,view,kind,'pixel mismatch');comparisons.append({'route':route,'view':view,'against':kind,'pixelExact':True})
  rr=[x for x in report['captures'] if x['route']==route and x['view']==view]
  for x in rr[1:]:
   for key in ['picks','pointerPick','calls','triangles','camera','projection','sourceVisible']:assert x[key]==rr[0][key],(route,view,key)
for view in ['front','oblique','edge']:
 assert not ImageChops.difference(Image.open(p/f'raw-{view}-original.png'),Image.open(p/f'meshopt-{view}-original.png')).getbbox(),'raw meshopt pixel mismatch'
assert report['sources'][0]['arrays']==report['sources'][1]['arrays'];assert report['sources'][0]['indexHash']==report['sources'][1]['indexHash'];report['pixelComparisons']=comparisons;report['passed']=True;report['scope']='Real canonical source isolated PBR and pointer picking,not full composed viewer orGPU/FPS claim';(p/'render-results.json').write_text(json.dumps(report,indent=2))


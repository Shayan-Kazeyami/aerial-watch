import asyncio,json,pathlib,hashlib,os,traceback
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
ROOT=pathlib.Path.cwd();W=ROOT/'case-topology-lane/recovery-remaining';OUT=W/'evidence';OUT.mkdir(exist_ok=True)
BASE=ROOT if os.environ.get('CI') else ROOT/'case-topology-lane/integration/recovery-75756356';RID='09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29' if os.environ.get('CI') else '75756356ca7b944a5143c519b75d3cac2f8aa62cfcf40302b249f7eefda85f69';REL=BASE/'preview-b/releases'/RID
PORT=os.environ.get('PORT','8768');PREFIX='' if os.environ.get('CI') else 'case-topology-lane/integration/recovery-75756356/';URL=f'http://127.0.0.1:{PORT}/{PREFIX}preview-b/releases/{RID}/atelier-preview.html?quality=efficient'
APPEND=(W/'append-caseback.js').read_bytes();SOURCE=(REL/'assembly-review.js').read_bytes()+b'\n'+APPEND;EXPECTED=hashlib.sha256(SOURCE).hexdigest()
R={'url':URL,'baseRelease':RID,'QAWrapperSHA256':EXPECTED,'setup':'Actual Three.js r187 viewer; Chromium SwiftShader, 430x932 DPR2 Smooth, paused fixed cameras. Private wrapper filename, original runtime files unchanged. Not physical-device FPS.','states':{},'errors':[]}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path=p.chromium.executable_path if os.environ.get('CI') else '/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=await b.new_page(viewport={'width':430,'height':932},device_scale_factor=2,is_mobile=True,has_touch=True);page.set_default_timeout(120000)
  async def atelier(route):
   resp=await route.fetch();src=await resp.text();assert "import('./assembly-review.js?v=atelier-local-1')" in src;await route.fulfill(response=resp,body=src.replace("import('./assembly-review.js?v=atelier-local-1')","import('./assembly-review-caseback-private-qa.js')"))
  async def wrapper(route):
   await route.fulfill(status=200,content_type='text/javascript',body=SOURCE)
  await page.route('**/atelier-preview.js',atelier);await page.route('**/assembly-review-caseback-private-qa.js',wrapper);page.on('pageerror',lambda e:R['errors'].append(str(e)))
  async def response(resp):
   if 'assembly-review-caseback-private-qa.js' in resp.url:R['executedWrapperSHA256']=hashlib.sha256(await resp.body()).hexdigest()
  page.on('response',response)
  try:
   await page.goto(URL,wait_until='domcontentloaded',timeout=120000);print('navigated',flush=True)
   await page.locator('body[data-ready=true]').wait_for(timeout=300000);await page.wait_for_function('document.querySelector("#stage").dataset.cameraReady==="true"',timeout=300000);print('ready',flush=True)
   R['init']=await page.evaluate('casebackQA.init()');assert R['executedWrapperSHA256']==EXPECTED;assert R['init']['before']==19032 and R['init']['after']==16728;print('init',R['init'],flush=True)
   async def compare(state):
    await page.evaluate('casebackQA.freeze()');await page.wait_for_function('casebackQA.settled()',timeout=180000);await page.evaluate('(p)=>casebackQA.pose(p)',state);data={}
    for name,candidate in [('before',False),('after',True),('repeat',False)]:
     data[name]=await page.evaluate('(c)=>casebackQA.set(c)',candidate);(OUT/(state+'-'+name+'.json')).write_text(json.dumps(data[name],indent=2));await page.locator('#assembly-canvas').screenshot(path=str(OUT/(state+'-'+name+'.png')),animations='disabled',timeout=120000)
    assert data['before']['camera']==data['after']['camera']==data['repeat']['camera'],state+' camera drift'
    a=Image.open(OUT/(state+'-before.png')).convert('RGB');z=Image.open(OUT/(state+'-after.png')).convert('RGB');r=Image.open(OUT/(state+'-repeat.png')).convert('RGB');diff=ImageChops.difference(a,z);stat=ImageStat.Stat(diff);repeat=ImageStat.Stat(ImageChops.difference(a,r));diff.save(OUT/(state+'-diff.png'))
    R['states'][state]={'meanAbsoluteDifference255':sum(stat.mean)/3,'repeatBaselineMeanDifference255':sum(repeat.mean)/3,'pixelsOver2':sum(max(p)>2 for p in diff.getdata()),'pixels':a.width*a.height};print(state,R['states'][state],flush=True)
   for mode in ['assembled','back','inner','inner-macro','inner-wire','edge','bore']:await compare(mode)
   assert not R['errors'];R['passed']=True
  except Exception as e:R['passed']=False;R['failure']=repr(e);traceback.print_exc()
  finally:
   (OUT/'report.json').write_text(json.dumps(R,indent=2));print(json.dumps(R),flush=True)
   try:await asyncio.wait_for(b.close(),15)
   except asyncio.TimeoutError:pass
asyncio.run(main())

import asyncio,json,pathlib,tempfile
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True)
ROOT='https://shayan-kazeyami.github.io/aerial-watch/';OWNER='87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2'
ASSETS=['optimized-assets/premium-face__face-svg04.meshopt.glb','optimized-assets/rebuild__assembly.meshopt.glb.gz'];R={'scope':'Public unchanged URLs, isolated fetch without GLB or gzip decoding. Fresh ephemeral versus persistent browser HTTP caches. No application changes.','phases':[],'errors':[]}
async def exercise(ctx,label,phases):
 page=await ctx.new_page();page.set_default_timeout(180000);await page.goto(ROOT+'deployment-manifest.json',wait_until='domcontentloaded');cdp=await ctx.new_cdp_session(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{'cacheDisabled':False});req={}
 cdp.on('Network.requestWillBeSent',lambda e:req.setdefault(e['requestId'],{}).update(url=e['request']['url'],requestHeaders=e['request'].get('headers',{})))
 cdp.on('Network.responseReceived',lambda e:req.setdefault(e['requestId'],{}).update(status=e['response']['status'],diskCache=e['response'].get('fromDiskCache',False),headers=e['response'].get('headers',{})))
 cdp.on('Network.loadingFinished',lambda e:req.setdefault(e['requestId'],{}).update(encodedBytes=e['encodedDataLength']))
 for phase,mode in phases:
  req.clear();results=[]
  for name in ASSETS:
   url=ROOT+'preview-b/releases/'+OWNER+'/'+name
   results.append(await page.evaluate('''async({url,mode})=>{const r=await fetch(url,{cache:mode});const b=await r.arrayBuffer();return {url,status:r.status,bytes:b.byteLength,cacheMode:mode};}''',{'url':url,'mode':mode}))
  await page.wait_for_timeout(300);row={'profile':label,'phase':phase,'fetches':results,'network':list(req.values())};R['phases'].append(row);print(json.dumps(row),flush=True)
  assert [x['bytes']for x in results]==[2379608,7965636] and all(x['status']==200 for x in results)
 await page.close()
async def main():
 async with async_playwright()as p:
  args=['--no-sandbox'];R['browser']='Chromium Playwright default build'
  b=await p.chromium.launch(args=args+['--log-net-log='+str((O/'ephemeral-netlog.json').resolve())]);R['browserVersion']=b.version
  ctx=await b.new_context();await exercise(ctx,'ephemeral',[('cold','default'),('warm','default'),('force-cache','force-cache')]);await ctx.close();await b.close()
  with tempfile.TemporaryDirectory()as profile:
   ctx=await p.chromium.launch_persistent_context(profile,args=args+['--log-net-log='+str((O/'persistent-netlog.json').resolve())]);await exercise(ctx,'persistent',[('cold','default'),('warm','default'),('force-cache','force-cache')]);await ctx.close()
   ctx=await p.chromium.launch_persistent_context(profile,args=args);await exercise(ctx,'persistent-restarted',[('after-restart','default')]);await ctx.close()
 R['passed']=True
try:asyncio.run(main())
finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2))

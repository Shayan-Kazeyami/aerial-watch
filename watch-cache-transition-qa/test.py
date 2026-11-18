import asyncio,json,pathlib,urllib.parse
from playwright.async_api import async_playwright
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True)
OLD='7125e9612de10991ebb13eb312268bae19ed3825bed3da8a508ed1ec33be2cd5';NEW='87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2';BASE='https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/'
R={'scope':'Actual browser network counters, not phone loading/FPS or guaranteed future CDN cache behavior','errors':[],'phases':[]}
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-sandbox']);ctx=await b.new_context(viewport={'width':430,'height':932});page=await ctx.new_page();page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)));cdp=await ctx.new_cdp_session(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{'cacheDisabled':False})
  records={};active=set()
  def request(e):
   records[e['requestId']]={'url':e['request']['url'],'type':e.get('type')};active.add(e['requestId'])
  def response(e):
   x=records.setdefault(e['requestId'],{});r=e['response'];x.update(status=r['status'],mime=r['mimeType'],diskCache=r.get('fromDiskCache',False),serviceWorker=r.get('fromServiceWorker',False),headers={k:v for k,v in r.get('headers',{}).items()if k.lower()in ['content-length','cache-control','etag','last-modified']})
  def finished(e):
   records.setdefault(e['requestId'],{})['encodedBytes']=e['encodedDataLength'];active.discard(e['requestId'])
  cdp.on('Network.requestWillBeSent',request);cdp.on('Network.responseReceived',response);cdp.on('Network.loadingFinished',finished);cdp.on('Network.loadingFailed',lambda e:active.discard(e['requestId']))
  try:
   old=(await (await ctx.request.get(BASE+OLD+'/deployment-manifest.json')).json());new=(await (await ctx.request.get(BASE+NEW+'/deployment-manifest.json')).json());a={x['path']:x for x in old['localFiles']};z={x['path']:x for x in new['localFiles']};same={n for n in a if n in z and a[n]['sha256']==z[n]['sha256']}
   for label,rid in [('cold',OLD),('warm-same-release',OLD),('new-release-identical-assets',NEW)]:
    records.clear();active.clear();await page.goto(BASE+rid+'/atelier-preview.html?quality=efficient',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=360000);await page.wait_for_load_state('networkidle',timeout=180000);await page.wait_for_timeout(1500)
    out=[dict(x)for x in records.values()];assets=[]
    for x in out:
     u=x.get('url','');path=urllib.parse.urlsplit(u).path;prefix='/aerial-watch/preview-b/releases/'+rid+'/'
     if path.startswith(prefix):
      name=path[len(prefix):]
      if name in same and any(t in name for t in ['.glb','.gltf','.bin','.ktx2','.png','.webp']):assets.append({**x,'path':name,'sha256':a[name]['sha256'],'fileBytes':a[name]['sizeBytes']})
    phase={'label':label,'release':rid,'requests':out,'unchangedLocalAssets':assets,'reportedEncodedTotal':sum(x.get('encodedBytes',0)for x in out),'unchangedAssetEncodedBytes':sum(x.get('encodedBytes',0)for x in assets),'unchangedAssetFileBytes':sum(x['fileBytes']for x in assets),'ready':True};R['phases'].append(phase);print(json.dumps({k:v for k,v in phase.items()if k not in ['requests','unchangedLocalAssets']}),flush=True)
   assert not R['errors'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())

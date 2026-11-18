import asyncio,json,pathlib,urllib.parse
from playwright.async_api import async_playwright
O=pathlib.Path('watch-cache-public-output');O.mkdir(exist_ok=True)
OLD='87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2';NEW='efb9c41b5a3531812fb64b960841c35d98cfe75799bd7bb774e852527cc029b3';ROOT='https://shayan-kazeyami.github.io/aerial-watch/preview-b/releases/'
ASSETS=['optimized-assets/premium-face__face-svg04.meshopt.glb','optimized-assets/rebuild__assembly.meshopt.glb.gz'];R={'scope':'Actual public GitHub Pages CDP encoded bytes; cache enabled; separate fresh contexts for baseline-transition vs candidate-cold; no overlays, no phone performance claim','phases':[],'errors':[]}
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for phases in [[('baseline-cold',OLD),('baseline-warm',OLD),('candidate-transition',NEW)],[('candidate-cold',NEW),('candidate-warm',NEW)]]:
    ctx=await b.new_context(viewport={'width':430,'height':932});page=await ctx.new_page();page.on('pageerror',lambda e:R['errors'].append(str(e)));cdp=await ctx.new_cdp_session(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{'cacheDisabled':False});req={}
    cdp.on('Network.requestWillBeSent',lambda e:req.update({e['requestId']:{'url':e['request']['url']}}))
    def response(e):
     r=e['response'];req.setdefault(e['requestId'],{}).update(status=r['status'],diskCache=r.get('fromDiskCache',False),headers={k:v for k,v in r.get('headers',{}).items()if k.lower()in ['content-length','content-encoding','cache-control','etag']})
    cdp.on('Network.responseReceived',response);cdp.on('Network.loadingFinished',lambda e:req.setdefault(e['requestId'],{}).update(encodedBytes=e['encodedDataLength']))
    for label,rid in phases:
     req.clear();await page.goto(ROOT+rid+'/atelier-preview.html?quality=efficient&assets=meshopt',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=360000);await page.wait_for_load_state('networkidle',timeout=180000);await page.wait_for_timeout(1500)
     selected=[dict(x)for x in req.values()if any(urllib.parse.urlsplit(x.get('url','')).path.endswith('/'+n)for n in ASSETS)]
     assert len(selected)==2 and all(x.get('status')==200 for x in selected),(label,selected)
     row={'label':label,'selectedRequests':selected,'selectedEncodedBytes':sum(x.get('encodedBytes',0)for x in selected),'totalEncodedBytes':sum(x.get('encodedBytes',0)for x in req.values())};R['phases'].append(row);print(json.dumps(row),flush=True)
     if label=='candidate-cold':await page.screenshot(path=str(O/'public-candidate.png'))
    await ctx.close()
   by={x['label']:x for x in R['phases']};assert all('/'+OLD+'/'in x['url']for x in by['candidate-transition']['selectedRequests']);assert by['candidate-cold']['selectedEncodedBytes']<=by['baseline-cold']['selectedEncodedBytes']+8192
   R['observedColdToTransitionSelectedByteDifference']=by['baseline-cold']['selectedEncodedBytes']-by['candidate-transition']['selectedEncodedBytes'];R['coldCandidateDelta']=by['candidate-cold']['selectedEncodedBytes']-by['baseline-cold']['selectedEncodedBytes'];assert not R['errors'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())

import asyncio,json,pathlib,urllib.parse
from playwright.async_api import async_playwright
from PIL import Image,ImageChops
P=pathlib.Path(__file__).parent;O=P/'output';O.mkdir(exist_ok=True)
OLD='87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2';NEW='efb9c41b5a3531812fb64b960841c35d98cfe75799bd7bb774e852527cc029b3';ROOT='http://127.0.0.1:8765/preview-b/releases/'
ASSETS=['optimized-assets/premium-face__face-svg04.meshopt.glb','optimized-assets/rebuild__assembly.meshopt.glb.gz'];RAWS=['premium-face/face-svg04.glb','rebuild/assembly.glb']
R={'scope':'Exact sealed HTTP fixture with max-age600, no source overlays; not GitHub CDN or phone timing','errors':[],'phases':[]}
CONFIG={'version':1,'view':'face','camera':{'position':[0,0,81.96682498642045],'target':[0,0,3.5],'zoom':1,'fov':32},'options':{'wireframe':False,'solidWireframe':False,'transparent':False,'transparentBackplate':False,'hideStrap':False,'openWork':True,'finishes':True,'crystals':True,'movementOnly':False,'interior':False,'powerPath':False,'quality':'efficient'},'clock':{'mechanism':0,'hands':0,'speed':1,'running':{'mechanism':False,'hands':False}},'settingSeconds':0,'explosion':0}
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  try:
   for scenario,phases in [('transition',[('base-cold',OLD),('base-warm',OLD),('candidate-transition',NEW)]),('candidate-cold',[('candidate-cold',NEW),('candidate-warm',NEW)]),('raw-fallback',[('raw-fallback',NEW)])]:
    ctx=await b.new_context(viewport={'width':430,'height':932},reduced_motion='reduce');page=await ctx.new_page();page.set_default_timeout(180000);page.on('pageerror',lambda e:R['errors'].append(str(e)));session=await ctx.new_cdp_session(page);await session.send('Network.enable');await session.send('Network.setCacheDisabled',{'cacheDisabled':False});req={}
    session.on('Network.requestWillBeSent',lambda e:req.update({e['requestId']:{'url':e['request']['url']}}))
    def response(e):
     req.setdefault(e['requestId'],{}).update(status=e['response']['status'],diskCache=e['response'].get('fromDiskCache',False))
    session.on('Network.responseReceived',response);session.on('Network.loadingFinished',lambda e:req.setdefault(e['requestId'],{}).update(encodedBytes=e['encodedDataLength']))
    if scenario=='raw-fallback':
     for name in ASSETS:await page.route('**/'+name,lambda route:route.fulfill(status=503,body='Controlled optimized transport failure'))
    for label,rid in phases:
     req.clear();await page.goto(ROOT+rid+'/atelier-preview.html?quality=efficient&assets=meshopt',wait_until='domcontentloaded');await page.locator('body[data-ready=true]').wait_for(timeout=360000);await page.wait_for_load_state('networkidle',timeout=180000);await page.wait_for_timeout(1200)
     selected=[dict(x)for x in req.values()if any(urllib.parse.urlsplit(x.get('url','')).path.endswith('/'+n)for n in ASSETS+RAWS)];row={'label':label,'release':rid,'selectedRequests':selected,'selectedEncodedBytes':sum(x.get('encodedBytes',0)for x in selected),'ready':True};R['phases'].append(row)
     if label in ['base-cold','candidate-cold','raw-fallback']:
      await page.locator('#import-config').set_input_files({'name':'fixed-view.json','mimeType':'application/json','buffer':json.dumps(CONFIG).encode()});await page.wait_for_function("assemblyInspect().mechanismElapsed===0&&assemblyInspect().view==='face'&&!assemblyInspect().animation&&!assemblyInspect().interiorAnimation")
      await page.wait_for_function("document.querySelector('#stage').dataset.cameraReady==='true'");await page.locator('.atelier-first-use').wait_for(state='hidden',timeout=15000);await page.wait_for_timeout(1500)
      row['state']=await page.evaluate('assemblyInspect()');row['resourceTotals']=await page.evaluate('assemblyResourceInspect().totals');await page.locator('#assembly-canvas').screenshot(path=str(O/(label+'.png')))
     print(json.dumps({k:v for k,v in row.items()if k not in ['state','selectedRequests','resourceTotals']}),flush=True)
    await ctx.close()
   by={x['label']:x for x in R['phases']};assert len(by['candidate-transition']['selectedRequests'])==2
   assert all('/'+OLD+'/' in x['url']for x in by['candidate-transition']['selectedRequests'])
   assert by['candidate-transition']['selectedEncodedBytes']<=by['base-warm']['selectedEncodedBytes']+4096
   assert by['candidate-transition']['selectedEncodedBytes']<by['base-cold']['selectedEncodedBytes']
   assert by['candidate-cold']['selectedEncodedBytes']<=by['base-cold']['selectedEncodedBytes']+4096
   for name in RAWS:assert any(x.get('status')==200 and urllib.parse.urlsplit(x['url']).path.endswith('/'+name)and '/'+OLD+'/'in x['url']for x in by['raw-fallback']['selectedRequests'])
   images={name:Image.open(O/(name+'.png')).convert('RGB')for name in ['base-cold','candidate-cold','raw-fallback']};R['pixels']={}
   for name in ['candidate-cold','raw-fallback']:
    assert images[name].size==images['base-cold'].size;diff=ImageChops.difference(images['base-cold'],images[name]);pix=list(diff.getdata());bad=sum(max(x)>8 for x in pix);R['pixels'][name]={'size':images[name].size,'maxChannelDifference':max(max(x)for x in pix),'pixelsOver8':bad,'totalPixels':len(pix)};assert bad/len(pix)<.0001,(name,R['pixels'][name])
   assert not R['errors'];R['passed']=True
  finally:(O/'REPORT.json').write_text(json.dumps(R,indent=2));await b.close()
asyncio.run(main())

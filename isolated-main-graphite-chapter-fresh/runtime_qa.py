import asyncio,base64,json,pathlib,hashlib,threading,http.server,functools
from playwright.async_api import async_playwright
from PIL import Image,ImageChops,ImageStat
D=pathlib.Path('isolated-main-graphite-chapter-fresh');O=D/'runtime-evidence';O.mkdir(exist_ok=True)
async def run():
 async with async_playwright() as p:
  browser=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);allresults={}
  try:
   for routekind in ['raw','meshopt']:
    page=await browser.new_page(viewport={'width':1000,'height':1000},device_scale_factor=1);page.set_default_timeout(180000);errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
    async def inject(route):
     response=await route.fetch();text=await response.text()
     if 'createOpenFrontFrame' in text and 'syncFrontDetails' in text:text+='\n'+(D/'probe.js').read_text()
     await route.fulfill(response=response,body=text)
    await page.route('**/assembly-review.js*',inject)
    await page.goto('http://127.0.0.1:8761/preview-b/assembly-review.html?quality=efficient&leather=craft14&assets='+routekind+'&finish=brushed&light=softbox',wait_until='domcontentloaded');await page.wait_for_function('window.graphiteQa?.status().ready');await page.wait_for_timeout(1200)
    data={k:json.load(open(D/(k+'.json'))) for k in ['source','candidate']};setup=await page.evaluate('(d)=>graphiteQa.setup(d)',data);results=[]
    for finish in [True,False]:
     for view in ['assembled','macro','exploded']:
      for enabled in [False,True,False]:
       r=await page.evaluate('(c)=>graphiteQa.capture(c)',{'candidate':enabled,'view':view,'finish':finish});png=base64.b64decode(r.pop('png').split(',')[1]);name=f'{routekind}-finish{int(finish)}-{view}-{len(results)}.png';(O/name).write_bytes(png);r['file']=name;r['png_sha256']=hashlib.sha256(png).hexdigest();results.append(r);print(routekind,finish,view,enabled,r['target']['position'],flush=True)
      a,b,c=results[-3:];assert a['camera']==b['camera']==c['camera'];assert a['target']['world']==b['target']['world']==c['target']['world'];assert a['png_sha256']==c['png_sha256'],'source A/B/A pixels changed';assert a['target']['position']==49152 and b['target']['position']==32736
      i1=Image.open(O/a['file']).convert('RGB');i2=Image.open(O/b['file']).convert('RGB');diff=ImageChops.difference(i1,i2);st=ImageStat.Stat(diff);a['candidate_pixel_comparison']={'mae_rgb':st.mean,'rms_rgb':st.rms,'bbox':diff.getbbox(),'warning':'Pixel difference diagnostic, not automatic visual acceptance.'};assert max(ImageStat.Stat(i1).stddev)>2,'blank frame'
    allresults[routekind]={'setup':setup,'cases':results,'pageerrors':errors,'route_asset_requests':[u for u in requests if u.endswith('.glb') or '.meshopt.' in u or u.endswith('.bin')],'cleanup':await page.evaluate('graphiteQa.finish()')};assert not errors,errors;await page.close()
   (O/'RESULTS.json').write_text(json.dumps({'pass':True,'scope':'Isolated authentic legacy/nonpremium route, runtime-generated target; raw/meshopt refer context asset routes, no packed q318 file exists. No public/defaultFPS claim.','routes':allresults},indent=2))
  except Exception as e:
   (O/'FAILURE.json').write_text(json.dumps({'error':repr(e),'partial_routes':allresults},indent=2))
   try:await page.screenshot(path=str(O/'failure.png'))
   except Exception:pass
   raise
  finally:await browser.close()
if __name__=='__main__':
 server=http.server.ThreadingHTTPServer(('127.0.0.1',8761),functools.partial(http.server.SimpleHTTPRequestHandler,directory='.'));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(run())
 finally:server.shutdown()

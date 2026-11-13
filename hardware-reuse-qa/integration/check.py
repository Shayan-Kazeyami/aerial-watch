import asyncio,json,pathlib,base64,hashlib,traceback
from playwright.async_api import async_playwright
R=pathlib.Path('hardware-reuse-qa/integration');O=R/'evidence';O.mkdir(exist_ok=True);RID=(R/'release-id.txt').read_text().strip();URL=f'http://127.0.0.1:8877/preview-b/releases/{RID}/atelier-preview.html?quality=efficient&normalStream=1&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&tickBatch=1';rows=json.loads(pathlib.Path('hardware-retopo-qa/reuse-audit.json').read_text())if pathlib.Path('hardware-retopo-qa/reuse-audit.json').exists()else json.loads((R/'reuse-audit.json').read_text());report={'fixtureRandom':'seeded LCG 434893964, both contexts','sourceMain':'f3c23832f6cb8af3463248355dd7f69ab5e7b6bf','sourceRelease':RID,'errors':[],'runs':{}};probe=(R/'probe.js').read_text()
async def main():
 async with async_playwright()as p:
  b=await p.chromium.launch(args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);
  for mode in ['baseline','candidate']:
   URL=f'http://127.0.0.1:8877/preview-b/releases/{"09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29" if mode=="baseline" else RID}/atelier-preview.html?quality=efficient&normalStream=1&face=svg04&leather=craft14&finish=brushed&crystal=clear&cap=satin&assets=meshopt&light=softbox&antialias=smaa&tickBatch=1'
   ctx=await b.new_context(viewport={'width':1000,'height':1000},device_scale_factor=1);page=await ctx.new_page();page.set_default_timeout(240000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
   async def route(r):
    response=await r.fetch();body=await response.body();report.setdefault('baselineModuleSHA256',hashlib.sha256(body).hexdigest());assert report['baselineModuleSHA256']=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee';await r.fulfill(response=response,body=body+probe.encode())
   async def mechanism(r):
    response=await r.fetch();body=await response.body();digest=hashlib.sha256(body).hexdigest();report[mode+'BatchModuleSHA256']=digest
    assert digest==('af6343619941debdb5bfc973f5132fc544595903fd4532f9d2aaa7252da21c67'if mode=='baseline'else'b933242c54bd84316ca1a2c4a3f7f4310fc00deef782149e049bc348f854d6ce')
    await r.fulfill(response=response,body=body)
   await page.add_init_script('(()=>{let seed=434893964;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296}})()');await page.route('**/assembly-review.js*',route)
   await page.route('**/assembly-mechanism-batch.js*',mechanism)
   try:
    await page.goto(URL,wait_until='domcontentloaded');await page.wait_for_function('window.__reuseQa?.ready&&window.assemblyInspect?.().presentation.interactive',timeout=300000);print(mode,'ready',flush=True)
    await page.evaluate('__reuseQa.show({view:"movement",pose:0})');rr={'sourceHashBefore':await page.evaluate('__reuseQa.hashSources()'),'poses':await page.evaluate('__reuseQa.validatePoses()'),'states':[]};report['runs'][mode]=rr
    cases=[dict(name='assembled',view='watch'),dict(name='exploded',view='watch',explode=1),dict(name='movement',view='movement'),dict(name='movement-clay',view='movement',finish=False),dict(name='movement-wire',view='movement',display='wire'),dict(name='movement-transparent',view='movement',display='transparent')]
    family={}
    for row in rows:
     if row['partNumber']not in family or row['maxNormalVectorError']>family[row['partNumber']]['maxNormalVectorError']:family[row['partNumber']]=row
    cases += [dict(name=f'wholepart-{r["sourceIndex"]}',sid=r['sourceIndex'],view='movement',zoom=1)for r in family.values()]
    cases += [dict(name=f'part-{r["sourceIndex"]}',sid=r['sourceIndex'],view='movement',zoom=12)for r in rows]
    for c in cases:
     name=c.pop('name');s=await page.evaluate('(p)=>__reuseQa.show(p)',c);im=s.pop('image');(O/f'{mode}-{name}.png').write_bytes(base64.b64decode(im.split(',')[1]));s['case']=name;s['hits']=await page.evaluate('__reuseQa.sourceRayHits()');rr['states'].append(s);(O/'report.json').write_text(json.dumps(report,indent=2));print(mode,name,flush=True)
    rr['sourceHashAfter']=await page.evaluate('__reuseQa.hashSources()');assert rr['sourceHashBefore']==rr['sourceHashAfter'];assert rr['states'][0]['batch']['supported'];
    # Exceptional materials and geometry versions must fall back to exact source meshes.
    await page.evaluate('__reuseQa.show({view:"movement"})');await page.evaluate('__reuseQa.selectSource(71)');rr['selected']=await page.evaluate('__reuseQa.renderCurrent()');await page.evaluate('__reuseQa.mutateSource(71)');s=await page.evaluate('__reuseQa.show({view:"movement"})');s.pop('image');rr['versionFallback']=s;rr['versionFallbackTrace']=await page.evaluate('__reuseQa.renderCurrent()');await page.evaluate('__reuseQa.mutateSource(54)');rr['canonicalVersionFallback']=await page.evaluate('__reuseQa.renderCurrent()');await page.evaluate('__reuseQa.replaceNormal(40)');rr['attributeReplacementFallback']=await page.evaluate('__reuseQa.renderCurrent()');await page.evaluate('__reuseQa.replaceNormal(39)');rr['canonicalAttributeReplacementFallback']=await page.evaluate('__reuseQa.renderCurrent()')
   except Exception as e:report['failure']=repr(e);report['traceback']=traceback.format_exc();raise
   finally:(O/'report.json').write_text(json.dumps(report,indent=2));await ctx.close()
  await b.close()
 # Source object transforms, geometry and picking remain exact despite different render-only buffers.
 a=report['runs']['baseline'];c=report['runs']['candidate'];assert a['poses']==c['poses'];assert a['sourceHashBefore']==c['sourceHashBefore'];
 for x,y in zip(a['states'],c['states']):
  assert x['case']==y['case'];assert [{k:v for k,v in o.items()if k not in ['positionVersion','normalVersion']}for o in x['source']]==[{k:v for k,v in o.items()if k not in ['positionVersion','normalVersion']}for o in y['source']],x['case'];assert x['camera']==y['camera'],x['case'];assert len(x['hits'])==len(y['hits']);
  for hx,hy in zip(x['hits'],y['hits']):
   assert hx['sourceIndex']==hy['sourceIndex']and hx['faceIndex']==hy['faceIndex'];assert abs(hx['distance']-hy['distance'])<1e-12;assert max(abs(u-v)for u,v in zip(hx['point'],hy['point']))<1e-12
 assert c['states'][0]['batch']['reusedEntries']==57;assert c['states'][0]['batch']['rejectedReuse']==0
 assert 71 in c['selected']['renderedOriginalSourceIds'];assert 71 in c['versionFallbackTrace']['renderedOriginalSourceIds'];assert all(sid in c['canonicalVersionFallback']['renderedOriginalSourceIds']for sid in [54,55,71,72,73]);
 assert 40 in c['attributeReplacementFallback']['renderedOriginalSourceIds'];assert all(sid in c['canonicalAttributeReplacementFallback']['renderedOriginalSourceIds']for sid in [39,40,78,90,91,106,107,131,132,162,164,165]);
 report['passed']=True;(O/'report.json').write_text(json.dumps(report,indent=2))
asyncio.run(main())

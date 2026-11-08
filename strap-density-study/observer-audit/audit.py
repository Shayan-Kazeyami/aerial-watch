import asyncio,json,pathlib,threading,http.server,functools,os
from playwright.async_api import async_playwright
ROOT=os.environ.get('AUDIT_ROOT','/tmp/aerial-current-backup-smoke'); OUT=pathlib.Path('strap-density-study/observer-audit')
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=ROOT));threading.Thread(target=server.serve_forever,daemon=True).start();URL=os.environ.get('AUDIT_URL',f'http://127.0.0.1:{server.server_port}/')
INIT=r'''(()=>{window.__observerAudit=[];let original=MutationObserver.prototype.observe;MutationObserver.prototype.observe=function(target,options){let e={url:location.href,target:target?.nodeName,id:target?.id,valid:target instanceof Node,stack:new Error().stack};try{let r=original.call(this,target,options);window.__observerAudit.push(e);return r}catch(err){e.error=String(err);window.__observerAudit.push(e);console.error('OBSERVE_FAILED',JSON.stringify(e));throw err}}})()'''
async def main():
 result={'root':ROOT,'cases':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE') or None,headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640});await c.add_init_script(INIT);q=await c.new_page();q.on('pageerror',lambda e:result['errors'].append(str(e)));q.on('console',lambda m:result['errors'].append(m.text)if 'OBSERVE_FAILED' in m.text else None)
  async def sample(name,wait=True):
   if 'atelier-preview.html' not in q.url:
    for _ in range(300):
     if any('atelier-preview.html' in f.url for f in q.frames):break
     await q.wait_for_timeout(100)
   frame=next((f for f in q.frames if 'atelier-preview.html' in f.url),q.main_frame)
   if wait:
    try:await frame.wait_for_function('window.assemblyInspect && !assemblyInspect().loading',timeout=120000)
    except Exception as e:result['cases'].append({'case':name,'readyError':str(e)})
   await q.wait_for_timeout(500)
   frames=[]
   for f in q.frames:
    try:frames.append(await f.evaluate('({url:location.href,calls:window.__observerAudit||[],loading:window.assemblyInspect?.().loading,failed:window.assemblyInspect?.().failed,interactive:window.assemblyInspect?.().presentation?.interactive})'))
    except:pass
   result['cases'].append({'case':name,'frames':frames});(OUT/'result.json').write_text(json.dumps(result,indent=2));return frame
  await q.goto(URL,wait_until='domcontentloaded',timeout=60000);f=await sample('iframe-initial');direct=f.url
  assert 'atelier-preview.html' in direct, 'No viewer frame; diagnostic cannot proceed'
  result['controls']=await f.evaluate("""()=>{let clicked=[];for(const e of document.querySelectorAll('button[data-mode]')){e.click();clicked.push(e.dataset.mode)}return clicked}""")
  await sample('iframe-controls',False)
  for name,action in [('iframe-reload',lambda:q.reload(wait_until='domcontentloaded',timeout=60000))]:
   try:await action();await sample(name)
   except Exception as e:result['cases'].append({'case':name,'navigationError':str(e)})
  # Independent page preserves direct comparison even if reload stalls.
  await q.close();q=await c.new_page();q.on('pageerror',lambda e:result['errors'].append(str(e)))
  await q.goto(direct,wait_until='domcontentloaded',timeout=60000);await sample('direct')
  try:
   await q.goto('about:blank',wait_until='domcontentloaded',timeout=60000);await q.go_back(wait_until='domcontentloaded',timeout=60000);await sample('direct-back')
  except Exception as e:result['cases'].append({'case':'direct-back','navigationError':str(e)})
  try:await q.reload(wait_until='domcontentloaded',timeout=60000);await sample('direct-reload')
  except Exception as e:result['cases'].append({'case':'direct-reload','navigationError':str(e)})
  await b.close()
 (OUT/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({'errors':result['errors'],'cases':[(x['case'],sum(len(f['calls'])for f in x.get('frames',[])))for x in result['cases']]}))
asyncio.run(main())

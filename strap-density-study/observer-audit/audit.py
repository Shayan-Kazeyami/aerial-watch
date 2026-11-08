import asyncio,json,pathlib,os
from playwright.async_api import async_playwright
OUT=pathlib.Path('strap-density-study/observer-audit');OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('AUDIT_URL','https://shayan-kazeyami.github.io/aerial-watch/')
INIT=r'''(()=>{window.__observerAudit=[];let original=MutationObserver.prototype.observe;MutationObserver.prototype.observe=function(target,options){let e={url:location.href,target:target?.nodeName,id:target?.id,valid:target instanceof Node,stack:new Error().stack};try{let r=original.call(this,target,options);window.__observerAudit.push(e);return r}catch(err){e.error=String(err);window.__observerAudit.push(e);throw err}}})()'''
READY='window.assemblyInspect && !assemblyInspect().loading && !assemblyInspect().failed && assemblyInspect().presentation.interactive && document.getElementById("loading").hidden'
async def main():
 result={'url':URL,'cases':[],'errors':[],'completed':False}
 def save():(OUT/'result.json').write_text(json.dumps(result,indent=2))
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE')or None,headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);c=await b.new_context(viewport={'width':800,'height':640});await c.add_init_script(INIT)
  q=await c.new_page();q.on('pageerror',lambda e:result['errors'].append({'message':str(e),'stack':getattr(e,'stack',None)}))
  async def sample(name):
   entry={'case':name,'ready':False};result['cases'].append(entry)
   f=None
   try:
    for _ in range(300):
     f=next((f for f in q.frames if 'atelier-preview.html' in f.url),None)
     if f:break
     await q.wait_for_timeout(100)
    assert f, 'No live viewer frame'
    await f.wait_for_function(READY,timeout=300000)
    entry['ready']=True
   except Exception as e:entry['readinessError']=str(e)
   entry['frames']=[]
   for fr in q.frames:
    try:entry['frames'].append(await fr.evaluate('({url:location.href,calls:window.__observerAudit||[],inspect:window.assemblyInspect?.(),loadingHidden:document.getElementById("loading")?.hidden})'))
    except Exception as e:entry['frames'].append({'url':fr.url,'snapshotError':str(e)})
   save()
   assert entry['ready'],entry.get('readinessError')
   return f
  async def tabs(f,name):
   values=await f.locator('button[data-mode]').evaluate_all('(es)=>es.map(e=>e.dataset.mode)')
   for value in values:
    await f.locator(f'button[data-mode="{value}"]').evaluate('(e)=>e.click()');await q.wait_for_timeout(100)
   result.setdefault('tabs',{})[name]=values;await sample(name)
  async def remount(name):
   await q.evaluate('''()=>{const old=document.getElementById('watch-viewer'),src=old.src;old.remove();let f=document.createElement('iframe');f.id='watch-viewer';f.style='width:100vw;height:100vh;border:0';f.src=src;document.body.append(f)}''');await sample(name)
  try:
   await q.goto(URL,wait_until='domcontentloaded',timeout=60000);f=await sample('native-interactive');direct=f.url
   await tabs(f,'native-tabs');await remount('native-remount-1');await remount('native-remount-2')
   wrapper=URL+'__observer-wrapper.html'
   await q.route(wrapper,lambda route:route.fulfill(content_type='text/html',body='<!doctype html><meta charset="utf-8"><title>Private same-origin wrapper QA</title><style>html,body{margin:0}iframe{width:100vw;height:100vh;border:0}</style><iframe id="watch-viewer" src='+json.dumps(direct)+'></iframe>'))
   await q.goto(wrapper,wait_until='domcontentloaded',timeout=60000);f=await sample('wrapper-interactive');await tabs(f,'wrapper-tabs');await remount('wrapper-remount-1');await remount('wrapper-remount-2')
   result['completed']=True
  except Exception as e:result['failure']=str(e)
  finally:save();await b.close()
 print(json.dumps({'completed':result['completed'],'cases':[(x['case'],x['ready'])for x in result['cases']],'errors':result['errors'],'failure':result.get('failure')}))
 assert result['completed'] and not result['errors'],'Diagnostic incomplete or page error; inspect exact report'
asyncio.run(main())

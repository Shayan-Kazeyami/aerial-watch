"""Explicitly invoked QA adapter; never auto-runs a watch or starts export.
Use only an isolated QA browser context. No release files or remote refs changed.
"""
import asyncio,json,pathlib,time
from urllib.parse import urlparse
from instrument import instrument,IDENTITY,RID
P=pathlib.Path(__file__).parent
async def install(page,origin):
 if origin not in ['http://127.0.0.1:8766','https://shayan-kazeyami.github.io']:raise ValueError('Unapproved QA origin')
 # Pages host includes /aerial-watch; local checkout does not.
 root=origin+('/aerial-watch' if origin.startswith('https:') else '')+'/preview-b/releases/'+RID+'/'
 source_url=root+IDENTITY['source']['path'];ledger={'identity':IDENTITY,'overlay':None,'nativeDownloads':[],'pageErrors':[],'snapshots':[]}
 script=(P/'trace.mjs').read_text().replace('export function createExportTrace','function createExportTrace')
 await page.add_init_script(script+'\nglobalThis.__watchExportTestTrace=createExportTrace();')
 async def route(request):
  if request.request.url!=source_url:raise ValueError('Unexpected module URL')
  response=await request.fetch();text=await response.text();patched=instrument(text,RID)
  await request.fulfill(response=response,body=patched,headers={**{k:v for k,v in response.headers.items() if k.lower() not in ['content-length','content-encoding']},'cache-control':'no-store'})
  ledger['overlay']={'url':source_url,'sourceSHA256':IDENTITY['source']['sha256'],'notReleaseBytes':True}
 await page.route(source_url,route)
 page.on('download',lambda d:ledger['nativeDownloads'].append({'atMonotonic':time.monotonic(),'suggestedFilename':d.suggested_filename,'url':d.url}))
 page.on('pageerror',lambda e:ledger['pageErrors'].append(str(e)))
 async def snapshot(label):
  if not page.url.startswith(root):raise ValueError('Not exact held release')
  # This can wait behind a synchronous GPU/readback block. Host timestamps
  # distinguish an unresponsive sample; they cannot interrupt native work.
  start=time.monotonic()
  task=asyncio.create_task(page.evaluate('''()=>globalThis.__watchExportTestTrace.snapshot({viewerStatus:document.querySelector('#viewer-status')?.textContent,dialogOpen:document.querySelector('.aerial-video-dialog')?.open,progressValue:document.querySelector('.aerial-video-status progress')?.value,progressMax:document.querySelector('.aerial-video-status progress')?.max,recordDisabled:document.querySelector('#record-scene')?.disabled})'''))
  try:result=await asyncio.wait_for(task,timeout=5)
  except asyncio.TimeoutError:result={'unresponsiveSample':True,'cause':'unknown main-thread/native work; do not infer GPU phase'}
  row={'label':label,'hostStart':start,'hostEnd':time.monotonic(),'result':result};ledger['snapshots'].append(row);return row
 return ledger,snapshot

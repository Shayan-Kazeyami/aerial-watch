import urllib.request,json,hashlib,time,concurrent.futures,pathlib
BASE='https://shayan-kazeyami.github.io/aerial-watch/'
RID='43e516fa6ed3a4be7e8b308bc35c1955dc811b710042e38cdbaeaf868b7c8932'
release=BASE+'preview-b/releases/'+RID+'/'
def get(url):
 with urllib.request.urlopen(url,timeout=120) as r:return r.read()
for attempt in range(30):
 try:
  home=get(BASE+'?hybrid='+str(time.time())).decode();assert 'watch-home-hybrid-v7.js' in home
  script=get(BASE+'watch-home-hybrid-v7.js').decode();assert RID in script
  m=json.loads(get(release+'deployment-manifest.json'));assert m['releaseId']==RID;break
 except Exception:
  if attempt==29:raise
  time.sleep(20)
def check(f):
 url=(BASE+'preview-b/releases/'+f['ownerReleaseId']+'/' if 'ownerReleaseId' in f else release)+f['path'];b=get(url);assert len(b)==f['sizeBytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],url
 return {'path':f['path'],'bytes':len(b),'owner':f.get('ownerReleaseId',RID)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:result=list(pool.map(check,m['localFiles']+m['references']))
pathlib.Path('integration-output').mkdir(exist_ok=True);pathlib.Path('integration-output/live-identities.json').write_text(json.dumps({'releaseId':RID,'verifiedFiles':len(result),'verifiedBytes':sum(x['bytes'] for x in result),'files':result},indent=2));print('Verified live homepage, release and',len(result),'asset identities')

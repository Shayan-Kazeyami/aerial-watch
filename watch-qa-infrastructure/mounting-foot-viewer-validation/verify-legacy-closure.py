from pathlib import Path
import json,hashlib,re,urllib.parse,threading,http.server,urllib.request
Q=Path(__file__).resolve().parent;root=Q/'qa-legacy-viewer';rid='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6';S=root/'preview-b/releases'/rid;m=json.loads((S/'deployment-manifest.json').read_text());modified={'assembly-review.html','assembly-review.js'};verified=[]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();urls=[];missing=[];graph={}
try:
 for f in m['localFiles']+m['references']:
  owner=f.get('ownerReleaseId',rid);path=f'preview-b/releases/{owner}/{f["path"]}';p=root/path;b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
  if owner!=rid or f['path']not in modified:assert h==f['sha256']and len(b)==f['sizeBytes']
  with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/'+path)as response:assert hashlib.sha256(response.read()).hexdigest()==h
  verified.append({'url':'/'+path,'sha256':h,'bytes':len(b),'qaModified':owner==rid and f['path']in modified})
 # Static ES imports, including bare Three aliases; no arbitrary URL requests.
 vendor='../'+next(f['ownerReleaseId']for f in m['references']if f['path']=='vendor/three.module.js')+'/vendor/'
 for f in m['localFiles']+m['references']:
  if not f['path'].endswith(('.js','.mjs')):continue
  owner=f.get('ownerReleaseId',rid);p=root/'preview-b/releases'/owner/f['path'];text=p.read_text()
  imports=re.findall(r'''(?:from\s*|import\s*\(\s*|import\s*)['"]([^'"]+)['"]''',text)
  edges=[]
  for spec in imports:
   if spec=='three':target=S/vendor/'three.module.js'
   elif spec.startswith('three/addons/'):target=S/vendor/spec.removeprefix('three/addons/')
   elif spec.startswith('./vendor/') and owner==rid:target=S/vendor/spec.removeprefix('./vendor/')
   elif spec.startswith('.'):target=p.parent/urllib.parse.urlsplit(spec).path
   else:continue
   edges.append(str(target.resolve()))
   if not target.resolve().is_relative_to(root.resolve())or not target.is_file():missing.append({'source':str(p.relative_to(root)),'specifier':spec})
  graph[str(p.resolve())]=edges
 for css in ['assembly-review.css','assembly-quality.css']:assert(S/css).is_file()
 # These dependencies are not on the baseline manifest, so hash and serve them explicitly.
 for name in ['qa-substitution.mjs','qa-foot-350.json','qa-foot-110.json','qa-foot-250.json']:
  p=S/name;b=p.read_bytes();urls.append({'path':name,'sha256':hashlib.sha256(b).hexdigest()})
finally:server.shutdown()
# Classify unresolved edges by actual static rendering entry reachability.
seen=set();pending=[str((S/'assembly-review.js').resolve())]
while pending:
 current=pending.pop()
 if current in seen:continue
 seen.add(current);pending.extend(graph.get(current,[]))
unused=[x for x in missing if str((root/x['source']).resolve())not in seen]
missing=[x for x in missing if x not in unused]
r={'staticReachableModules':len(seen),'unreachableModuleUnresolved':unused,'closureHTTPVerified':len(verified),'files':verified,'qaAdditionalFiles':urls,'unresolvedStaticImports':missing,'passed':not missing,'limits':'Static ES literals and manifest HTTP bytes; no browser/dynamic URL execution or optional informational HTML links acceptance'};(Q/'LEGACY_URL_CLOSURE.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items()if k!='files'});assert not missing

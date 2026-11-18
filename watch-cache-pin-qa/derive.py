"""Build only camera reset split exact changed seal files in a scratch directory (no Git/ref writes)."""
import json,hashlib,sys,subprocess,tempfile
from pathlib import Path
baseline,candidate,out,releases=map(Path,sys.argv[1:5])
helper=Path(__file__).with_name("identity-gate.mjs")
module=(candidate/"assembly-asset-routing.js").resolve()
owners=json.loads(subprocess.check_output(["node","--input-type=module","-e",f"import {{CANONICAL_ASSET_OWNERS}} from {json.dumps(module.as_uri())}; console.log(JSON.stringify(CANONICAL_ASSET_OWNERS))"],text=True))
sha=lambda data:hashlib.sha256(data).hexdigest()
compact=lambda data:json.dumps(data,separators=(',',':')).encode('utf-8')
m=json.loads((baseline/'deployment-manifest.json').read_text());release_base=m['releaseId']
assert release_base=='87a8607a738ba192c68f266db3f241e148f48f34216e7976c73cc062adb1f3e2'
assert sha(compact({k:m[k] for k in ('schemaVersion','localFiles','references')}))==release_base
files={x['path']:x for x in m['localFiles']}
change={}
def put(name,data):
 change[name]=data
 files[name]={'path':name,'sizeBytes':len(data),'sha256':sha(data)}
for x in ('assembly-asset-routing.js',):
 put(x,(candidate/x).read_bytes())
rev=json.loads((baseline/'quality-study/viewer-revision.json').read_text())
rev['files']=[{'path':r['path'],'bytes':r['sizeBytes'],'sha256':r['sha256']} for r in sorted(files.values(),key=lambda r:r['path']) if '/' not in r['path'] and Path(r['path']).suffix in ['.html','.css','.js']]
rev['digest']=sha(compact(rev['files']))
put('quality-study/viewer-revision.json',(json.dumps(rev,indent=2)+'\n').encode())
put('quality-study/viewer-revision.js',b'export default '+compact(rev)+b';\n')
m['localFiles']=sorted(files.values(),key=lambda r:r['path'])
for name,owner in owners.items():
 assert not any(x['path']==name for x in m['references'])
 m['references'].append({**files[name],'ownerReleaseId':owner})
m['references'].sort(key=lambda r:r['path'])
with tempfile.TemporaryDirectory() as temp:
 manifest_path=Path(temp)/'prospective-manifest.json';manifest_path.write_text(json.dumps(m))
 subprocess.run(['node',str(helper),str(manifest_path),str(module),str(candidate),str(baseline),str(releases)],check=True,stdout=sys.stderr)
rid=sha(compact({k:m[k] for k in ('schemaVersion','localFiles','references')}))
m['releaseId']=rid;change['deployment-manifest.json']=(json.dumps(m,indent=2)+'\n').encode()
r=json.loads((baseline/'release-receipt.json').read_text())
r['releaseId']=rid;r['totalBytes']=sum(x['sizeBytes'] for x in m['localFiles'])
r['fileCount']=len(m['localFiles']);r['referenceCount']=len(m['references']);r['referencedBytes']=sum(x['sizeBytes'] for x in m['references'])
change['release-receipt.json']=(json.dumps(r,indent=2)+'\n').encode()
d=out/rid
for name,data in change.items():
 p=d/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(data)
summary={'derived_release_id':rid,'base_release_id':release_base,'viewer_digest':rev['digest'],'shared_reference_count':len(m['references']),'bound_local_count':len(m['localFiles']),'exact_delta_SHA256':{n:sha(b) for n,b in change.items()},'derived_only_nonproduction':True}
print(json.dumps(summary,indent=2))

from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent;repo=root.parent;binding=json.loads((root/'BINDING.json').read_text());rid=binding['releaseId'];r=repo/'preview-b/releases'/rid
sha=lambda b:hashlib.sha256(b).hexdigest()
for name,h in binding['diagnostic_files'].items():assert sha((root/name).read_bytes())==h,name
for name,h in binding['repository_helpers'].items():assert sha((repo/name).read_bytes())==h,name
m=json.loads((r/'deployment-manifest.json').read_text());assert sha(json.dumps({k:m[k]for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode())==rid
for f in m['localFiles']+m['references']:
 p=(r.parent/f['ownerReleaseId'] if 'ownerReleaseId'in f else r)/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes'] and sha(b)==f['sha256'],str(p)
print('297 exact release bindings and diagnostic source hashes verified; no publication')

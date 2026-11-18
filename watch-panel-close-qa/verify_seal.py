from pathlib import Path
import hashlib,json
r=Path('preview-b/releases/7125e9612de10991ebb13eb312268bae19ed3825bed3da8a508ed1ec33be2cd5');m=json.loads((r/'deployment-manifest.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(json.dumps({k:m[k]for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode())==m['releaseId']
for f in m['localFiles']:
 b=(r/f['path']).read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],f['path']
for f in m['references']:
 b=(r.parent/f['ownerReleaseId']/f['path']).read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],f['path']
rev=json.loads((r/'quality-study/viewer-revision.json').read_text());assert sha(json.dumps(rev['files'],separators=(',',':')).encode())==rev['digest']
print('Verified exact seal +297 runtime bindings +viewer revision digest')

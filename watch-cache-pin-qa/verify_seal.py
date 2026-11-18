from pathlib import Path
import hashlib,json
r=Path('preview-b/releases/efb9c41b5a3531812fb64b960841c35d98cfe75799bd7bb774e852527cc029b3');m=json.loads((r/'deployment-manifest.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(json.dumps({k:m[k]for k in ['schemaVersion','localFiles','references']},separators=(',',':')).encode())==m['releaseId']
for f in m['localFiles']:
 b=(r/f['path']).read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],f['path']
for f in m['references']:
 b=(r.parent/f['ownerReleaseId']/f['path']).read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],f['path']
rev=json.loads((r/'quality-study/viewer-revision.json').read_text());assert sha(json.dumps(rev['files'],separators=(',',':')).encode())==rev['digest']
print('Verified exact seal +301 runtime bindings +viewer revision digest')

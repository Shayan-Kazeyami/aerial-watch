import json,hashlib,shutil
from pathlib import Path
P=Path('qa-component-search');BASE=Path('preview-b/releases/e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6');OUT=P/'runtime'
m=json.loads((BASE/'deployment-manifest.json').read_text())
assert m['releaseId']=='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
OUT.mkdir(exist_ok=True)
for f in m['localFiles']+m['references']:
 src=BASE.parent/f['ownerReleaseId']/f['path'] if 'ownerReleaseId' in f else BASE/f['path']
 b=src.read_bytes();assert hashlib.sha256(b).hexdigest()==f['sha256'],str(src)
 dest=OUT/f['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 if 'ownerReleaseId' in f:
  sibling=P/f['ownerReleaseId']/f['path'];sibling.parent.mkdir(parents=True,exist_ok=True);sibling.write_bytes(b)
source=(OUT/'assembly-review.js').read_bytes();assert hashlib.sha256(source).hexdigest()=='91fcb25fbcc71e7e259dc603ba019d8c626e8506399dc14cf3c12075cc0fa4ee'

patches=[
 ('atelier-preview.js','<p id="atelier-count" class="tool-note"></p>','<p id="atelier-count" class="tool-note" role="status" aria-atomic="true"></p>'),
 ('assembly-review.js',' â€” no matches; clear the search or change the group',' — no matches; clear the search or change the group')
]
proof={'baseMain':'b84a51ec91b715aa70408e8bff6e988e29d93edb','release':m['releaseId'],'runtimeSourceModified':True,'productionSourceModified':False,'patches':[]}
for filename,before,after in patches:
 path=OUT/filename;b=path.read_bytes();text=b.decode('utf-8');assert text.count(before)==1
 candidate=text.replace(before,after);path.write_text(candidate,encoding='utf-8')
 proof['patches'].append({'file':filename,'originalSHA256':hashlib.sha256(b).hexdigest(),'candidateSHA256':hashlib.sha256(candidate.encode()).hexdigest(),'before':before,'after':after,'count':1})
(P/'source-proof.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False))

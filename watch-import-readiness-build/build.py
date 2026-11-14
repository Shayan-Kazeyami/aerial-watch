"""Build-only additive proposal atop pinned privacy/encoding feature; no source/ref/deploy writes."""
from pathlib import Path
import os,json,hashlib,shutil
Q=Path(__file__).resolve().parent;OLD='0f760c648dffb367f5542730a3ec99537e0c8a3bc554e805431d66422f5a0275';B=Path(os.environ.get('IMPORT_READINESS_BASE','watch-save-feedback-build/staging/preview-b/releases/'+OLD));sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(B/'deployment-manifest.json').read_bytes();assert sha(raw)=='3aefdb08df1d76c3d5868819f57dcce2943c4dcc246130059213b945ece2415f';m=json.loads(raw);can={k:m[k] for k in ['schemaVersion','localFiles','references']};assert sha(json.dumps(can,separators=(',',':')).encode())==OLD
for f in m['localFiles']+m['references']:
 src=B.parent/f.get('ownerReleaseId',OLD)/f['path'];data=src.read_bytes();assert len(data)==f['sizeBytes'] and sha(data)==f['sha256'],str(src)
assert sha((B/'assembly-component-labels.js').read_bytes())=='1c811a0b185bdbd8e13f99c6aa44d088015b94e28b1fd10c0c99f6d0303f8fdb'
assert sha((B/'atelier-error-details.js').read_bytes())=='e28bdd29a032d5dad5d2a501b08c02536a386b22abb04fc7bc2796b9a843de58'
assert sha((B/'assembly-review.js').read_bytes())=='84e8d605a1d125911eb90b7f774d29b71aa2ce0c6299a9c3b9fa84b5fae7f5b8'
assert sha((B/'assembly-story.js').read_bytes())=='c501fdfa2071d9c760cc2001bdaaac7b53299241eca138fbc6eb60551ff3708c'
patch=json.loads((Q/'patch.json').read_text());source=(B/'assembly-review.js').read_text();assert source.count(patch['old'])==1;candidate=source.replace(patch['old'],patch['new'],1).encode();assert sha(candidate)=='f02f88014eedd44769f5dce54c784b07d391aae6523da1d7bd2582cdfaa8f23f'
changes={'assembly-review.js':candidate};files={f['path']:dict(f) for f in m['localFiles']}
def put(n,b):changes[n]=b;files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)}
put('assembly-review.js',candidate)
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']} for f in sorted(files.values(),key=lambda f:f['path']) if '/' not in f['path'] and Path(f['path']).suffix in ['.html','.js','.css']]
v={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
put('quality-study/viewer-revision.json',(json.dumps(v,indent=2)+'\n').encode());put('quality-study/viewer-revision.js',('export default '+json.dumps(v,separators=(',',':'))+';\n').encode())
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};rid=sha(json.dumps(can,separators=(',',':')).encode());manifest={**can,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']};receipt={'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','fileCount':len(files),'totalBytes':sum(f['sizeBytes'] for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes'] for f in m['references'])}
root=Q/'staging';root.mkdir(exist_ok=False);stage=root/'preview-b/releases'/rid
for f in can['localFiles']+can['references']:
 owner=f.get('ownerReleaseId',rid);data=(B.parent/f.get('ownerReleaseId',OLD)/f['path']).read_bytes() if f['path'] not in changes or 'ownerReleaseId' in f else changes[f['path']];dst=root/'preview-b/releases'/owner/f['path'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);assert sha(data)==f['sha256'] and len(data)==f['sizeBytes']
for n,j in [('deployment-manifest.json',manifest),('release-receipt.json',receipt)]: (stage/n).write_text(json.dumps(j,indent=2)+'\n')
# Preserve pinned feature bootstrap/UI. ONLY immutable target changes in isolated staging.
entry=B.parents[2]
entryPins={'index.html': 'ec5afa0fb870b9e3a0a76a60bd8f7ff270481b36aaaa300e646c0fc6bfdb4098', 'watch-home-coordinated-successor.js': 'dcc667c23cca1c0d3111965feacb8ae6efa1c2842d8e115dce2c36c647f0fd69', 'watch-home-loading-v4.css': '0db4e30c1e54f824152441bf5f566664df84ebf61d8996b8a78f9c4e271c5ee1'}
for name in ['index.html','watch-home-coordinated-successor.js','watch-home-loading-v4.css']:
 data=(entry/name).read_bytes();assert sha(data)==entryPins[name];new=data.replace(OLD.encode(),rid.encode()) if name!='watch-home-loading-v4.css' else data
 if name=='watch-home-coordinated-successor.js':assert data.count(OLD.encode())==1
 assert new.replace(rid.encode(),OLD.encode())==data
 (root/name).write_bytes(new)

(Q/'release-id.txt').write_text(rid)
(Q/'build-report.json').write_text(json.dumps({'baseCommit':'2d985556edc6103807f38d9ed394a4a577d6c6a4','releaseId':rid,'closureFiles':len(can['localFiles'])+len(can['references']),'changedPaths':sorted(changes),'scope':'isolated one-token import readiness guard text fix; no browser/deployment approval'},indent=2)+'\n')
print(rid)

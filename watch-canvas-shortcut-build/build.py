"""Build-only additive proposal atop pinned privacy/encoding feature; no source/ref/deploy writes."""
from pathlib import Path
import os,json,hashlib,shutil
Q=Path(__file__).resolve().parent;OLD='48438e79481a6258e2ae563e943d25a516c2e5a515f15a6335bdb08197ca752d';B=Path(os.environ.get('SHORTCUT_BASE','watch-utf8-text-build/staging/preview-b/releases/'+OLD));sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(B/'deployment-manifest.json').read_bytes();assert sha(raw)=='7dbdd8e5503aab89f8f5c9f685c1fcdd8a58b19b9afe976495a178c5399e6d23';m=json.loads(raw);can={k:m[k] for k in ['schemaVersion','localFiles','references']};assert sha(json.dumps(can,separators=(',',':')).encode())==OLD
for f in m['localFiles']+m['references']:
 src=B.parent/f.get('ownerReleaseId',OLD)/f['path'];data=src.read_bytes();assert len(data)==f['sizeBytes'] and sha(data)==f['sha256'],str(src)
assert sha((B/'assembly-component-labels.js').read_bytes())=='1c811a0b185bdbd8e13f99c6aa44d088015b94e28b1fd10c0c99f6d0303f8fdb'
assert sha((B/'atelier-error-details.js').read_bytes())=='e28bdd29a032d5dad5d2a501b08c02536a386b22abb04fc7bc2796b9a843de58'
assert sha((B/'assembly-review.js').read_bytes())=='fcdc431418f99868358b1e9d3570d6209ad1dcafc53241ba12bd77aa5f83fcc2'
original=(B/'assembly-review.js').read_bytes();text=original.decode('utf-8')
base=(Q/'BASE_HANDLER.txt').read_text();replacement=(Q/'CANDIDATE_HANDLER.txt').read_text();assert sha(base.encode())=='4477b23df2024ea838e9d70eac1cb9640c3e741cdf7c03677bf55294ec74abd8';assert sha(replacement.encode())=='b681b05b7915cca77ed825187d747f8740fefc48057eeced3caed6d9c47790f1';assert text.count(base)==1;text=text.replace(base,replacement,1)
candidate=text.encode('utf-8')
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
entryPins={'index.html': '9bcdd366a5e1a0f1fb0a48f0838244cef234a4b92364d0821c3f4d6251f2630f', 'watch-home-coordinated-successor.js': 'c570bb6af19a14b1d71ab206cfc222b8a84641537c68205d370fd828a0a1bd37', 'watch-home-loading-v4.css': '0db4e30c1e54f824152441bf5f566664df84ebf61d8996b8a78f9c4e271c5ee1'}
for name in ['index.html','watch-home-coordinated-successor.js','watch-home-loading-v4.css']:
 data=(entry/name).read_bytes();assert sha(data)==entryPins[name];new=data.replace(OLD.encode(),rid.encode()) if name!='watch-home-loading-v4.css' else data
 if name=='watch-home-coordinated-successor.js':assert data.count(OLD.encode())==1
 assert new.replace(rid.encode(),OLD.encode())==data
 (root/name).write_bytes(new)

(Q/'release-id.txt').write_text(rid)
(Q/'build-report.json').write_text(json.dumps({'baseCommit':'1e1cd2a1478334a89207a19d19d932637584d97e','releaseId':rid,'closureFiles':len(can['localFiles'])+len(can['references']),'changedPaths':sorted(changes),'scope':'isolated canvas browser-shortcut guard; no browser/deployment approval'},indent=2)+'\n')
print(rid)

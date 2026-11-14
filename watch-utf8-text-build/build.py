"""Build-only additive proposal atop pinned privacy/encoding feature; no source/ref/deploy writes."""
from pathlib import Path
import os,json,hashlib,shutil
Q=Path(__file__).resolve().parent;OLD='94ad3066d775ac9b39dd95a4c52a70388d86df29e327e556edfeee0328624817';B=Path(os.environ.get('UTF8_BASE','watch-explorer-label-build/staging/preview-b/releases/'+OLD));sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(B/'deployment-manifest.json').read_bytes();assert sha(raw)=='51d305215aa039f434a704660f41022996d1e942dc2323736591a488ebd9c3c3';m=json.loads(raw);can={k:m[k] for k in ['schemaVersion','localFiles','references']};assert sha(json.dumps(can,separators=(',',':')).encode())==OLD
for f in m['localFiles']+m['references']:
 src=B.parent/f.get('ownerReleaseId',OLD)/f['path'];data=src.read_bytes();assert len(data)==f['sizeBytes'] and sha(data)==f['sha256'],str(src)
assert sha((B/'assembly-component-labels.js').read_bytes())=='1c811a0b185bdbd8e13f99c6aa44d088015b94e28b1fd10c0c99f6d0303f8fdb'
assert sha((B/'atelier-error-details.js').read_bytes())=='e28bdd29a032d5dad5d2a501b08c02536a386b22abb04fc7bc2796b9a843de58'
assert sha((B/'assembly-review.js').read_bytes())=='18acb2b6eea2a0a26b80dd173fc48a8bece76e6f2a66238ef84e3c57e0c79ae7'
original=(B/'assembly-review.js').read_bytes();text=original.decode('utf-8')
for bad,good,count in [('Â·','·',10),('â€¦','…',2),('â†’','→',6),('Ã—','×',1)]:
 assert text.count(bad)==count,(bad,text.count(bad));text=text.replace(bad,good)
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
entryPins={'index.html': '4f22851e028a39c6737ecd85cead3de88911fb75408506144c4b4d993d7e6879', 'watch-home-coordinated-successor.js': '11f912b843f625d259b53e309adc63362676b6e6606cd5e22f5c739c2554a70e', 'watch-home-loading-v4.css': '0db4e30c1e54f824152441bf5f566664df84ebf61d8996b8a78f9c4e271c5ee1'}
for name in ['index.html','watch-home-coordinated-successor.js','watch-home-loading-v4.css']:
 data=(entry/name).read_bytes();assert sha(data)==entryPins[name];new=data.replace(OLD.encode(),rid.encode()) if name!='watch-home-loading-v4.css' else data
 if name=='watch-home-coordinated-successor.js':assert data.count(OLD.encode())==1
 assert new.replace(rid.encode(),OLD.encode())==data
 (root/name).write_bytes(new)

(Q/'release-id.txt').write_text(rid)
(Q/'build-report.json').write_text(json.dumps({'baseCommit':'482ee78bf8ef29a29ac07f9605aaee8681dbf731','releaseId':rid,'closureFiles':len(can['localFiles'])+len(can['references']),'changedPaths':sorted(changes),'scope':'isolated nineteen remaining UTF8 UI token repairs; no browser/deployment approval'},indent=2)+'\n')
print(rid)

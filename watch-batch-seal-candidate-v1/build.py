"""Reproducible candidate seal. Never updates an existing release or public loader."""
import pathlib,json,hashlib,shutil,tempfile
REPO=pathlib.Path(__file__).resolve().parent.parent
OUT=pathlib.Path(__file__).resolve().parent
BASE='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6'
releases=REPO/'preview-b/releases';base=releases/BASE
sha=lambda b:hashlib.sha256(b).hexdigest()
compact=lambda o:json.dumps(o,separators=(',',':')).encode()
m=json.loads((base/'deployment-manifest.json').read_text())
assert sha(compact({k:m[k] for k in ['schemaVersion','localFiles','references']}))==BASE
for f in m['localFiles']+m['references']:
 p=(releases/f['ownerReleaseId'] if 'ownerReleaseId'in f else base)/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes'] and sha(b)==f['sha256'],str(p)
stage=pathlib.Path(tempfile.mkdtemp(prefix='watch-seal-build-'))
try:
 shutil.copytree(base,stage,dirs_exist_ok=True)
 candidate=REPO/'watch-batch-integration-review-v1/assembly-mechanism-batch.js'
 assert sha(candidate.read_bytes())=='02868f9ab9556b10e3bd4f55b0adcd5f48cbe3c1d7328e58f2446cc1833efab1'
 shutil.copy2(candidate,stage/'assembly-mechanism-batch.js')
 def info(name):
  b=(stage/name).read_bytes();return{'path':name,'sizeBytes':len(b),'sha256':sha(b)}
 files={f['path']:info(f['path']) for f in m['localFiles']}
 rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']} for f in sorted(files.values(),key=lambda x:x['path']) if '/' not in f['path'] and pathlib.Path(f['path']).suffix in ['.js','.css','.html']]
 revision=json.loads((base/'quality-study/viewer-revision.json').read_text());revision['files']=rf;revision['digest']=sha(compact(rf))
 for name,data in [('quality-study/viewer-revision.json',json.dumps(revision,indent=2)+'\n'),('quality-study/viewer-revision.js','export default '+compact(revision).decode()+';\n')]:
  (stage/name).write_text(data);files[name]=info(name)
 canonical={'schemaVersion':m['schemaVersion'],'localFiles':sorted(files.values(),key=lambda x:x['path']),'references':m['references']}
 rid=sha(compact(canonical));manifest={**canonical,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']}
 (stage/'deployment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 receipt=json.loads((base/'release-receipt.json').read_text());receipt.update(releaseId=rid,totalBytes=sum(f['sizeBytes'] for f in canonical['localFiles']))
 (stage/'release-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 dest=releases/rid
 if dest.exists():
  assert {str(p.relative_to(stage)):sha(p.read_bytes()) for p in stage.rglob('*') if p.is_file()}=={str(p.relative_to(dest)):sha(p.read_bytes()) for p in dest.rglob('*') if p.is_file()},'Existing immutable candidate differs'
 else:shutil.copytree(stage,dest)
 (OUT/'release-id.txt').write_text(rid+'\n')
 (OUT/'BUILD.json').write_text(json.dumps({'base':BASE,'releaseId':rid,'viewerDigest':revision['digest'],'candidate_module_sha256':sha(candidate.read_bytes()),'public_loader_changed':False,'physical_gpu_verified':False},indent=2))
 print(rid)
finally:shutil.rmtree(stage)

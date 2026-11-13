import pathlib,hashlib,json,shutil
BASE_ID='6b2118bcfb83c3cac2631fff21e487cba67971454dd787eb0da62f2c7caccf68'
root=pathlib.Path('preview-b/releases');base=root/BASE_ID;stage=root/'case-fillet-qa-stage'
shutil.copytree(base,stage,dirs_exist_ok=True)
CHANGED=['assembly-hybrid-case-data.js','hybrid-case-assets/hybrid-innerseat-density-r02.meshopt.glb.gz']
for name in CHANGED:
 (stage/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(pathlib.Path('case-fillet-qa')/name,stage/name)
m=json.loads((base/'deployment-manifest.json').read_text());files={f['path']:dict(f) for f in m['localFiles']}
def sha(b):return hashlib.sha256(b).hexdigest()
def info(p):
 b=(stage/p).read_bytes();return {'path':p,'sizeBytes':len(b),'sha256':sha(b)}
for name in CHANGED:files[name]=info(name)
revision_files=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']} for f in sorted(files.values(),key=lambda f:f['path']) if '/' not in f['path'] and pathlib.Path(f['path']).suffix in ['.html','.js','.css']]
rev={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(revision_files,separators=(',',':')).encode()),'files':revision_files}
(stage/'quality-study/viewer-revision.json').write_text(json.dumps(rev,indent=2)+'\n')
(stage/'quality-study/viewer-revision.js').write_text('export default '+json.dumps(rev,separators=(',',':'))+';\n')
for name in ['quality-study/viewer-revision.json','quality-study/viewer-revision.js']:files[name]=info(name)
canonical={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']}
rid=sha(json.dumps(canonical,separators=(',',':')).encode())
(stage/'deployment-manifest.json').write_text(json.dumps({**canonical,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']},indent=2)+'\n')
(stage/'release-receipt.json').write_text(json.dumps({'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','canonicalization':'SHA-256 of UTF-8 JSON.stringify({schemaVersion:2,localFiles,references}); each array sorted lexicographically by path; field order as shown in manifest','fileCount':len(files),'totalBytes':sum(f['sizeBytes'] for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes'] for f in m['references'])},indent=2)+'\n')
dest=root/rid
if dest.exists():shutil.rmtree(dest)
stage.rename(dest)
for f in canonical['localFiles']+canonical['references']:
 p=(root/f['ownerReleaseId'] if 'ownerReleaseId'in f else dest)/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes'] and sha(b)==f['sha256'],str(p)
out=pathlib.Path('mobile-output');out.mkdir(exist_ok=True);(out/'build.json').write_text(json.dumps({'releaseId':rid,'revision':rev['digest'],'releasePath':str(dest)}));print('BUILD',rid,rev['digest'],flush=True)
for f in CHANGED+['quality-study/viewer-revision.json','quality-study/viewer-revision.js','deployment-manifest.json','release-receipt.json']:
 p=out/'release'/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dest/f,p)


pathlib.Path('case-fillet-qa/url.txt').write_text('http://127.0.0.1:8765/'+str(dest)+'/atelier-preview.html')

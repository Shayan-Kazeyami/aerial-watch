import pathlib,json,hashlib,shutil
R=pathlib.Path('marked-mesh-qa');root=pathlib.Path('preview-b/releases');rid=(R/'release-id.txt').read_text();base=root/rid;stage=root/'marked-mesh-stage';shutil.copytree(base,stage,dirs_exist_ok=True)
changes=['assembly-hybrid-case-data.js','hybrid-case-assets/hybrid-lug-density-r03.meshopt.glb.gz','assembly-leather-authoring-identity.js','leather-assets/r14/leather.gltf','leather-assets/r14/geometry.bin']
for n in changes:(stage/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'changes'/n,stage/n)
m=json.loads((base/'deployment-manifest.json').read_text());files={f['path']:dict(f)for f in m['localFiles']};sha=lambda b:hashlib.sha256(b).hexdigest()
def info(n):b=(stage/n).read_bytes();return {'path':n,'sizeBytes':len(b),'sha256':sha(b)}
for n in changes:files[n]=info(n)
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']}for f in sorted(files.values(),key=lambda f:f['path'])if '/'not in f['path']and pathlib.Path(f['path']).suffix in ['.html','.js','.css']];rev={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
for n,bb in [('quality-study/viewer-revision.json',json.dumps(rev,indent=2)+'\n'),('quality-study/viewer-revision.js','export default '+json.dumps(rev,separators=(',',':'))+';\n')]: (stage/n).write_text(bb);files[n]=info(n)
can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};outid=sha(json.dumps(can,separators=(',',':')).encode());(stage/'deployment-manifest.json').write_text(json.dumps({**can,'releaseId':outid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']},indent=2)+'\n');(stage/'release-receipt.json').write_text(json.dumps({'schemaVersion':2,'releaseId':outid,'algorithm':'SHA-256','canonicalization':'SHA-256 of UTF-8 JSON.stringify({schemaVersion:2,localFiles,references}); each array sorted lexicographically by path; field order as shown in manifest','fileCount':len(files),'totalBytes':sum(f['sizeBytes']for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes']for f in m['references'])},indent=2)+'\n');dest=root/outid
if dest.exists():shutil.rmtree(dest)
stage.rename(dest)
for f in can['localFiles']+can['references']:
 b=((root/f['ownerReleaseId']if 'ownerReleaseId'in f else dest)/f['path']).read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],f['path']
(R/'build.json').write_text(json.dumps({'releaseId':outid,'baseline':rid}));(R/'url.txt').write_text('http://127.0.0.1:8765/'+str(dest)+'/atelier-preview.html');print(outid)
O=pathlib.Path('marked-output/release');O.mkdir(parents=True,exist_ok=True)
for n in changes+['deployment-manifest.json','release-receipt.json','quality-study/viewer-revision.json','quality-study/viewer-revision.js']:(O/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dest/n,O/n)

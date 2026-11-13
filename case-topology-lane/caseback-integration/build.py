import pathlib,json,hashlib,shutil,os,re
Q=pathlib.Path('case-topology-lane/caseback-integration');BASE=pathlib.Path(os.environ.get('WATCH_BASE','strap-combined-qa/resume/recovery-09e3e0ae/preview-b/releases/09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29'));m=json.load(open(BASE/'deployment-manifest.json'));assert m['releaseId']=='09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29';sha=lambda b:hashlib.sha256(b).hexdigest()
for f in m['localFiles']+m['references']:
 p=BASE.parent/f['ownerReleaseId']/f['path']if'ownerReleaseId'in f else BASE/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes']and sha(b)==f['sha256'],f['path']
out=Q/'release';out.mkdir(exist_ok=True);files={f['path']:dict(f)for f in m['localFiles']};changed=[]
def put(n,b):
 p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);files[n]={'path':n,'sizeBytes':len(b),'sha256':sha(b)};changed.append(n)
for n in ['rebuild/assembly.glb','optimized-assets/rebuild__assembly.meshopt.glb.gz']:put(n,(Q/'work'/n).read_bytes())
e=json.load(open(Q/'encoding-report.json'));r=json.load(open(Q/'bake-report.json'));s=(BASE/'assembly-optimized-loading.js').read_bytes().decode();s,n=re.subn(r'const GZIP_DECODED_BYTES=\d+;',f"const GZIP_DECODED_BYTES={e['meshoptBytes']};",s);assert n==1;put('assembly-optimized-loading.js',s.encode())
s=(BASE/'assembly-leather-authoring-identity.js').read_bytes().decode();i=json.loads(s[s.index('Object.freeze(')+14:s.rfind(')')]);assert i['hardware']['expectedSha256']==r['sourceSHA256'];i['hardware'].update(expectedSha256=r['candidateSHA256'],expectedBytes=r['candidateBytes'],verificationScope='Canonical assembly after caseback meridian reconstruction; all leather, keeper, springbar and other source buffers byte-preserved');put('assembly-leather-authoring-identity.js',('export const AUTHORED_LEATHER_IDENTITY=Object.freeze('+json.dumps(i,indent=2)+');\n').encode())
# Every other first-party file stays byte-identical, including routing, finish, cap guards and all interaction/benchmark code.
protected=[n for n in files if n not in changed]
for n in protected:assert files[n]==next(f for f in m['localFiles']if f['path']==n)
rf=[{'path':f['path'],'bytes':f['sizeBytes'],'sha256':f['sha256']}for f in sorted(files.values(),key=lambda x:x['path'])if'/'not in f['path']and pathlib.Path(f['path']).suffix in ['.html','.js','.css']];v={'schemaVersion':1,'algorithm':'SHA-256','scope':'Build-transformed local first-party viewer JS, CSS and HTML; shared asset/vendor identities are in schema-2 deployment manifest.','canonicalization':'SHA-256 of UTF-8 JSON.stringify(files), ordered lexicographically by path.','digest':sha(json.dumps(rf,separators=(',',':')).encode()),'files':rf}
put('quality-study/viewer-revision.json',(json.dumps(v,indent=2)+'\n').encode());put('quality-study/viewer-revision.js',('export default '+json.dumps(v,separators=(',',':'))+';\n').encode());can={'schemaVersion':2,'localFiles':sorted(files.values(),key=lambda f:f['path']),'references':m['references']};rid=sha(json.dumps(can,separators=(',',':')).encode());(out/'deployment-manifest.json').write_text(json.dumps({**can,'releaseId':rid,'referenceLayout':m['referenceLayout'],'assetClosure':m['assetClosure']},indent=2)+'\n');(out/'release-receipt.json').write_text(json.dumps({'schemaVersion':2,'releaseId':rid,'algorithm':'SHA-256','fileCount':len(files),'totalBytes':sum(f['sizeBytes']for f in files.values()),'referenceCount':len(m['references']),'referencedBytes':sum(f['sizeBytes']for f in m['references'])},indent=2)+'\n')
# Stage complete immutable candidate while preserving shared owner paths.
stage=BASE.parent/rid
for n in [f['path']for f in can['localFiles']]+['deployment-manifest.json','release-receipt.json']:
 p=out/n if(out/n).exists()else BASE/n;d=stage/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
for f in can['localFiles']+can['references']:
 p=BASE.parent/f['ownerReleaseId']/f['path']if'ownerReleaseId'in f else stage/f['path'];b=p.read_bytes();assert sha(b)==f['sha256']and len(b)==f['sizeBytes']
sourcegz=(BASE/'optimized-assets/rebuild__assembly.meshopt.glb.gz').stat().st_size
report={'baseMain':'f3c23832f6cb8af3463248355dd7f69ab5e7b6bf','baseRelease':m['releaseId'],'releaseId':rid,'changedFiles':changed+['deployment-manifest.json','release-receipt.json'],'protectedFilesByteExact':len(protected)-2,'sourceClosureFiles':len(m['localFiles'])+len(m['references']),'encoding':e,'sourceGzipBytes':sourcegz,'gzipBytesSaved':sourcegz-e['gzipBytes'],'mainNotPromoted':True};(Q/'release-id.txt').write_text(rid);(Q/'build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
# Existing crown and layer regressions run against this candidate, not historical source.
for folder in ['crown-unified-qa','layer-focus-qa']:
 pathlib.Path(folder,'release-id.txt').write_text(rid)
for n in ['assembly-review.js','assembly-crown-hotspot.js']:shutil.copyfile(stage/n,pathlib.Path('crown-unified-qa')/n)

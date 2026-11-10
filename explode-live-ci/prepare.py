import pathlib,json,hashlib,shutil,subprocess
RID='36f0aca93a5c9e1cf01e0237aabcc0c71ee96fbfc2cc64394b74b35c32cf75e8'
root=pathlib.Path('preview-b/releases')/RID
m=json.loads((root/'deployment-manifest.json').read_text())
canonical={k:m[k] for k in ['schemaVersion','localFiles','references']}
assert hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()==RID
unit=pathlib.Path('explode-live-unit');unit.mkdir(exist_ok=True)
for f in m['localFiles']+m['references']:
 p=(root.parent/f['ownerReleaseId'] if 'ownerReleaseId' in f else root)/f['path'];b=p.read_bytes()
 assert len(b)==f['sizeBytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],str(p)
 if '/' not in f['path'] or f['path'].startswith('vendor/'):
  dest=unit/f['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in root.glob('*.js'):subprocess.run(['node','--check',str(p)],check=True)
assert not list(root.glob('qa-*'))
shutil.copytree('explode-live-ci/tests',unit/'tests',dirs_exist_ok=True)
print('VERIFIED_IMMUTABLE_RELEASE',RID,len(m['localFiles']),len(m['references']),flush=True)

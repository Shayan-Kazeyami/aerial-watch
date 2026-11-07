import pathlib,hashlib,tarfile,json,subprocess
root=pathlib.Path('live');release='949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8';old='cb5b426319babe1f263ddec44156a56eac0bf8b3020c979cc5f3c22884524695';prefix='preview-b/releases/'+release+'/';expected='c17bcb4246a8fcfab87143a029d4da342b0fac71'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==expected
archive=pathlib.Path('release.tar.gz');assert sha(archive)=='657c9356385123af0f159c249bbc3e44b3ee4425a39b2c6b1379ea862baa786f'
assert not (root/prefix).exists()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  p=pathlib.PurePosixPath(m.name);assert m.name.rstrip('/')==prefix.rstrip('/') or m.name.startswith(prefix)
  assert not p.is_absolute() and '..' not in p.parts and (m.isdir() or m.isfile())
 t.extractall(root,filter='data')
manifest=json.loads((root/prefix/'deployment-manifest.json').read_text())
assert sha(root/prefix/'deployment-manifest.json')=='73755191a9995cdfe9f74ed06e0944a351d6888e66f57a7187e2579260228b5c'
assert len(manifest['localFiles'])==152 and len(manifest['references'])==120
for f in manifest['localFiles']:
 p=root/prefix/f['path'];assert p.stat().st_size==f['sizeBytes'] and sha(p)==f['sha256']
for f in manifest['references']:
 p=root/'preview-b/releases'/f['ownerReleaseId']/f['path'];assert p.stat().st_size==f['sizeBytes'] and sha(p)==f['sha256']
files={str(p.relative_to(root/prefix)) for p in (root/prefix).rglob('*') if p.is_file()}
assert files=={f['path'] for f in manifest['localFiles']}|{'deployment-manifest.json','release-receipt.json'}
bootstrap='watch-home-949a4881-studio.js';previous='watch-home-cb5b4263-studio.js'
oldjs=(root/previous).read_text();assert oldjs.count(old)==1
assert not(root/bootstrap).exists();(root/bootstrap).write_text(oldjs.replace(old,release))
p=root/'index.html';s=p.read_text();assert s.count(previous)==1 and s.count(old)==1
p.write_text(s.replace(previous,bootstrap).replace(old,release))
assert (root/previous).read_text()==oldjs
subprocess.run(['git','-C',str(root),'add','--',prefix,bootstrap,'index.html'],check=True)
changed=subprocess.check_output(['git','-C',str(root),'diff','--cached','--name-only'],text=True).splitlines()
assert len(changed)==156 and all(p.startswith(prefix) or p in [bootstrap,'index.html'] for p in changed)
# Physical site bytes, excluding repository bookkeeping; same hosting inventory definition.
tracked=subprocess.check_output(['git','-C',str(root),'ls-files','-z'],text=True).split('\0')
physical=sum((root/p).stat().st_size for p in tracked if p)
assert physical<2**30
print(json.dumps({'release':release,'filesChanged':len(changed),'siteBytes':physical,'headroom':2**30-physical,'expectedParent':expected}))


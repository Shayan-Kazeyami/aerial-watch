import pathlib,hashlib,tarfile,json,subprocess
root=pathlib.Path('live');release='cb5b426319babe1f263ddec44156a56eac0bf8b3020c979cc5f3c22884524695';old='9c055e4777a79c7987dd6cd5ccabf9f189121fd6c64e2f54853aa694827add06';prefix='preview-b/releases/'+release+'/';expected='2a8748aeabc70e75f10f63fa644bcad9f315f26f'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==expected
archive=pathlib.Path('release.tar.gz');assert sha(archive)=='f067267e350e40dcf98758a37d5538b0c044cec9cc3f42b32b7533482a27226f'
assert not (root/prefix).exists()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  p=pathlib.PurePosixPath(m.name);assert m.name.rstrip('/')==prefix.rstrip('/') or m.name.startswith(prefix)
  assert not p.is_absolute() and '..' not in p.parts and (m.isdir() or m.isfile())
 t.extractall(root,filter='data')
manifest=json.loads((root/prefix/'deployment-manifest.json').read_text())
assert sha(root/prefix/'deployment-manifest.json')=='0a825d03218fd0035dc0bec91225e1e477218e3e60a00d0a12b1d3a622828a61'
assert len(manifest['localFiles'])==151 and len(manifest['references'])==120
for f in manifest['localFiles']:
 p=root/prefix/f['path'];assert p.stat().st_size==f['sizeBytes'] and sha(p)==f['sha256']
for f in manifest['references']:
 p=root/'preview-b/releases'/f['ownerReleaseId']/f['path'];assert p.stat().st_size==f['sizeBytes'] and sha(p)==f['sha256']
files={str(p.relative_to(root/prefix)) for p in (root/prefix).rglob('*') if p.is_file()}
assert files=={f['path'] for f in manifest['localFiles']}|{'deployment-manifest.json','release-receipt.json'}
bootstrap='watch-home-cb5b4263-studio.js';previous='watch-home-9c055e47-studio.js'
oldjs=(root/previous).read_text();assert oldjs.count(old)==1
assert not(root/bootstrap).exists();(root/bootstrap).write_text(oldjs.replace(old,release))
p=root/'index.html';s=p.read_text();assert s.count(previous)==1 and s.count(old)==1
p.write_text(s.replace(previous,bootstrap).replace(old,release))
assert (root/previous).read_text()==oldjs
subprocess.run(['git','-C',str(root),'add','--',prefix,bootstrap,'index.html'],check=True)
changed=subprocess.check_output(['git','-C',str(root),'diff','--cached','--name-only'],text=True).splitlines()
assert len(changed)==155 and all(p.startswith(prefix) or p in [bootstrap,'index.html'] for p in changed)
# Physical site bytes, excluding repository bookkeeping; same hosting inventory definition.
tracked=subprocess.check_output(['git','-C',str(root),'ls-files','-z'],text=True).split('\0')
physical=sum((root/p).stat().st_size for p in tracked if p)
assert physical<2**30
print(json.dumps({'release':release,'filesChanged':len(changed),'siteBytes':physical,'headroom':2**30-physical,'expectedParent':expected}))

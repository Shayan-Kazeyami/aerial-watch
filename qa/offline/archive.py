import pathlib,hashlib,json,tarfile,sys,shutil
root=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
manifest=root/'deployment-manifest.json'
assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='2dfc71fed1007acb84ad13c4e7ccd25e7531713cc4f6fa82b21500e7862ddd8f'
files=list(root.rglob('*'));assert all(not p.is_symlink() for p in files)
# Preserve entire restored source, including small generated receipts: no source exclusions.
archive=out/'aerial-watch-r18-final-source.tar.gz'
with tarfile.open(archive,'w:gz')as t:
 t.add(root,arcname='source')
 t.add(pathlib.Path(__file__).with_name('RESTORE.md'),arcname='RESTORE.md')
 t.add(pathlib.Path(__file__).with_name('verify-composed.py'),arcname='verify-composed.py')
 t.add(pathlib.Path(__file__).with_name('guards.json'),arcname='guards.json')
restore=out.parent/'offline-roundtrip';restore.mkdir()
with tarfile.open(archive)as t:t.extractall(restore,filter='data')
original={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files if p.is_file()}
actual={str(p.relative_to(restore/'source')):hashlib.sha256(p.read_bytes()).hexdigest()for p in (restore/'source').rglob('*')if p.is_file()}
assert original==actual
for e in json.loads(manifest.read_text())['files']:
 p=restore/'source'/e['path'];assert p.stat().st_size==e['sizeBytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
receipt={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'sourceCommit':'41a5cbba744c6211429dd0d2a4ad1d8893e56e6c','sourceDigest':'1d16cf3e5e653360db93e3ab23921161d741f9f372639fe59bb0929787002e4c','manifestSha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'roundtripFileCount':len(actual),'excludedSourceFiles':[],'roundtripAllFilesExact':True}
(out/'backup-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))

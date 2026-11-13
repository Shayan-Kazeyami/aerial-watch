from pathlib import Path
import json,hashlib,shutil,zipfile
rid='58afec995ed68ca32bbed7e3c135a47d668445bcfc4fbc655820e3164c6a224c'
root=Path('preview-b/releases');m=json.loads((root/rid/'deployment-manifest.json').read_text());out=Path('backup-package');out.mkdir(exist_ok=True)
files={}
def add(p):
 p=Path(p);b=p.read_bytes();files[str(p)]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};dest=out/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
for f in m['localFiles']+m['references']:
 p=root/f.get('ownerReleaseId',rid)/f['path'];b=p.read_bytes();assert len(b)==f['sizeBytes'] and hashlib.sha256(b).hexdigest()==f['sha256'];add(p)
for p in [root/rid/'deployment-manifest.json',root/rid/'release-receipt.json','index.html','watch-home-case-58afec99.js','watch-home-loading-v3.css','ATTRIBUTION.md','README.md']:add(p)
manifest={'sourceCommit':'54a5579b7ba6a47eb7bfe9f676a2d323a46bc724','releaseId':rid,'scope':'Standalone deployed viewer source and declared local dependency closure, not the full development history or native modeling source.','files':files}
(out/'BACKUP-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'VERIFY.py').write_text("from pathlib import Path\nimport json,hashlib\np=Path(__file__).parent\nm=json.loads((p/'BACKUP-MANIFEST.json').read_text())\nfor n,f in m['files'].items():\n b=(p/n).read_bytes();assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],n\nprint('Verified',len(m['files']),'files for',m['sourceCommit'])\n")
(out/'RESTORE.md').write_text('''# Aerial Watch standalone runtime backup\n\nRelease 54a5579b, 13 November 2026. Includes viewer HTML/JS/CSS, current release and all manifest-declared local assets/vendor dependencies, keeping original relative layout. It is standalone, not an incremental overlay. It does not include all historical releases or Blender/native modeling source.\n\n1. Extract to an empty folder.\n2. Run `python VERIFY.py` (Windows: `py VERIFY.py`).\n3. Run `python -m http.server 8000` (Windows: `py -m http.server 8000`).\n4. Open http://localhost:8000/ . Do not open index.html through file://.\n\nRestoration verification compares every archived runtime file against exact source bytes. The production release passed assembled, exploded, close-up, slider, reassembly and movement QA. Actual phone/WebGPU hardware performance remains unverified.\n''')
z=Path('Aerial-Watch-Standalone-54a5579b.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,6) as a:
 for p in out.rglob('*'):
  if p.is_file():a.write(p,p.relative_to(out))
restore=Path('backup-restore-test');restore.mkdir(exist_ok=True)
with zipfile.ZipFile(z) as a:assert a.testzip() is None;a.extractall(restore)
for n,f in files.items():
 b=(restore/n).read_bytes();assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],n
print(json.dumps({'files':len(files),'runtimeBytes':sum(f['bytes'] for f in files.values()),'zipBytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'restore':'all files match source'}))

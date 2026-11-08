import os,sys,subprocess,hashlib,json
from pathlib import Path
source=Path(sys.argv[1]).resolve();dest=Path('strap-density-study').resolve();A=dest/'end-shell-audit';O=dest/'shell/full-v4';A.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256((source/'geometry.bin').read_bytes()).hexdigest()=='ae62f1a0e32f2bbe0e2591dff0a0664d676102e12b8f71db8e5adc1912f309c4'
os.environ.update(STRAP_SOURCE_ASSET_DIR=str(source),STRAP_STUDY_DIR=str(dest),OPENBLAS_NUM_THREADS='1')
subprocess.run([sys.executable,'strap-qa/audit.py'],check=True)
for name in ['cuts.py','loops.py','split_paths.py','export_interfaces.py','paint_boundary.py']:subprocess.run([sys.executable,str(A/name)],check=True)
for name in ['build_full.py','stitch_full.py','attributes_full.py']:subprocess.run([sys.executable,str(dest/'shell'/name)],check=True)
os.environ['STRAP_STUDY_DIR']=str(O)
for name in ['export_round_cap.py','compact_export.py']:subprocess.run([sys.executable,'strap-qa/'+name],check=True)
print(json.load(open(O/'compact-export.json')))

import os,sys,subprocess,hashlib,json
from pathlib import Path
source=Path(sys.argv[1]).resolve();dest=Path(sys.argv[2]).resolve();dest.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256((source/'geometry.bin').read_bytes()).hexdigest()=='ae62f1a0e32f2bbe0e2591dff0a0664d676102e12b8f71db8e5adc1912f309c4','Requires exact R18 source geometry'
os.environ.update(STRAP_SOURCE_ASSET_DIR=str(source),STRAP_STUDY_DIR=str(dest),OPENBLAS_NUM_THREADS='1')
for name in ['audit.py', 'build_round_cap.py', 'propagate_edges.py', 'localize_normals.py save', 'normal_crease.py', 'normal_cylinder.py', 'localize_normals.py restore', 'export_round_cap.py', 'compact_export.py', 'check_round_cap.py']:subprocess.run([sys.executable,str(Path(__file__).parent/name.split()[0]),*name.split()[1:]],check=True)
print(json.dumps(json.load(open(dest/'compact-export.json'))))

import os,sys,subprocess,hashlib
from pathlib import Path
S=Path(sys.argv[1]).resolve();D=Path('strap-density-study');D.mkdir(exist_ok=True)
assert hashlib.sha256((S/'geometry.bin').read_bytes()).hexdigest()=='ae62f1a0e32f2bbe0e2591dff0a0664d676102e12b8f71db8e5adc1912f309c4'
os.environ.update(STRAP_SOURCE_ASSET_DIR=str(S),STRAP_STUDY_DIR=str(D.resolve()),OPENBLAS_NUM_THREADS='1')
subprocess.run([sys.executable,'strap-qa/audit.py'],check=True)
subprocess.run(['bash',str(D/'neck-v13-qa/upper-left/regenerate.sh')],check=True)
base=D/'neck-v13-qa/upper-left'
subprocess.run([sys.executable,'strap-density-study/shell/refine_uv.py'],cwd=base,check=True)
subprocess.run([sys.executable,'strap-qa/export-wide.py'],check=True)

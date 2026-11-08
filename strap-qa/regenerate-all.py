import os,sys,subprocess
from pathlib import Path
source=Path(sys.argv[1]).resolve()
subprocess.run([sys.executable,'strap-qa/regenerate-shell.py',str(source)],check=True)
D=Path('strap-density-study')
for end in ['upper-left','lower-right','lower-left']:
 subprocess.run(['bash',str(D/'other-ends-v9'/end/'regenerate.sh')],check=True)
subprocess.run([sys.executable,str(D/'combined-ordered-v9/prepare_upper_right.py')],check=True)
subprocess.run([sys.executable,str(D/'combined-ordered-v9/assemble.py')],check=True)
os.environ.update(STRAP_SOURCE_ASSET_DIR=str(source),STRAP_STUDY_DIR=str((D/'combined-ordered-v9').resolve()))
for s in ['export_all.py','compact_export.py']:subprocess.run([sys.executable,'strap-qa/'+s],check=True)

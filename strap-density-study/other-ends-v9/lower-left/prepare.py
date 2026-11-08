from pathlib import Path
import numpy as np,json
SOURCE=Path(__file__).resolve().parents[2]
D=Path('strap-density-study');(D/'end-shell-audit').mkdir(parents=True,exist_ok=True);(D/'shell/ordered-v9').mkdir(parents=True,exist_ok=True)
for ci,si in enumerate([0,2,1]):
 z=np.load(SOURCE/f'input-2-{si}.npz');d={k:z[k].copy() for k in z.files};d['positions']*=np.array([-1,1,-1]);d['normals']*=np.array([-1,1,-1]);np.savez_compressed(D/f'input-0-{ci}.npz',**d)
Path('setup.json').write_text(json.dumps({'actualMesh':2,'actualPrimitiveForCanonical':[0,2,1],'coordinateScale':[-1,1,-1],'windingReversed':False,'source':str(SOURCE)},indent=2))

from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];D=Path('strap-density-study');(D/'end-shell-audit').mkdir(parents=True,exist_ok=True);(D/'shell/ordered-v9').mkdir(parents=True,exist_ok=True)
for i,j in enumerate([0,2,1]):
 z=np.load(R/f'input-2-{j}.npz');p=z['positions'].copy();n=z['normals'].copy();p[:,2]*=-1;n[:,2]*=-1;np.savez_compressed(D/f'input-0-{i}.npz',positions=p,normals=n,uv=z['uv'],faces=z['faces'][:,[0,2,1]])

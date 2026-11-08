from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];D=Path('strap-density-study');(D/'end-shell-audit').mkdir(parents=True,exist_ok=True);(D/'shell/uv-v10').mkdir(parents=True,exist_ok=True)
for i,j in enumerate([0,2,1]):
 z=np.load(R/f'input-2-{j}.npz');s=np.array([-1,1,-1]);np.savez_compressed(D/f'input-0-{i}.npz',positions=z['positions']*s,normals=z['normals']*s,uv=z['uv'],faces=z['faces'])

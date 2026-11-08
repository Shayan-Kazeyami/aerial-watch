from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3];D=Path('strap-density-study');D.mkdir(exist_ok=True)
for can,ori in enumerate([0,2,1]):
 z=np.load(R/f'strap-density-study/input-2-{ori}.npz');p=z['positions'].copy();n=z['normals'].copy();p[:,2]*=-1;n[:,2]*=-1;np.savez_compressed(D/f'input-0-{can}.npz',positions=p,normals=n,uv=z['uv'],faces=z['faces'][:,[0,2,1]])

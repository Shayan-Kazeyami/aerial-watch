import os
import numpy as np,json
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR'])
def topo(ts):
 p=np.round(ts.reshape(-1,3).astype(float),6);v,iv=np.unique(p,axis=0,return_inverse=True);f=iv.reshape(-1,3);edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,n=np.unique(edges,axis=0,return_counts=True);return dict(boundary=int((n==1).sum()),nonmanifold=int((n>2).sum()),degenerate=int((np.diff(np.sort(f,axis=1),axis=1)==0).any(1).sum()))
old=[];new=[]
for pi in range(3):
 q=np.load(D/f'input-0-{pi}.npz');old.append(q['positions'][q['faces']]);new.append(np.load(D/f'round-cap-0-{pi}.npz')['triangles'][:,:,:3])
res=dict(before=topo(np.concatenate(old)),after=topo(np.concatenate(new)),warning='Rounded1e-6mm topology diagnostic only; requires exact cut-edge validation before release')
json.dump(res,open(D/'round-cap-topology.json','w'),indent=2);print(res)

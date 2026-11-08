import numpy as np,json
from collections import Counter
from pathlib import Path
O=Path('strap-density-study/wide-uv14-lower-right');D=Path('strap-density-study/neck-v13-qa/lower-right/strap-density-study');src=[]
for m in range(3):
 z=np.load(D/f'input-0-{m}.npz');src.append(z['positions'][z['faces']])
new=np.load(O/'output.npz')['triangles'][:,:,:3];rows=[]
def edges(T,n):
 q=np.round(T.astype(float),n);p,ids=np.unique(q.reshape(-1,3),axis=0,return_inverse=True);ids=ids.reshape(-1,3);e=np.sort(np.concatenate([ids[:,[0,1]],ids[:,[1,2]],ids[:,[2,0]]]),axis=1);u,c=np.unique(e,axis=0,return_counts=True);return {tuple(map(tuple,p[a]))for a in u[c==1]},int((c>2).sum())
for n in [8,7,6,5]:
 a,an=edges(np.concatenate(src),n);b,bn=edges(new,n);rows.append(dict(digits=n,sourceBoundary=len(a),newBoundary=len(b),added=len(b-a),missing=len(a-b),sourceNonmanifold=an,newNonmanifold=bn))
(O/'topology.json').write_text(json.dumps(rows,indent=2));print(rows)

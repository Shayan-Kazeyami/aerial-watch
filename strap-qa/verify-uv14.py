import numpy as np,json
from pathlib import Path
D=Path('strap-density-study/neck-v13-qa/upper-left/strap-density-study');O=Path('strap-density-study/wide-uv14')
def audit(t):
 p,f=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);f=f.reshape(-1,3);es=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);sg=np.where(es[:,0]<es[:,1],1,-1);se=np.sort(es,axis=1);edge,inv,n=np.unique(se,axis=0,return_inverse=True,return_counts=True);s=np.bincount(inv,weights=sg);bd={tuple(p[e].ravel())for e in edge[n==1]};area=np.linalg.norm(np.cross(t[:,1].astype(float)-t[:,0],t[:,2].astype(float)-t[:,0]),axis=1);return bd,dict(boundary=len(bd),nonmanifold=int((n>2).sum()),winding=int(((n==2)&(abs(s)>0)).sum()),zero=int((area==0).sum()))
old=[];new=[]
for m in range(3):
 z=np.load(D/f'input-0-{m}.npz');old.append(z['positions'][z['faces']]);new.append(np.load(O/f'round-cap-0-{m}.npz')['triangles'][:,:,:3])
a,ar=audit(np.concatenate(old).astype('<f4'));b,br=audit(np.concatenate(new).astype('<f4'));assert a==b,(ar,br);assert br['nonmanifold']<=ar['nonmanifold'];assert br['winding']==0 and br['zero']==0,br
(O/'strict-geometry-gate.json').write_text(json.dumps(dict(source=ar,candidate=br,passed=True),indent=2));print(ar,br)

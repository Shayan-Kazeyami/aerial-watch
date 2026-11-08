import os
import numpy as np,json
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR']);counts=[]
for i in range(3):
 T=np.load(D/f'round-cap-0-{i}.npz')['triangles'];p=T[:,:,:3];y=p[:,:,1]+.95;z=p[:,:,2]+22.4;r=np.hypot(y,z);mask=(r>1.578)&(r<1.581)&(p[:,:,0]>-9.9)&(p[:,:,0]<9.920431)&(y>0);n=np.stack([np.zeros_like(y),y/r,z/r],2);T[:,:,3:6][mask]=n[mask]; cap=(p[:,:,0]>9.96042)&(p[:,:,0]<9.96044)&(r>1.21)&(r<1.54043); T[:,:,3:6][cap]=np.array([1.,0.,0.]);np.savez_compressed(D/f'round-cap-0-{i}.npz',triangles=T);counts.append(int(mask.sum()))
json.dump(dict(corners=counts,scope='analytic radial normal for unchanged exposed cylinder before new fillet tangent'),open(D/'round-cap-cylinder-normals.json','w'))

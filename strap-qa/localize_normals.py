import os,sys,numpy as np
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR'])
for i in range(3):
 p=D/f'round-cap-0-{i}.npz';t=np.load(p)['triangles']
 if sys.argv[1]=='save':np.save(D/f'precrease-{i}.npy',t[:,:,3:6]);continue
 old=np.load(D/f'precrease-{i}.npy');y=t[:,:,1]+.95;z=t[:,:,2]+22.4;r=np.hypot(y,z);a=np.abs(np.arctan2(z,y));w=np.clip((r-1.4504276)/.09,0,1)*np.clip((t[:,:,0]-9.60)/.32,0,1)*np.clip((np.deg2rad(75)-a)/np.deg2rad(30),0,1);w=w*w*(3-2*w);n=old*(1-w[:,:,None])+t[:,:,3:6]*w[:,:,None];n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-20);t[:,:,3:6]=np.where((w==0)[:,:,None],old,n);np.savez_compressed(p,triangles=t)

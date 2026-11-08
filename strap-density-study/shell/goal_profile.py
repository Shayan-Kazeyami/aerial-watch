import numpy as np
from pathlib import Path
from shapely.geometry import Polygon
A=Path('strap-density-study/end-shell-audit');raw=np.load(A/'paint-outer-boundary.npz')['positions'];poly=Polygon(raw[:,1:]).buffer(0);coords=np.array(poly.exterior.coords)[:-1];bottom=np.flatnonzero(abs(coords[:,0]+3)<1e-7);i=bottom[np.argmin(coords[bottom,1])];j=bottom[np.argmax(coords[bottom,1])]
def walk(a,b,step):
 ids=[a]
 while ids[-1]!=b:ids.append((ids[-1]+step)%len(coords))
 return coords[ids]
qs=[walk(i,j,1),walk(i,j,-1)];yz=max(qs,key=lambda p:p[:,0].max());aa=raw[:,1:];bb=np.roll(raw,-1,axis=0)[:,1:];dd=bb-aa;v=yz[:,None,:]-aa[None,:,:];tt=np.clip((v*dd[None,:,:]).sum(2)/np.maximum((dd*dd).sum(1),1e-30),0,1);dist=np.linalg.norm(v-tt[:,:,None]*dd[None,:,:],axis=2);ids=dist.argmin(1);xx=raw[ids,0]*(1-tt[np.arange(len(yz)),ids])+np.roll(raw,-1,axis=0)[ids,0]*tt[np.arange(len(yz)),ids];goal=np.c_[xx,yz];r=np.hypot(goal[:,1]+.95,goal[:,2]+22.4);central=np.flatnonzero((goal[:,1]>-2.4)&(r>1.57));a,b=central[0],central[-1];phi=np.unwrap(np.arctan2(goal[a:b+1,2]+22.4,goal[a:b+1,1]+.95));order=np.argsort(phi);ph=phi[order];gg=goal[a:b+1][order]
def goal_at(cut):
 # Match ordered section arclength, not polar angle: lower neck is not star-shaped.
 # Polar sorting reversed a collinear neck run on different floating-point builds.
 src=np.load(A/'xcut_outer_profile-path.npz')['positions']
 sl=np.r_[0,np.cumsum(np.linalg.norm(np.diff(src,axis=0),axis=1))];sl/=sl[-1]
 aa=src[:-1];dd=np.diff(src,axis=0);v=cut[:,None,:]-aa[None,:,:]
 t=np.clip((v*dd[None,:,:]).sum(2)/np.maximum((dd*dd).sum(1),1e-30),0,1)
 ids=np.linalg.norm(v-t[:,:,None]*dd[None,:,:],axis=2).argmin(1)
 u=sl[ids]+t[np.arange(len(cut)),ids]*(sl[ids+1]-sl[ids])
 gl=np.r_[0,np.cumsum(np.linalg.norm(np.diff(goal,axis=0),axis=1))];gl/=gl[-1]
 return np.stack([np.interp(u,gl,goal[:,k]) for k in range(3)],axis=1)

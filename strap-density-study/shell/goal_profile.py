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
 out=np.empty_like(cut);theta=np.arctan2(cut[:,2]+22.4,cut[:,1]+.95);left=(cut[:,1]<=-2.4)&(cut[:,2]<-22.4);right=(cut[:,1]<=-2.4)&~left;mid=~(left|right)
 for k in range(3):
  out[mid,k]=np.interp(theta[mid],ph,gg[:,k]);lp=goal[:a+1];idx=np.argsort(lp[:,1]);out[left,k]=np.interp(cut[left,1],lp[idx,1],lp[idx,k]);rp=goal[b:];idx=np.argsort(rp[:,1]);out[right,k]=np.interp(cut[right,1],rp[idx,1],rp[idx,k])
 return out

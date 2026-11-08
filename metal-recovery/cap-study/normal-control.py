import numpy as np
z=np.load('metal-recovery/cap-study/hybrid-smooth-v4.npz');p,n,uv,f=z['position'],z['normal'].copy(),z['uv'],z['index'];A=20.55;B=21.45
for sy in [-1,1]:
 for sx in [-1,1]:
  m=(p[:,1]*sy>A+1e-6)&(p[:,1]*sy<B-1e-6)&(p[:,0]*sx>9);v=p[m][:,[0,2]]-np.array([sx*11.65,-.9]);tt=np.arctan2(v[:,1],v[:,0]);ends=[]
  for y in [A,B]:
   ids=np.flatnonzero((abs(p[:,1]-sy*y)<1e-6)&(p[:,0]*sx>9));v=p[ids][:,[0,2]]-np.array([sx*11.65,-.9]);theta=np.arctan2(v[:,1],v[:,0]);o=np.argsort(theta);theta=theta[o];ns=n[ids[o]];interp=np.stack([np.interp(tt,np.r_[theta[-1]-2*np.pi,theta,theta[0]+2*np.pi],np.r_[ns[-1,k],ns[:,k],ns[0,k]]) for k in range(3)],axis=1);interp/=np.linalg.norm(interp,axis=1)[:,None];ends.append(interp)
  t=(abs(p[m,1])-A)/(B-A);nn=(1-t[:,None])*ends[0]+t[:,None]*ends[1];nn/=np.linalg.norm(nn,axis=1)[:,None];n[m]=nn
np.savez_compressed('metal-recovery/cap-study/hybrid-normal-control-v5.npz',position=p,normal=n,uv=uv,index=f)

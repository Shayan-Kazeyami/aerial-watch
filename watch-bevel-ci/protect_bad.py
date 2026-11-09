import numpy as np
from scipy.spatial import cKDTree
D=np.load('watch-bevel/wide-cap.npz');p,n=D['position'],D['normal'];orig=D['index'];f=np.r_[np.fromfile('watch-bevel/protected-ix.bin','u4').reshape(-1,3),np.fromfile('watch-bevel/root-opt-0.004.bin','u4').reshape(-1,3)]
t=p[f].astype('f8');cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);dots=np.einsum('ij,ij->i',cr,n[f].mean(1));bad=set(f[dots< -1e-9].ravel().tolist());w,inv=np.unique(np.round(p.astype('f8'),5),axis=0,return_inverse=True);fw=inv[f];edges=np.sort(np.concatenate([fw[:,[0,1]],fw[:,[1,2]],fw[:,[2,0]]]),axis=1);ed,ct=np.unique(edges,axis=0,return_counts=True);badw=np.unique(ed[ct>2]);bad.update(np.flatnonzero(np.isin(inv,badw)).tolist());print('bad',len(bad),'flips',int((dots< -1e-9).sum()),'nonmanifold',int((ct>2).sum()))
if bad:
 ids=np.unique(np.concatenate(cKDTree(p).query_ball_point(p[list(bad)],.06)));locks=np.fromfile('watch-bevel/locks.bin','u1');locks[ids]=1;locks.tofile('watch-bevel/locks.bin');print('new locked',len(ids),'total',locks.sum())

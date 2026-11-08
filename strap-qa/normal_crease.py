import os
import numpy as np,json
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR']);ts=[np.load(D/f'round-cap-0-{i}.npz')['triangles']for i in range(3)];T=np.concatenate(ts);p=T[:,:,:3].astype(float);_,iv=np.unique(np.round(p.reshape(-1,3),6),axis=0,return_inverse=True);f=iv.reshape(-1,3);fn=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);fn/=np.maximum(np.linalg.norm(fn,axis=1,keepdims=True),1e-30);angles=[]
for k in range(3):
 a=p[:,(k+1)%3]-p[:,k];b=p[:,(k+2)%3]-p[:,k];angles.append(np.arctan2(np.linalg.norm(np.cross(a,b),axis=1),np.einsum('ij,ij->i',a,b)))
weights=np.stack(angles,1).reshape(-1);normals=np.repeat(fn,3,axis=0);order=np.argsort(iv);sortedids=iv[order];bounds=np.r_[0,np.flatnonzero(np.diff(sortedids))+1,len(order)];result=np.empty_like(normals)
for a,b in zip(bounds[:-1],bounds[1:]):
 ids=order[a:b];ns=normals[ids];dots=ns@ns.T;mask=dots>np.cos(np.deg2rad(35));agg=(mask*weights[ids][None,:])@ns;agg/=np.maximum(np.linalg.norm(agg,axis=1,keepdims=True),1e-30);result[ids]=agg
T[:,:,3:6]=result.reshape(-1,3,3);off=0
for i,t in enumerate(ts):np.savez_compressed(D/f'round-cap-0-{i}.npz',triangles=T[off:off+len(t)]);off+=len(t)
json.dump(dict(method='geometric corner-angle-weighted;35deg face-normal grouping',scope='upper body normals, not geometry; sewing and lower body untouched'),open(D/'round-cap-normal-field.json','w'))

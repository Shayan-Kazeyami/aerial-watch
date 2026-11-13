import numpy as np,pathlib,json,sys
from scipy.spatial import cKDTree
for d in pathlib.Path('marked-mesh-qa/parts').iterdir():
 p=np.fromfile(d/'position.bin','f4').reshape(-1,3);n=np.fromfile(d/'normal.bin','f4').reshape(-1,3);locks=np.fromfile(d/'locks.bin','u1');old=np.fromfile(d/'index.bin','u4').reshape(-1,3);new=np.fromfile(d/'opt-0.008.bin','u4').reshape(-1,3)
 _,inv=np.unique(np.round(p.astype('f8'),5),axis=0,return_inverse=True)
 def bad(f):
  q=p[f].astype('f8');cr=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);flip=np.einsum('ij,ij->i',cr,n[f].mean(1))< -1e-9
  fw=inv[f];e=np.sort(np.concatenate([fw[:,[0,1]],fw[:,[1,2]],fw[:,[2,0]]]),axis=1);ed,ct=np.unique(e,axis=0,return_counts=True)
  return flip,ed[ct>2],ed[ct==1]
 of,oe,ob=bad(old);nf,ne,nb=bad(new);oldtris={tuple(sorted(x)) for x in old[of]};newflip=[x for x in new[nf] if tuple(sorted(x))not in oldtris];oldedge={tuple(x)for x in oe};newedge=[x for x in ne if tuple(x)not in oldedge];oldbound={tuple(x)for x in ob};newbound=[x for x in nb if tuple(x)not in oldbound]
 ids=set(np.array(newflip,dtype=int).ravel().tolist());w=set(np.array(newedge+newbound,dtype=int).ravel().tolist());ids.update(np.flatnonzero(np.isin(inv,list(w))).tolist())
 print(d.name,'tri',len(new),'newFlips',len(newflip),'newNonManifold',len(newedge),'newBound',len(newbound),'lock',len(ids))
 if ids and '--verify' in sys.argv:raise AssertionError(d.name+' topology failure')
 if ids:
  near=np.unique(np.concatenate(cKDTree(p).query_ball_point(p[list(ids)],.3)));locks[near]=1;locks.tofile(d/'locks.bin')

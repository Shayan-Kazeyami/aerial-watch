"""Coalesce only sub-ULP added chart knots; all geometry/interface vertices locked."""
import numpy as np,json
from pathlib import Path
from scipy.spatial import cKDTree
O=Path('strap-density-study/wide-uv14-lower-left');parts=[np.load(O/f'new-patch-{m}.npz')for m in range(3)];ts=np.concatenate([z['triangles']for z in parts]);origins=np.concatenate([z['sourceFace']for z in parts]);mats=np.repeat(np.arange(3),[len(z['triangles'])for z in parts]);p,iv=np.unique(ts[:,:,:3].reshape(-1,3),axis=0,return_inverse=True);f=iv.reshape(-1,3);e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);u,c=np.unique(e,axis=0,return_counts=True);locked=set(np.unique(u[c==1]));original=set(tuple(x)for m in range(3)for x in np.load(O/f'target-{m}.npz')['triangles'][:,:,:3].reshape(-1,3));locked.update(i for i,x in enumerate(p)if tuple(x)in original);eps=float(np.spacing(abs(p)).max());pairs=list(cKDTree(p).query_pairs(eps));parent=np.arange(len(p));members={i:[i]for i in range(len(p))};valence=np.bincount(f.ravel(),minlength=len(p))
def find(i):
 while parent[i]!=i:i=parent[i]
 return i
records=[]
for a,b in sorted(pairs,key=lambda ab:np.linalg.norm(p[ab[0]]-p[ab[1]])):
 aa,bb=find(a),find(b)
 if aa==bb or aa in locked or bb in locked:continue
 ids=members[aa]+members[bb];rep=max([aa,bb],key=lambda i:valence[i]);other=bb if rep==aa else aa
 if np.linalg.norm(p[ids].astype(float)-p[rep],axis=1).max()>eps:continue
 parent[other]=rep;members[rep]=ids;records.append(dict(a=int(other),representative=int(rep),distance=float(np.linalg.norm(p[other]-p[rep]))))
originalAreas=np.linalg.norm(np.cross(ts[:,1,:3].astype(float)-ts[:,0,:3],ts[:,2,:3].astype(float)-ts[:,0,:3]),axis=1)/2;originalMats=mats.copy();newp=np.array([p[find(i)]for i in range(len(p))]);ts[:,:,:3]=newp[f];p2,iv2=np.unique(ts[:,:,:3].reshape(-1,3),axis=0,return_inverse=True);ff=iv2.reshape(-1,3);good=(ff[:,0]!=ff[:,1])&(ff[:,1]!=ff[:,2])&(ff[:,2]!=ff[:,0]);ts=ts[good];origins=origins[good];mats=mats[good];whole=[]
for m,z in enumerate(parts):
 new=ts[mats==m];old=np.load(O/f'round-cap-0-{m}.npz')['triangles'];arr=np.concatenate([old[:-len(z['triangles'])],new]);np.savez_compressed(O/f'new-patch-{m}.npz',triangles=new,sourceFace=origins[mats==m]);np.savez_compressed(O/f'round-cap-0-{m}.npz',triangles=arr);whole.append(arr)
np.savez_compressed(O/'output.npz',triangles=np.concatenate(whole));(O/'coalesce-report.json').write_text(json.dumps(dict(lockedVertices=len(locked),localULP=eps,removedFaces=int((~good).sum()),removedSourceArea=float(originalAreas[~good].sum()),removedAreaByMaterial={int(m):float(originalAreas[(~good)&(originalMats==m)].sum())for m in range(3)},maxDisplacement=float(np.linalg.norm(newp.astype(float)-p,axis=1).max()),merges=records),indent=2));print('merged',len(records),'faces removed',sum(~good))

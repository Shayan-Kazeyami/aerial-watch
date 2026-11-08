from pathlib import Path
import numpy as np,json
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
D=Path('strap-density-study');O=D/'shell/uv-v10';q=dict(np.load(O/'stitched-new.npz'));T=q['triangles'].astype(float);K=q['kind'];p,first,iv=np.unique(np.round(T.reshape(-1,3),8),axis=0,return_index=True,return_inverse=True);p=T.reshape(-1,3)[first].copy();f=iv.reshape(-1,3);original=p.copy()
def solve(faceMask,axes,extraFixed,mode):
 global p
 ff=f[faceMask];ee=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);ee=np.sort(ee,axis=1);edges,c=np.unique(ee,axis=0,return_counts=True);bound=np.unique(edges[c==1]);verts=np.unique(ff);fixed=np.unique(np.r_[bound,verts[extraFixed[verts]]]);free=np.setdiff1d(verts,fixed);mp=np.full(len(p),-1);mp[free]=np.arange(len(free));row=[];col=[];dat=[];rhs=np.zeros((len(free),len(axes)));diag=np.zeros(len(free))
 for a,b in edges:
  # Uniform combinatorial Laplace is positive and avoids unstable source sliver cotangents.
  w=1.
  for i,j in [(a,b),(b,a)]:
   ii=mp[i]
   if ii<0:continue
   diag[ii]+=w
   if mp[j]>=0:row.append(ii);col.append(mp[j]);dat.append(-w)
   else:rhs[ii]+=w*p[j,axes]
 row.extend(range(len(free)));col.extend(range(len(free)));dat.extend(diag);A=coo_matrix((dat,(row,col)),shape=(len(free),len(free))).tocsr();val=spsolve(A,rhs)
 if len(axes)==1:val=val[:,None]if val.ndim==1 else val
 p[np.ix_(free,axes)]=val;print(mode,'free',len(free),'maxmove',np.linalg.norm(p-original,axis=1).max())
# Cap height is harmonic over actual YZ chart, all actual outer/bore/bottom perimeter fixed;
# material island is interior chart identity, not an artificial geometry boundary.
solve(K==3,[0],np.zeros(len(p),bool),'cap-X')
# Fair lower collar across transverse rows; preserve exact cut/bottom/cap and upper arc.
# Already smooth collar retained exactly.
q['triangles']=p[f];np.savez_compressed(O/'stitched-new-prefair.npz',**dict(np.load(O/'stitched-new.npz')));np.savez_compressed(O/'stitched-new.npz',**q);json.dump(dict(maxDisplacement=float(np.linalg.norm(p-original,axis=1).max()),p99Displacement=float(np.quantile(np.linalg.norm(p-original,axis=1),.99))),open(O/'fair-report.json','w'),indent=2)

from pathlib import Path
import numpy as np,json,collections
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
O=Path('strap-density-study/shell/uv-v10');q=dict(np.load(O/'stitched-new.npz'));T=q['triangles'];K=q['kind'];p,first,iv=np.unique(np.round(T.reshape(-1,3),8),axis=0,return_index=True,return_inverse=True);p=T.reshape(-1,3)[first].copy();orig=p.copy();f=iv.reshape(-1,3);ff=f[K==3];e=np.sort(np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1);ed,ct=np.unique(e,axis=0,return_counts=True);fixed=np.unique(ed[ct==1]);verts=np.unique(ff);free=np.setdiff1d(verts,fixed);mp=np.full(len(p),-1);mp[free]=np.arange(len(free));weights=collections.defaultdict(float)
for t in ff:
 a=p[t,1:]
 den=abs((a[1,0]-a[0,0])*(a[2,1]-a[0,1])-(a[1,1]-a[0,1])*(a[2,0]-a[0,0]))
 if den<1e-18:continue
 for k in range(3):
  i,j=(k+1)%3,(k+2)%3;cot=float((a[i]-a[k])@(a[j]-a[k])/den);weights[tuple(sorted([t[i],t[j]]))]+=.5*cot
row=[];col=[];dat=[];rhs=np.zeros(len(free));diag=np.zeros(len(free))
for (a,b),w in weights.items():
 for i,j in [(a,b),(b,a)]:
  ii=mp[i]
  if ii<0:continue
  diag[ii]+=w
  if mp[j]>=0:row.append(ii);col.append(mp[j]);dat.append(-w)
  else:rhs[ii]+=w*p[j,0]
row.extend(range(len(free)));col.extend(range(len(free)));dat.extend(diag);A=coo_matrix((dat,(row,col)),shape=(len(free),len(free))).tocsr();p[free,0]=spsolve(A,rhs);q['triangles']=p[f];np.savez_compressed(O/'stitched-new-before-fem.npz',**dict(np.load(O/'stitched-new.npz')));np.savez_compressed(O/'stitched-new.npz',**q);json.dump(dict(freeVertices=len(free),maxDisplacement=float(abs(p[:,0]-orig[:,0]).max())),open(O/'fair-fem-report.json','w'),indent=2);print('capFEM',len(free),abs(p[:,0]-orig[:,0]).max())

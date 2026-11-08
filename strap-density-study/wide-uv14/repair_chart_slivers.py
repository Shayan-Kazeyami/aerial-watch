"""Retriangulate sub-Float32 internal chart slivers without welding vertices.
Remove degenerate ABC cell and split its long-edge neighbor at existing B.
No position changes; only newly generated patch faces may be touched.
"""
import numpy as np,json
from collections import defaultdict,Counter
from pathlib import Path
from scipy.spatial import cKDTree
O=Path('strap-density-study/wide-uv14');patch=[np.load(O/f'new-patch-{m}.npz')['triangles'].astype(float)for m in range(3)];ts=np.concatenate(patch);mats=np.repeat(np.arange(3),list(map(len,patch)));target=np.concatenate([np.load(O/f'target-{m}.npz')['triangles'][:,:,:3]for m in range(3)]).astype(float);tree=cKDTree(target.mean(1));report=[]
def owners(pts):
 _,opts=tree.query(pts.mean(0),k=96);hits=set()
 for j in opts:
  t=target[j];uv=(np.linalg.pinv(np.stack([t[1]-t[0],t[2]-t[0]],1))@(pts-t[0]).T).T;bc=np.c_[1-uv.sum(1),uv]
  if np.linalg.norm(bc@t-pts,axis=1).max()<4e-6 and bc.min()>-2e-4:hits.add(int(j))
 return hits
for iteration in range(12):
 p,iv=np.unique(ts[:,:,:3].reshape(-1,3),axis=0,return_inverse=True);f=iv.reshape(-1,3);edges=defaultdict(list)
 for i,tri in enumerate(f):
  for a,b in zip(tri,np.roll(tri,-1)):edges[tuple(sorted((a,b)))].append((i,1 if a<b else -1))
 bad=Counter(i for vals in edges.values()if len(vals)==2 and vals[0][1]==vals[1][1]for i,d in vals);opts=[i for i,n in bad.items()if n==3]
 if not opts:break
 fi=min(opts,key=lambda i:np.linalg.norm(np.cross(ts[i,1,:3]-ts[i,0,:3],ts[i,2,:3]-ts[i,0,:3])));t=ts[fi];lens=[np.linalg.norm(t[(k+1)%3,:3]-t[k,:3])for k in range(3)];k=int(np.argmax(lens));aa=k;cc=(k+1)%3;bb=(k+2)%3;a,c,b=t[aa,:3],t[cc,:3],t[bb,:3];dd=c-a;fraction=(b-a)@dd/(dd@dd);height=np.linalg.norm(b-a-fraction*dd);eps=float(np.spacing(abs(t[:,:3]).astype('<f4')).max())
 assert -.0001<fraction<1.0001 and height<eps*1.1,(fi,height,eps)
 vals=edges[tuple(sorted((f[fi,aa],f[fi,cc])))];neighbor=[i for i,d in vals if i!=fi];assert len(neighbor)==1;ni=neighbor[0];assert owners(t[:,:3])&owners(ts[ni,:,:3]),'not same parent surface'
 nt=ts[ni];ia=np.where((nt[:,:3]==a).all(1))[0][0];ic=np.where((nt[:,:3]==c).all(1))[0][0];ib=3-ia-ic;q=(1-fraction)*nt[ia]+fraction*nt[ic];q[:3]=b
 # Preserve neighbor's directed edge ordering.
 if (ia+1)%3==ic:repl=[np.array([nt[ia],q,nt[ib]]),np.array([q,nt[ic],nt[ib]])]
 else:repl=[np.array([nt[ic],q,nt[ib]]),np.array([q,nt[ia],nt[ib]])]
 report.append(dict(removedFace=int(fi),neighbor=int(ni),height=float(height),localULP=eps,material=int(mats[ni])));keep=np.ones(len(ts),bool);keep[[fi,ni]]=False;ts=np.concatenate([ts[keep],repl]);mats=np.r_[mats[keep],[mats[ni],mats[ni]]]
else:raise RuntimeError('repair iteration limit')
whole=[]
for m in range(3):
 new=ts[mats==m].astype('<f4');old=np.load(O/f'round-cap-0-{m}.npz')['triangles'];old=old[:-len(patch[m])];arr=np.concatenate([old,new]);whole.append(arr);np.savez_compressed(O/f'new-patch-{m}.npz',triangles=new);np.savez_compressed(O/f'round-cap-0-{m}.npz',triangles=arr)
np.savez_compressed(O/'output.npz',triangles=np.concatenate(whole));(O/'sliver-repair-report.json').write_text(json.dumps(report,indent=2));print(report)

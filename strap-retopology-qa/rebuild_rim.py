"""Contour/depth remeshing from authored profile. No polygon-collapse/decimation."""
import numpy as np,json
from scipy.spatial import cKDTree
from pathlib import Path
R=Path('strap-retopology-qa');a=np.load(R/'face71.npz');p,n,tri=a['POSITION'],a['NORMAL'],a['ix'];mp=np.load(R/'profile-map.npz');g,idx=mp['g'],mp['idx'];N=1216;K=33;grid=g.reshape(2,K,N,3)
# Distinct front/back/cap corner normals retain authored hard transitions.
b=idx//(K*N);k=(idx//N)%K;labels=np.where(np.all(b[tri]==b[tri[:,0]][:,None],axis=1),b[tri[:,0]],np.where(np.mean(k[tri],axis=1)<16,2,3))
lookup={}
for q,lab in zip(tri,labels):
 for v in q:lookup[(int(idx[v]),int(lab))]=int(v)
normalgrid=np.zeros((2,K,N,3))
for back in [0,1]:
 for i in range(N):
  ks=[r for r in range(K) if (back*K*N+r*N+i,back) in lookup]
  if not ks:raise Exception(('missing',back,i))
  for d in range(3):normalgrid[back,:,i,d]=np.interp(np.arange(K),ks,[n[lookup[(back*K*N+r*N+i,back)],d] for r in ks])
normalgrid/=np.linalg.norm(normalgrid,axis=3)[...,None]
# Adaptive depth selection driven by surface deviation plus inherited normal field.
def subdiv(i,lo,hi,out):
 if hi-lo<2:return
 r=np.arange(lo+1,hi);t=(r-lo)/(hi-lo)
 pos=grid[:,lo:lo+1,i]+t[None,:,None]*(grid[:,hi:hi+1,i]-grid[:,lo:lo+1,i]);err=np.linalg.norm(pos-grid[:,r,i],axis=2).max(0)
 nor=normalgrid[:,lo:lo+1,i]+t[None,:,None]*(normalgrid[:,hi:hi+1,i]-normalgrid[:,lo:lo+1,i]);nor/=np.linalg.norm(nor,axis=2)[...,None];ne=np.linalg.norm(nor-normalgrid[:,r,i],axis=2).max(0)
 score=np.maximum(err/.00025,ne/.002)
 if score.max()>1:
  mid=int(r[np.argmax(score)]);out.add(mid);subdiv(i,lo,mid,out);subdiv(i,mid,hi,out)
ks=[]
for i in range(N):
 out={0,32};subdiv(i,0,32,out);ks.append(sorted(out))
verts=[];norms=[];faces=[];vmap={}
def vertex(back,k,i,lab):
 key=(back,k,i,lab)
 if key in vmap:return vmap[key]
 pid=back*K*N+k*N+i;old=lookup.get((pid,lab));v=len(verts);vmap[key]=v;verts.append(p[old] if old is not None else grid[back,k,i]);norms.append(n[old] if old is not None else normalgrid[back,k,i]);return v
# Zipper stitches unequal depth columns without T junctions.
for back in [0,1]:
 for i in range(N):
  j=(i+1)%N;L=ks[i];U=ks[j];l=r=0
  while l<len(L)-1 or r<len(U)-1:
   q=[vertex(back,L[l],i,back),vertex(back,U[r],j,back)]
   if r==len(U)-1 or (l<len(L)-1 and L[l+1]<=U[r+1]):q.append(vertex(back,L[l+1],i,back));l+=1
   else:q.append(vertex(back,U[r+1],j,back));r+=1
   faces.append(q)
for k,lab in [(0,2),(32,3)]:
 for i in range(N):
  j=(i+1)%N;q=[vertex(0,k,i,lab),vertex(0,k,j,lab),vertex(1,k,j,lab),vertex(1,k,i,lab)];faces.extend([q[:3],[q[0],q[2],q[3]]])
v=np.array(verts,dtype='f4');nn=np.array(norms,dtype='f4');ix=np.array(faces,dtype='u4');cr=np.cross(v[ix[:,1]]-v[ix[:,0]],v[ix[:,2]]-v[ix[:,0]]);rev=np.einsum('ij,ij->i',cr,nn[ix].mean(1))<0;ix[rev]=ix[rev][:,[0,2,1]]
np.savez(R/'rim-candidate.npz',POSITION=v,NORMAL=nn,ix=ix)
report={'beforeTriangles':len(tri),'afterTriangles':len(ix),'beforeVertices':len(p),'afterVertices':len(v),'contourSamplesRetained':N,'depthColumnsHistogram':{int(k):int(c)for k,c in zip(*np.unique(list(map(len,ks)),return_counts=True))},'depthToleranceMM':.00025,'normalVectorTolerance':.002,'method':'Reconstruct structured shell from original 33-depth authored profiles; adaptive depth knots and zipper connectivity; full contour preserved; no edge collapse.'};(R/'rim-rebuild-report.json').write_text(json.dumps(report,indent=2));print(report)

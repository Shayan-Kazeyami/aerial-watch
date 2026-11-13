import pathlib,json,numpy as np
Q=pathlib.Path('movement-retopo-qa/structured-cap-study');d=json.loads(pathlib.Path('movement-retopo-qa/97-candidate.json').read_text());p=np.array(sum(d['loops'],[]),float);f=np.array(d['cap']);cross=lambda a,b:a[...,0]*b[...,1]-a[...,1]*b[...,0]
def orient(f):
 rev=cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])<0;f[rev]=f[rev][:,[0,2,1]];return f
f=orient(f);before=f.copy()
# Insert deterministic radial interior samples into the existing constrained mesh.
# Splits keep the exact same planar domain, including all six holes.
rings=[]
for r in np.arange(.2,3.46,.3):
 count=max(16,int(np.ceil(2*np.pi*r/.3)));theta=np.arange(count)*2*np.pi/count;rings.extend(np.column_stack([r*np.cos(theta),r*np.sin(theta)]).tolist())
from scipy.spatial import cKDTree
tree=cKDTree(p);inserted=0
for point in rings:
 point=np.array(point)
 if tree.query(point)[0]<.06:continue
 A=p[f[:,0]];B=p[f[:,1]];C=p[f[:,2]]
 good=(cross(B-A,point-A)>1e-10)&(cross(C-B,point-B)>1e-10)&(cross(A-C,point-C)>1e-10)
 hits=np.flatnonzero(good)
 if not len(hits):continue
 assert len(hits)==1
 i=hits[0];a,b,c=f[i];k=len(p);p=np.concatenate([p,[point]]);f[i]=[a,b,k];f=np.concatenate([f,[[b,c,k],[c,a,k]]]);inserted+=1

# Constrained local flips: preserve every contour edge and vertex; no edge collapse.
flips=0
for sweep in range(200):
 edges={}
 for i,t in enumerate(f):
  for a,b,c in [(t[0],t[1],t[2]),(t[1],t[2],t[0]),(t[2],t[0],t[1])]:edges.setdefault(tuple(sorted([a,b])),[]).append((i,c))
 used=set();n=0
 for (a,b),adj in edges.items():
  if len(adj)!=2:continue
  (i,c),(j,e)=adj
  if i in used or j in used:continue
  A,B,C,D=p[[a,b,c,e]]
  if cross(C-A,B-A)*cross(D-A,B-A)>=-1e-20 or cross(A-C,D-C)*cross(B-C,D-C)>=-1e-20:continue
  # Delaunay criterion using opposite cotangent sums, positive convex quadrilateral.
  u=A-C;v=B-C;cotC=np.dot(u,v)/abs(cross(u,v));u=A-D;v=B-D;cotD=np.dot(u,v)/abs(cross(u,v))
  if cotC+cotD>=-1e-9:continue
  f[i]=[c,e,a];f[j]=[e,c,b];used.update([i,j]);n+=1
 f=orient(f);flips+=n
 if not n:break
print('sweeps',sweep,'flips',flips)
def metric(f):
 e=np.concatenate([p[f[:,0]]-p[f[:,1]],p[f[:,1]]-p[f[:,2]],p[f[:,2]]-p[f[:,0]]]);length=np.linalg.norm(e,axis=1);return {'maxEdgeMM':float(length.max()),'p99EdgeMM':float(np.percentile(length,99))}
def boundary(f):
 e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);e,c=np.unique(e,axis=0,return_counts=True);assert c.max()==2;return e[c==1]
assert np.array_equal(boundary(before),boundary(f));assert len(f)==len(before)+2*inserted
np.savez(Q/'seeded.npz',position2D=p,cap=f);r={'status':'local cap-topology candidate only, not serialized/PBR validated','method':'exact fixed-boundary constrained local Delaunay edge flips; no contour or side-normal changes','flips':flips,'radialInteriorPoints':inserted,'before':metric(before),'after':metric(f),'allBoundaryEdgesExact':True,'beforeCapTriangles':len(before),'afterCapTriangles':len(f),'totalTriangles':17812+4*inserted};(Q/'seeded.json').write_text(json.dumps(r,indent=2));print(r)

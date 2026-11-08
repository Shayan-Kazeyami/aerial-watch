import os
import numpy as np,json
from pathlib import Path
D=Path(os.environ['STRAP_STUDY_DIR']);src=[];cand=[];database={}
for pi in range(3):
 q=np.load(D/f'input-0-{pi}.npz');src.append(q['positions'][q['faces']]);cand.append(dict(np.load(D/f'round-cap-0-{pi}.npz')))
def edge_info(p,axis):
 ids=[i for i in range(3)if i!=axis];keys=[tuple(np.round(p[i].astype(float),6))for i in ids];reverse=keys[0]>keys[1];return tuple(sorted(keys)),ids,reverse
for pi,q in enumerate(cand):
 for face,bc,si in zip(q['triangles'],q['barycentric'],q['source_faces']):
  p=src[pi][si]
  for row,b in zip(face,bc):
   zero=np.flatnonzero(abs(b)<1e-7)
   if len(zero)!=1:continue
   key,ids,rev=edge_info(p,int(zero[0]));t=float(b[ids[1]]/(b[ids].sum()));t=1-t if rev else t
   if 1e-7<t<1-1e-7:database.setdefault(key,[]).append((t,row[:3].copy()))
for key,items in database.items():
 items.sort(key=lambda z:z[0]);keep=[]
 for t,p in items:
  if not keep or (abs(t-keep[-1][0])>1e-7 and np.linalg.norm(p-keep[-1][1])>1e-7):keep.append((t,p))
 database[key]=keep
reports=[]
for pi,q in enumerate(cand):
 out=[];changed=0;inserted=0
 for face,bc,si in zip(q['triangles'],q['barycentric'],q['source_faces']):
  polygon=[];add=0;p=src[pi][si]
  for k in range(3):
   l=(k+1)%3;polygon.append(face[k]);zs=np.flatnonzero((abs(bc[k])<1e-7)&(abs(bc[l])<1e-7))
   if len(zs)!=1:continue
   key,ids,rev=edge_info(p,int(zs[0]));knots=database.get(key,[])
   if not knots:continue
   ta=float(bc[k,ids[1]]/bc[k,ids].sum());tb=float(bc[l,ids[1]]/bc[l,ids].sum());ta,tb=(1-ta,1-tb)if rev else(ta,tb)
   if abs(tb-ta)<1e-12:continue
   needed=[(t,pt)for t,pt in knots if min(ta,tb)+1e-7<t<max(ta,tb)-1e-7 and np.linalg.norm(pt-face[k,:3])>1e-7 and np.linalg.norm(pt-face[l,:3])>1e-7];needed.sort(reverse=tb<ta,key=lambda v:v[0])
   for t,pt in needed:
    a=face[k]+(face[l]-face[k])*((t-ta)/(tb-ta));a[:3]=pt;polygon.append(a);add+=1
  if not add:out.append(face);continue
  changed+=1;inserted+=add;center=face.mean(0)
  for k in range(len(polygon)):out.append(np.array([center,polygon[k],polygon[(k+1)%len(polygon)]]))
 out=np.array(out,dtype='<f4');pp=out[:,:,:3].astype(float);ok=np.linalg.norm(np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]),axis=1)>0;out=out[ok];np.savez_compressed(D/f'round-cap-0-{pi}.npz',triangles=out);reports.append(dict(primitive=pi,edge_split_faces=changed,inserted_knots=inserted,triangles=len(out)));print(reports[-1])
json.dump(dict(source_edges_with_knots=len(database),primitives=reports),open(D/'round-cap-propagation.json','w'),indent=2)

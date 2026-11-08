import numpy as np
from collections import defaultdict
def make_splitter(path):
 q=np.load(path);knots=defaultdict(list)
 def key(a,b):return tuple(sorted([tuple(a.astype('<f4')),tuple(b.astype('<f4'))]))
 for ep,f,p in zip(q['edges'],q['fraction'],q['points']):knots[key(*ep)].append((float(f),p))
 def split(triangles):
  out=[];owners=[]
  for i,t in enumerate(triangles):
   poly=[]
   for a,b in zip(t,np.roll(t,-1,axis=0)):
    poly.append(a);k=key(a[:3],b[:3]);rev=tuple(a[:3].astype('<f4'))>tuple(b[:3].astype('<f4'));seen=set()
    for f,p in sorted(knots.get(k,[]),key=lambda x:1-x[0]if rev else x[0]):
     fac=1-f if rev else f
     if fac<=1e-8 or fac>=1-1e-8 or tuple(p)in seen:continue
     seen.add(tuple(p));row=a+(b-a)*fac;row[:3]=p;poly.append(row)
   if len(poly)==3:out.append(t);owners.append(i)
   else:
    poly=np.array(poly);c=poly.mean(0)
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
     tr=np.array([c,a,b]);p=tr[:,:3].astype('<f4').astype(float)
     if np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))>0:out.append(tr);owners.append(i)
  return np.array(out),np.array(owners,dtype=int)
 return split

import numpy as np
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely.strtree import STRtree
D=Path('strap-density-study');ts=[]
for i in range(3):
 q=np.load(D/f'input-0-{i}.npz');t=q['positions'][q['faces']].astype(float);mask=(t[:,:,0].max(1)>9.3)&(t[:,:,1].max(1)>-3.01)&(t[:,:,2].min(1)<-20);ts.append(t[mask])
T=np.concatenate(ts);a=T[:,0,1:];b=T[:,1,1:]-a;c=T[:,2,1:]-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];keep=abs(det)>1e-13;T=T[keep];a=a[keep];b=b[keep];c=c[keep];det=det[keep];tree=STRtree([Polygon(t[:,1:])for t in T])
def source_x(y,z,fallback):
 y,z,fallback=np.broadcast_arrays(y,z,fallback);out=np.array(fallback,dtype=float).reshape(-1).copy()
 for k,(yy,zz)in enumerate(zip(y.ravel(),z.ravel())):
  ids=tree.query(Point(float(yy),float(zz)).buffer(1e-8));
  if not len(ids):continue
  d=np.array([yy,zz])-a[ids];v=(d[:,0]*c[ids,1]-d[:,1]*c[ids,0])/det[ids];w=(b[ids,0]*d[:,1]-b[ids,1]*d[:,0])/det[ids];u=1-v-w;good=(u>=-1e-6)&(v>=-1e-6)&(w>=-1e-6);xx=u*T[ids,0,0]+v*T[ids,1,0]+w*T[ids,2,0];xx=xx[good&(xx>=9.399999)&(xx<=10.001)]
  if len(xx):out[k]=xx.max()
 return out.reshape(y.shape)

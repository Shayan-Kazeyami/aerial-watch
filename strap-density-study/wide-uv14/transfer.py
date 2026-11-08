import sys
sys.path.insert(0,'/tmp/strap-remesh-deps')
import numpy as np,json
from pathlib import Path
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union,triangulate
from shapely.strtree import STRtree
from shapely import constrained_delaunay_triangles
O=Path('strap-density-study/wide-uv14');z=np.load(O/'source-loft.npz');P=z['positions'];Q=z['param'];UV=z['uv'];labels=z['labels'];mats=z['materials'];charts=[]
def bary(q,t):
 a=t[:,0];b=t[:,1]-a;c=t[:,2]-a;v=q[:,None,:]-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];det=np.where(abs(det)<1e-25,1e-25,det);x=(v[:,:,0]*c[:,1]-v[:,:,1]*c[:,0])/det;y=(b[:,0]*v[:,:,1]-b[:,1]*v[:,:,0])/det;return np.stack([1-x-y,x,y],2)
for lab in np.unique(labels):
 ids=np.where(labels==lab)[0];q=Q[ids];ab=q[:,1]-q[:,0];ac=q[:,2]-q[:,0];area=abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0]);ids=ids[area>1e-10]
 if not len(ids):continue
 geom=unary_union([Polygon(t)for t in Q[ids]]);charts.append(dict(label=int(lab),material=int(mats[ids[0]]),ids=ids,geom=geom,tree=cKDTree(P[ids].mean(1))))
print('charts',len(charts),flush=True);tree=STRtree([c['geom']for c in charts]);records=[];coverage=[];target_meta={m:{k:v for k,v in np.load(O/f'target-{m}.npz').items()} for m in range(3)};target_cache={m:q['triangles'] for m,q in target_meta.items()}
def polygons(g):
 if g.geom_type=='Polygon':return [g]if g.area>1e-14 else[]
 if hasattr(g,'geoms'):return [p for x in g.geoms for p in polygons(x)]
 return []
def uvmap(c,params,positions):
 ids=c['ids'];bc=bary(params,Q[ids]);inside=bc.min(2)>=-1e-7;sp=np.einsum('pti,tij->ptj',bc,P[ids]);dist=np.linalg.norm(sp-positions[:,None,:],axis=2);dist[~inside]=np.inf
 for k in range(len(params)):
  if not inside[k].any():
   # Local unbounded affine continuation; do not clamp UVs to source edges.
   v=np.maximum(-bc[k],0).sum(1);near=np.where(v<v.min()+.02)[0];j=near[np.linalg.norm(sp[k,near]-positions[k],axis=1).argmin()];dist[k,j]=0
 pick=dist.argmin(1);return np.einsum('pi,pij->pj',bc[np.arange(len(params)),pick],UV[ids[pick]])
for mi in range(3):
 d=np.load(O/f'target-{mi}.npz');ts=d['triangles'].astype(float);ps=d['param'];kind=d['kind'];ps[kind==0,:,1]=d['profileS'][kind==0]
 for fi,(t,param,k)in enumerate(zip(ts,ps,kind)):
  if k!=0:records.append((mi,t,param,np.eye(3),(mi,fi)));continue
  poly=Polygon(param)
  if not poly.is_valid or poly.area<1e-13:records.append((mi,t,param,np.eye(3),(mi,fi)));continue
  ids=tree.query(poly);ids=sorted(ids,key=lambda i:charts[i]['tree'].query(t[:,:3].mean(0))[0]);remain=poly;parts=[]
  for cid in ids:
   c=charts[cid];g=remain.intersection(c['geom'])
   for po in polygons(g):parts.append((c,po))
   if not g.is_empty:remain=remain.difference(g)
   if remain.is_empty:break
  if not remain.is_empty:
   cid=min(range(len(charts)),key=lambda i:charts[i]['geom'].distance(poly)*10+charts[i]['tree'].query(t[:,:3].mean(0))[0]);c=charts[cid]
   for po in polygons(remain):parts.append((c,po));coverage.append(dict(material=mi,face=fi,area=po.area,chart=c['label']))
  for c,po in parts:
   # Triangulate chart intersection; filter exterior/hole triangles.
   for tri in constrained_delaunay_triangles(po).geoms:
    if not po.covers(tri.representative_point()):continue
    q=np.array(tri.exterior.coords)[:3];bc=bary(q,param[None])[:,0];a=bc@t;a[:,6:]=uvmap(c,q,a[:,:3]);records.append((c['material'],a,q,bc,(mi,fi)))
 print('processed',mi,len(ts),flush=True)
# Canonical original-edge knots, then propagated splits will be done in a separate topology pass.
parts=[[],[],[]];origin=[[],[],[]];params=[[],[],[]];barys=[[],[],[]]
for mi,a,q,bc,source in records:
 if np.linalg.norm(np.cross(a[1,:3]-a[0,:3],a[2,:3]-a[0,:3]))<1e-15:continue
 # Preserve original winding by comparing original source face (or original a for unchanged).
 if source is not None:
  sm,sf=source;old=target_cache[sm][sf];oldn=np.cross(old[1,:3]-old[0,:3],old[2,:3]-old[0,:3]);newn=np.cross(a[1,:3]-a[0,:3],a[2,:3]-a[0,:3]);
  if oldn@newn<0:a=a[[0,2,1]];q=q[[0,2,1]]
 parts[mi].append(a);params[mi].append(q);origin[mi].append(source if source else(-1,-1));origparam=target_meta[source[0]]['param'][source[1]].copy();origparam[:,1]=target_meta[source[0]]['profileS'][source[1]] if target_meta[source[0]]['kind'][source[1]]==0 else origparam[:,1];barys[mi].append(np.eye(3) if target_meta[source[0]]['kind'][source[1]]!=0 or np.array_equal(a[:,:3],target_cache[source[0]][source[1],:,:3]) else bary(q,origparam[None])[:,0])
for mi in range(3):np.savez_compressed(O/f'raw-transfer-{mi}.npz',triangles=np.array(parts[mi]),param=params[mi],sourceFace=origin[mi],barycentric=barys[mi])
(O/'transfer-report.json').write_text(json.dumps(dict(charts=len(charts),faces=list(map(len,parts)),uncoveredParameterArea=sum(x['area']for x in coverage),extrapolations=coverage),indent=2));print('result',list(map(len,parts)),flush=True)

import sys,numpy as np,json,time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('strap-density-study/end-shell-audit/neck-v13');source=[]
for i in range(3):
 z=np.load(f'strap-density-study/input-0-{i}.npz');source.append(z['positions'][z['faces']])
s=np.concatenate(source).astype(float);new=np.load('strap-density-study/shell/uv-v10/stitched-new.npz')['triangles'].astype(float);outside=np.concatenate([np.load(f'strap-density-study/shell/uv-v10/outside-{i}.npz')['triangles'][:,:,:3] for i in range(3)]);candidate=np.concatenate([new,outside]);
def tree(t):
 p=t.reshape(-1,3);return BVHTree.FromPolygons(p.tolist(),np.arange(len(p)).reshape(-1,3).tolist(),all_triangles=True,epsilon=0.)
def samples(t):return np.unique(np.concatenate([t.reshape(-1,3),t.mean(1),(t[:,0]+t[:,1])/2,(t[:,1]+t[:,2])/2,(t[:,2]+t[:,0])/2]),axis=0)
regional=[]
for t in s[(s[:,:,0].max(1)>=8.5)&(s[:,:,1].max(1)>=-3.5)&(s[:,:,2].min(1)<-20)]:
 po=list(t)
 for axis,value in [(0,8.5),(1,-3.5)]:
  out=[]
  for u,v in zip(po,po[1:]+po[:1]):
   da=u[axis]-value;db=v[axis]-value
   if da>=0:out.append(u)
   if (da>=0)!=(db>=0):out.append(u+da/(da-db)*(v-u))
  po=out
 for i in range(1,len(po)-1):regional.append([po[0],po[i],po[i+1]])
a=tree(s);b=tree(candidate);sn=samples(np.array(regional));nn=samples(new);rows=[]
for label,pts,target in [('new_to_source',nn,a),('source_to_candidate',sn,b)]:
 ds=[];nearest=[];faces=[]
 for p in pts:
  q,n,idx,d=target.find_nearest(Vector(p));ds.append(d);nearest.append(q);faces.append(idx)
 ds=np.array(ds);nearest=np.array(nearest);faces=np.array(faces);i=np.argmax(ds);rr=np.hypot(pts[:,1]+.95,pts[:,2]+22.4);regions={'all':np.ones(len(pts),bool),'bore':rr<.78,'bottom_attachment':pts[:,1]<-2.95,'outer_roll':(rr>1.5)&(pts[:,1]>-2.0),'cap_face':pts[:,0]>9.94};summary={}
 for reg,m in regions.items():
  if m.any():summary[reg]={'samples':int(m.sum()),'maxMM':float(ds[m].max()),'p99MM':float(np.quantile(ds[m],.99)),'meanMM':float(ds[m].mean())}
 rows.append({'direction':label,'regions':summary,'maxPoint':pts[i].tolist(),'nearest':nearest[i].tolist(),'nearestFace':int(faces[i])});np.savez_compressed(R/f'{label}.npz',positions=pts,distances=ds,nearest=nearest,nearestFaces=faces)
(R/'distance-report.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2),flush=True)

import numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('strap-density-study/end-shell-audit/neck-v13');src=[]
for i in range(3):
 z=np.load(f'strap-density-study/input-0-{i}.npz');t=z['positions'][z['faces']].astype(float);src.append(t[(t[:,:,0].max(1)>8.49)&(t[:,:,1].max(1)>-3.51)&(t[:,:,2].min(1)<-20)])
src=np.concatenate(src);new=np.load('strap-density-study/shell/uv-v10/stitched-new.npz')['triangles'].astype(float)
def tree(t):return BVHTree.FromPolygons(t.reshape(-1,3).tolist(),np.arange(t.size//3).reshape(-1,3).tolist(),all_triangles=True,epsilon=0)
def samples(t):
 p=np.unique(np.concatenate([t.reshape(-1,3),t.mean(1),(t[:,0]+t[:,1])/2,(t[:,1]+t[:,2])/2,(t[:,2]+t[:,0])/2]),axis=0);return p[(p[:,0]>8.5-1e-7)&(p[:,1]>-3.5-1e-7)&(p[:,2]<-20)]
rows=[]
for metal in ['springbar','default_case','integrated_case']:
 t=np.load(R/f'{metal}.npz')['triangles'];bt=tree(t);row={'metal':metal,'triangles':len(t),'straps':[]}
 for label,tri in [('source',src),('ordered_v9',new)]:
  pp=samples(tri);distance=[];near=[];ids=[]
  for p in pp:
   q,n,i,d=bt.find_nearest(Vector(p));distance.append(d);near.append(q);ids.append(i)
  distance=np.array(distance);near=np.array(near);ids=np.array(ids);k=distance.argmin();pairs=tree(tri).overlap(bt);row['straps'].append({'strap':label,'samples':len(pp),'minClearanceMM':float(distance[k]),'p01ClearanceMM':float(np.quantile(distance,.01)),'minStrapPoint':pp[k].tolist(),'minMetalPoint':near[k].tolist(),'minMetalFace':int(ids[k]),'BVHOverlapPairs':len(pairs)});np.savez_compressed(R/f'{metal}-{label}.npz',positions=pp,distances=distance,nearest=near,overlapPairs=np.array(pairs));
 rows.append(row);print(row,flush=True)
(R/'metal-contact-report.json').write_text(json.dumps(rows,indent=2))

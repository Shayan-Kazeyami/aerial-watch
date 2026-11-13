import numpy as np,json
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
p=np.fromfile('case-topology-lane/current/position.bin',np.float32).reshape(-1,3);n=np.fromfile('case-topology-lane/current/normal.bin',np.float32).reshape(-1,3);i=np.fromfile('case-topology-lane/current/index.bin',np.uint32).reshape(-1,3)
a=i[:,[0,1,2]].flatten();b=i[:,[1,2,0]].flatten();nc,l=connected_components(coo_matrix((np.ones(len(a)),(a,b)),shape=(len(p),len(p))),directed=False);rows=[]
for k in range(nc):
 v=np.where(l==k)[0];t=np.where(l[i[:,0]]==k)[0];q=p[v];r=np.hypot(q[:,0],q[:,2]);rows.append(dict(id=k,triangles=len(t),vertices=len(v),min=q.min(0).tolist(),max=q.max(0).tolist(),r=[float(r.min()),float(r.max())],normalRange=[n[v].min(0).tolist(),n[v].max(0).tolist()]))
np.save('case-topology-lane/labels.npy',l);open('case-topology-lane/components.json','w').write(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))

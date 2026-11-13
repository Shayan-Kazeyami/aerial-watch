import sys;sys.path.insert(0,'/tmp/marked-py')
import trimesh,numpy as np,pathlib,json
R=pathlib.Path('marked-mesh-qa');out={};rng=np.random.default_rng(17)
for d in (R/'parts').iterdir():
 p=np.fromfile(d/'position.bin','f4').reshape(-1,3);old=np.fromfile(d/'index.bin','u4').reshape(-1,3);new=np.fromfile(d/'opt-0.008.bin','u4').reshape(-1,3);locks=np.fromfile(d/'locks.bin','u1');row={}
 for key,src,dst in [('sourceToCandidate',old,new),('candidateToSource',new,old)]:
  selected=src[(locks[src]==0).any(1)];sel=selected[rng.choice(len(selected),min(len(selected),20000),replace=False)];points=np.concatenate([p[np.unique(sel)],p[sel].mean(1),p[sel[:,[0,1]]].mean(1)])
  mesh=trimesh.Trimesh(p,dst,process=False);dist=[]
  for i in range(0,len(points),1000):
   _,ds,_=trimesh.proximity.closest_point(mesh,points[i:i+1000]);dist.extend(ds)
  row[key]={'samples':len(points),'maxMm':float(np.max(dist)),'p99Mm':float(np.percentile(dist,99))}
 out[d.name]=row;print(d.name,row,flush=True)
(R/'distance-report.json').write_text(json.dumps(out,indent=2))

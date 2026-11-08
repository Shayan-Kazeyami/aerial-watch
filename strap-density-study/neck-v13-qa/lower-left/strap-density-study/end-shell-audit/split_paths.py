import numpy as np,json
from pathlib import Path
R=Path('strap-density-study/end-shell-audit');z=np.load(R/'outer_attachment-loop.npz');p=z['positions'];e=np.flatnonzero((abs(p[:,0]-8.2)<1e-6)&(abs(p[:,1]+3.5)<1e-6));assert len(e)==2;e.sort();paths=[np.arange(e[0],e[1]+1),np.r_[np.arange(e[1],len(p)),np.arange(0,e[0]+1)]];out=[]
for ids in paths:
 pts=p[ids];name='xcut_outer_profile' if np.max(abs(pts[:,0]-8.2))<1e-6 else 'bottom_attachment';edges=ids[:-1];np.savez_compressed(R/f'{name}-path.npz',positions=pts,sourceSegment=z['sourceSegment'][edges],sourcePrimitiveTriangle=z['sourcePrimitiveTriangle'][edges]);out.append({'name':name,'vertices':len(pts),'endpoints':pts[[0,-1]].tolist(),'bounds':[pts.min(0).tolist(),pts.max(0).tolist()],'materialRuns':z['sourcePrimitiveTriangle'][edges,0].tolist()})
(R/'path-report.json').write_text(json.dumps(out,indent=2));print([{k:v for k,v in d.items() if k!='materialRuns'} for d in out])

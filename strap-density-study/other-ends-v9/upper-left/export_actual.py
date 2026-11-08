import numpy as np,json,hashlib
from pathlib import Path
S=Path('strap-density-study/shell/ordered-v9');O=Path('actual');O.mkdir(exist_ok=True);rows=[]
for i in range(3):
 for prefix in ['new-patch','outside','round-cap-0']:
  t=np.load(S/f'{prefix}-{i}.npz')['triangles'].copy();t[:,:,0]*=-1;t[:,:,3]*=-1;t=t[:,[0,2,1]]
  if prefix=='new-patch':
   f=t[:,:,:3].astype(float);keep=np.linalg.norm(np.cross(f[:,1]-f[:,0],f[:,2]-f[:,0]),axis=1)>0;t=t[keep]
  p=O/f'{prefix}-{i}.npz';np.savez_compressed(p,triangles=t);rows.append(dict(file=p.name,faces=len(t),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'manifest.json').write_text(json.dumps(dict(status='private candidate; geometric and visual acceptance separate',transform='Own upper-left source X reflected and winding reversed; output inverse transform',files=rows),indent=2))

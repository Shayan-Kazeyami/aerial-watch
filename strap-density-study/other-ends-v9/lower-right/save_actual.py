import numpy as np,json,hashlib
from pathlib import Path
D=Path('strap-density-study');O=D/'shell/ordered-v9';A=Path('actual-coordinates');A.mkdir(exist_ok=True);rows=[]
def actual(t):
 t=t.astype('<f4').copy();t[:,:,2]*=-1;t[:,:,5]*=-1;return t[:,[0,2,1],:]
def valid(t):return np.linalg.norm(np.cross(t[:,1,:3].astype(float)-t[:,0,:3],t[:,2,:3].astype(float)-t[:,0,:3]),axis=1)>0
for canonical,original in enumerate([0,2,1]):
 old=np.load(O/f'outside-{canonical}.npz')['triangles'].astype('<f4');old=old[valid(old)];whole=np.load(O/f'round-cap-0-{canonical}.npz')['triangles'];patch=whole[len(old):]
 for name,t in [('final-material',whole),('outside-material',old),('new-patch',patch)]:
  path=A/f'{name}-{original}.npz';np.savez_compressed(path,triangles=actual(t));rows.append({'file':str(path),'triangles':len(t),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
manifest={'scope':'private lower-right full ordered-v9 candidate; pending independent gates and actual viewer','canonicalTransform':'Z reflection positions/normals, facewinding reversal; canonicalmaterial0,1,2→actual0,2,1','files':rows,'sourceBounds':'actualX>=9.4,Y>=-3,Z>20; oppositeends/sourcebottom retained','warning':'Do not union independent left/right outsidepieces; longsourceboretriangles spanbothends. Clipoutsidebothvolumes jointly before mergingpatches.'};Path('manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))

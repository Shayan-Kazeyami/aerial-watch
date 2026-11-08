import numpy as np,json,hashlib
from pathlib import Path
root=Path('.');D=Path('strap-density-study');O=D/'shell/ordered-v9';A=root/'actual';A.mkdir(exist_ok=True);scale=np.array([-1,1,-1],dtype='f4');rows=[]
def transform(t):
 t=t.copy().astype('<f4');t[:,:,:3]*=scale;t[:,:,3:6]*=scale;return t
for ci,ai in enumerate([0,2,1]):
 whole=np.load(O/f'round-cap-0-{ci}.npz')['triangles'];old=np.load(O/f'outside-{ci}.npz')['triangles'].astype('<f4');a=old[:,:,:3].astype(float);m=np.linalg.norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]),axis=1)>0;old=old[m];assert np.array_equal(whole[:len(old)],old);patch=whole[len(old):];actualfull=transform(whole);actualold=transform(old);actualpatch=transform(patch)
 np.savez_compressed(A/f'round-cap-2-{ai}.npz',triangles=actualfull);np.savez_compressed(A/f'outside-{ai}.npz',triangles=actualold);np.savez_compressed(A/f'new-patch-{ai}.npz',triangles=actualpatch)
 rows.append({'actualPrimitive':ai,'canonicalPrimitive':ci,'fullFaces':len(whole),'outsideFaces':len(old),'newPatchFaces':len(patch),'fullFloat32SHA256':hashlib.sha256(actualfull.tobytes()).hexdigest(),'patchFloat32SHA256':hashlib.sha256(actualpatch.tobytes()).hexdigest()})
(A/'report.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))

import numpy as np,json
from pathlib import Path
root=Path(__file__).resolve().parents[3];rows=[]
for mi in range(3):
 z=np.load(root/f'strap-density-study/input-2-{mi}.npz');src=np.concatenate([z['positions'],z['normals'],z['uv']],1)[z['faces']].astype('<f4');dst=np.load(f'actual-coordinates/final-material-{mi}.npz')['triangles'].astype('<f4');src[src==0]=0;dst[dst==0]=0;keys=set(t.tobytes() for t in dst);m=(src[:,:,1]<=-3).all(1);left=(src[:,:,0]<0).all(1);rows.append({'actualPrimitive':mi,'sourceBelowYMinus3':int(m.sum()),'missingBelowAttributeFaces':sum(t.tobytes() not in keys for t in src[m]),'sourceLeftFaces':int(left.sum()),'missingLeftAttributeFaces':sum(t.tobytes() not in keys for t in src[left])})
Path('retained-actual-report.json').write_text(json.dumps(rows,indent=2));print(rows)

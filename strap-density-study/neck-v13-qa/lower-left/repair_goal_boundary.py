import numpy as np,json
z=np.load('boundary-cycles.npz');cycles=[z[k] for k in z.files];large=max(cycles,key=lambda p:abs((p[:,1]*np.roll(p,-1,axis=0)[:,2]-p[:,2]*np.roll(p,-1,axis=0)[:,1]).sum()));assert len(large)>100
np.savez_compressed('strap-density-study/end-shell-audit/paint-outer-boundary.npz',positions=large)
from pathlib import Path
A=Path('strap-density-study/end-shell-audit')
for name,wantLowFirst in [('xcut_outer_profile-path',True),('bottom_attachment-path',False)]:
 z=np.load(A/f'{name}.npz');d={k:z[k].copy() for k in z.files};p=d['positions'];lowFirst=p[0,2]<p[-1,2]
 if lowFirst!=wantLowFirst:
  for k in d:d[k]=d[k][::-1].copy()
  np.savez_compressed(A/f'{name}.npz',**d)

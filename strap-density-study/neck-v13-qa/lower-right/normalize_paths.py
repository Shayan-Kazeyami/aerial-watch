from pathlib import Path
import numpy as np
A=Path('strap-density-study/end-shell-audit')
for name,ascending in [('xcut_outer_profile',True),('bottom_attachment',False)]:
 f=A/f'{name}-path.npz';z=np.load(f);d={k:z[k] for k in z.files};p=d['positions'];reverse=(p[0,2]>p[-1,2]) if ascending else(p[0,2]<p[-1,2])
 if reverse:
  d={k:v[::-1] for k,v in d.items()};np.savez_compressed(f,**d)

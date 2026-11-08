import os,sys,numpy as np
from pathlib import Path
ROOT=Path.cwd();R=ROOT/'strap-density-study/neck-v13-qa/lower-right';O=ROOT/'strap-density-study/wide-uv14-lower-right';os.chdir(R);sys.path.insert(0,str(R/'strap-density-study/shell'));ns={};exec(Path('strap-density-study/shell/build_uv.py').read_text().split('prev=p;')[0],ns);lookup={tuple(np.round(p,8)):0. for p in ns['p']}
for u in ns['us'][1:]:
 for p in ns['surface'](u,ns['ss']):lookup[tuple(np.round(p,8))]=float(u)
q=np.load('strap-density-study/shell/uv-v10/raw.npz');m=q['kind']==0;T=q['triangles'][m];S=q['profileS'][m];U=np.array([[lookup[tuple(np.round(p,8))]for p in t]for t in T]);np.savez_compressed(O/'loft-param-triangles.npz',triangles=T,profileS=S,profileU=U,material=q['materials'][m]);print(len(T))

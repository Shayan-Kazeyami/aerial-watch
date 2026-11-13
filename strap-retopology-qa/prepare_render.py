import numpy as np,json,pathlib
R=pathlib.Path('strap-retopology-qa');a=np.load(R/'rim-candidate.npz')
for k in ['POSITION','NORMAL','ix']:a[k].astype('u4' if k=='ix' else 'f4').tofile(R/(k+'.bin'))
(R/'candidate-meta.json').write_text(json.dumps({'vertices':len(a['POSITION']),'triangles':len(a['ix'])}))

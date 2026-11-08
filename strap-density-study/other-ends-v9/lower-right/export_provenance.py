from pathlib import Path
import numpy as np,json
# Reuse isolated deterministic edge splitter; all sourceTriangle IDs remain original lower-mesh face IDs.
s=Path('strap-density-study/shell/stitch_ordered.py').read_text();exec(s.split("q=np.load(O/'raw.npz')")[0])
actual=Path('actual-coordinates');counts=[]
for can,ori in enumerate([0,2,1]):
 z=np.load(A/f'preserved-outside-{can}.npz');base=np.concatenate([z['positions'],z['normals'],z['uv'],z['barycentric']],2);t,ids=split(base);attrs=t[:,:,:8].astype('<f4');area=np.linalg.norm(np.cross(attrs[:,1,:3].astype(float)-attrs[:,0,:3],attrs[:,2,:3].astype(float)-attrs[:,0,:3]),axis=1);keep=area>0;attrs=attrs[keep];ids=ids[keep];bary=t[keep,:,8:11];attrs[:,:,2]*=-1;attrs[:,:,5]*=-1;attrs=attrs[:,[0,2,1],:];bary=bary[:,[0,2,1],:][:,:,[0,2,1]]
 np.savez_compressed(actual/f'outside-material-{ori}-provenance.npz',triangles=attrs,sourceTriangle=z['sourceTriangle'][ids],barycentric=bary,sourcePreservedOutsideIndex=ids);counts.append({'actualPrimitive':ori,'faces':len(attrs),'sourceUniqueFaces':len(np.unique(z['sourceTriangle'][ids]))})
print(counts)

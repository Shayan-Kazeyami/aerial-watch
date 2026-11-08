import numpy as np,json
T=[]
for i in range(3):
 z=np.load(f'strap-density-study/input-0-{i}.npz');T.append(z['positions'][z['faces']])
t=np.concatenate(T);p,ix=np.unique(np.round(t.reshape(-1,3),7),axis=0,return_inverse=True);f=ix.reshape(-1,3);e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);e,c=np.unique(np.sort(e,axis=1),axis=0,return_counts=True);b=p[e[c==1]];inregion=(b[:,:,0].max(1)>=8.2)&(b[:,:,1].max(1)>=-3.5)&(b[:,:,2].min(1)<-20);r={'sourceBoundaryEdges':len(b),'possiblyInsideRepair':int(inregion.sum()),'insideBounds':b[inregion].tolist()};open('punctures.json','w').write(json.dumps(r,indent=2));print(r)

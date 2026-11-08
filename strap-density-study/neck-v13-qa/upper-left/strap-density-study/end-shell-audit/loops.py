import numpy as np,collections,json
from pathlib import Path
root=Path('strap-density-study/end-shell-audit');z=np.load(root/'cut-x8.5-y-3.5.npz');s=z['segments'];lab=z['sourcePrimitiveTriangle'];keys,first,inv=np.unique(np.round(s.reshape(-1,3),7),axis=0,return_index=True,return_inverse=True);coords=s.reshape(-1,3)[first];ed=inv.reshape(-1,2);adj=collections.defaultdict(list)
for i,(a,b) in enumerate(ed):
 if a==b:continue
 adj[a].append((b,i));adj[b].append((a,i))
seen=set();reports=[]
for st in adj:
 if st in seen:continue
 ids=[];eids=[];cur=st;prev=-1
 while cur not in seen:
  seen.add(cur);ids.append(cur);choices=[x for x in adj[cur] if x[0]!=prev];nxt,ei=choices[0];eids.append(ei);prev,cur=cur,nxt
 pts=coords[ids];labels=lab[eids];rr=np.hypot(pts[:,1]+.95,pts[:,2]+22.4);name='bore' if rr.max()<.9 else 'outer_attachment';seams=np.flatnonzero(labels[:,0]!=np.roll(labels[:,0],1));le=np.linalg.norm(pts-np.roll(pts,-1,axis=0),axis=1)
 np.savez_compressed(root/f'{name}-loop.npz',positions=pts,sourcePrimitiveTriangle=labels,sourceSegment=np.array(eids),materialSeamVertices=seams)
 reports.append({'name':name,'vertices':len(pts),'materialCounts':dict(collections.Counter(map(int,labels[:,0]))),'materialSeams':len(seams),'bounds':[pts.min(0).tolist(),pts.max(0).tolist()],'radii':[float(rr.min()),float(rr.max())],'edgeLengths_mm':{'min':float(le.min()),'median':float(np.median(le)),'max':float(le.max())},'seamPositions':pts[seams].tolist()})
(root/'loops.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))

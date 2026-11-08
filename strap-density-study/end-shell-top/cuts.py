import numpy as np,json,collections
from pathlib import Path
out=Path('strap-density-study/end-shell-top');rows=[]
for X in [9.4]:
 for Y in [-2.]:
  seg=[];labels=[];stats=[]
  for pi in range(3):
   z=np.load(f'strap-density-study/input-0-{pi}.npz');p=z['positions'].astype(float);f=z['faces'];t=p[f];mask=(t[:,:,0].max(1)>=X)&(t[:,:,1].max(1)>=Y)&(t[:,:,2].min(1)<-20);cross=whole=0
   for ti in np.flatnonzero(mask):
    poly=list(t[ti]);
    for axis,value in [(0,X),(1,Y)]:
     new=[]
     for a,b in zip(poly,poly[1:]+poly[:1]):
      da=a[axis]-value;db=b[axis]-value
      if da>=0:new.append(a)
      if (da>=0)!=(db>=0):new.append(a+da/(da-db)*(b-a))
     poly=new
     if not poly:break
    if len(poly)<3:continue
    whole+=int((t[ti,:,0]>=X).all() and (t[ti,:,1]>=Y).all());cross+=1
    for a,b in zip(poly,poly[1:]+poly[:1]):
     if np.linalg.norm(a-b)<1e-10:continue
     if (abs(a[0]-X)<1e-8 and abs(b[0]-X)<1e-8) or (abs(a[1]-Y)<1e-8 and abs(b[1]-Y)<1e-8):seg.append([a,b]);labels.append([pi,ti])
   stats.append({'primitive':pi,'intersectedFaces':cross,'fullyRemovedFaces':whole})
  seg=np.array(seg);report={'X':X,'Y':Y,'faces':stats,'segments':len(seg),'tolerances':[]}
  for dig in [7,6,5]:
   u,rev=np.unique(np.round(seg.reshape(-1,3),dig),axis=0,return_inverse=True);ed=rev.reshape(-1,2);adj=collections.defaultdict(list)
   for a,b in ed:
    if a==b:continue
    adj[a].append(b);adj[b].append(a)
   seen=set();comps=[]
   for a in adj:
    if a in seen:continue
    st=[a];seen.add(a);nodes=[]
    while st:
     q=st.pop();nodes.append(q)
     for v in adj[q]:
      if v not in seen:seen.add(v);st.append(v)
    pts=u[nodes];r=np.hypot(pts[:,1]+.95,pts[:,2]+22.4);comps.append({'nodes':len(nodes),'degreeHistogram':dict(collections.Counter(len(adj[v]) for v in nodes)),'bounds':[pts.min(0).tolist(),pts.max(0).tolist()],'radiusRange':[float(r.min()),float(r.max())]})
   report['tolerances'].append({'digits':dig,'components':comps})
  rows.append(report);np.savez_compressed(out/f'cut-x{X}-y{Y}.npz',segments=seg,sourcePrimitiveTriangle=np.array(labels))
(out/'cuts.json').write_text(json.dumps(rows,indent=2));
for r in rows:
 print(r['X'],r['Y'],r['segments'],[(t['digits'],[(c['nodes'],c['degreeHistogram']) for c in t['components']]) for t in r['tolerances']])

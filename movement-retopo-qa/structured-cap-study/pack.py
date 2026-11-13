import pathlib,json,numpy as np,hashlib,base64,gzip,tarfile,io
Q=pathlib.Path('movement-retopo-qa/structured-cap-study');R=pathlib.Path('movement-retopo-qa/runtime97');out=Q/'runtime97';out.mkdir(exist_ok=True);s=np.load(Q/'seeded.npz');d=json.loads(pathlib.Path('movement-retopo-qa/97-candidate.json').read_text());p=np.fromfile(R/'position.bin','<f4').reshape(-1,3);n=np.fromfile(R/'normal.bin','<f4').reshape(-1,3);ix=np.fromfile(R/'index.bin','<u4').reshape(-1,3);pn=np.column_stack([p,n]);cap=np.all(abs(n[ix,:,] if False else n[ix][:,:,1])>.99999,axis=1);side=pn[ix[~cap]];assert cap.sum()==4458*2
points=s['position2D'].astype('<f4');faces=s['cap'];tri=[]
for y,sign in [(d['ymin'],-1),(d['ymax'],1)]:
 pos=np.column_stack([points[:,0],np.full(len(points),y,dtype='<f4'),points[:,1]]);norm=np.zeros_like(pos);norm[:,1]=sign;this=np.column_stack([pos,norm]);tri.append(this[faces[:,[0,2,1]] if sign>0 else faces])
tri=np.concatenate([*tri,side]).astype('<f4');values,inv=np.unique(tri.reshape(-1,6),axis=0,return_inverse=True);ix=inv.astype('<u4');p=values[:,:3].astype('<f4');n=values[:,3:].astype('<f4');assert len(ix)//3==18292
# Exact side tuples, unchanged planar cap domain; manifold test on welded positions.
w,wi=np.unique(p,axis=0,return_inverse=True);fi=wi[ix].reshape(-1,3);edges=np.sort(np.concatenate([fi[:,[0,1]],fi[:,[1,2]],fi[:,[2,0]]]),axis=1);e,c=np.unique(edges,axis=0,return_counts=True);assert np.all(c==2),(np.unique(c,return_counts=True));area=np.linalg.norm(np.cross(w[fi[:,1]]-w[fi[:,0]],w[fi[:,2]]-w[fi[:,0]]),axis=1);assert area.min()>1e-13
volume=np.einsum('ij,ij->i',w[fi[:,0]].astype(float),np.cross(w[fi[:,1]].astype(float),w[fi[:,2]].astype(float))).sum()/6
for name,a in [('position',p),('normal',n),('index',ix)]:a.tofile(out/(name+'.bin'))
manifest=json.loads((R/'manifest.json').read_text());manifest.update(candidateVertices=len(p),candidateTriangles=len(ix)//3,candidatePositionNormalIndexBytes=p.nbytes+n.nbytes+ix.nbytes,exactPositionTriangleStreamPreserved=False,capRetopology='fixed contour/side tuples;120 radial cap interior samples, constrained local Delaunay flips',sideTriangleTuplesExact=True,closedManifold=True,degenerateTriangles=0,volumeMM3=float(volume));manifest['files']={name+'.bin':{'bytes':(out/(name+'.bin')).stat().st_size,'sha256':hashlib.sha256((out/(name+'.bin')).read_bytes()).hexdigest()}for name in ['position','normal','index']};(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(manifest)
b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w')as t:
 for k in ['position','normal','index']:
  data=(out/(k+'.bin')).read_bytes();i=tarfile.TarInfo('movement-fixture/data/97-after-'+k+'.bin');i.size=len(data);t.addfile(i,io.BytesIO(data))
(Q/'compact97.b64').write_bytes(base64.b64encode(gzip.compress(b.getvalue(),mtime=0)))

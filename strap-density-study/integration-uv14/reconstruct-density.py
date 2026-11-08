from pathlib import Path
import numpy as np,json,hashlib,zlib,base64,sys
S,I,O=map(Path,sys.argv[1:4]);O.mkdir(parents=True,exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();j=json.load(open(S/'leather.gltf'));b=(S/'geometry.bin').read_bytes();manifest=json.load(open(I/'manifest.json'));anchor=json.load(open(I/'validated-density-proof-anchor.json'));assert sha(b)==manifest['sourceGeometrySHA256']==anchor['sourceGeometrySHA256'];assert sha((I/'validated-density-proof-anchor.json').read_bytes())==manifest['validatedProofAnchorSHA256'];assert sha((I/'density-report.json').read_bytes())==anchor['files']['report.json'];assert sha((I/'density-verification.json').read_bytes())==anchor['files']['verification.json'];assert sha((I/'cut-config.json').read_bytes())==anchor['files']['cut-config.json'];CONFIG=json.load(open(I/'cut-config.json'))
def arr(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];return np.frombuffer(b,{5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']],a['count']*n,v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
def clip(poly,axis,limit,sign):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=sign*(a[axis]-limit);db=sign*(b[axis]-limit);ia=da>=0;ib=db>=0
  if ia:out.append(a)
  if ia!=ib:out.append(a+(b-a)*da/(da-db))
 return out
def protected(P,F,mesh):
 locked=set(np.flatnonzero(P[:,1]>-3));tri=P[F]
 for e in CONFIG['ends']:
  if e['mesh']!=mesh:continue
  candidates=(np.max(tri[:,:,0]*e['xSign'],1)>=e['xCut'])&(np.max(tri[:,:,1],1)>=e['yCut'])&(np.max(tri[:,:,2]*e['hingeZSign'],1)>=e['zCut'])
  for f in np.flatnonzero(candidates):
   poly=clip(list(tri[f]),0,e['xSign']*e['xCut'],e['xSign'])
   if poly:poly=clip(poly,1,e['yCut'],1)
   if poly:poly=clip(poly,2,e['hingeZSign']*e['zCut'],e['hingeZSign'])
   if poly:locked.update(map(int,F[f]))
 return locked
def edges(f):
 e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),1);u,c=np.unique(e,axis=0,return_counts=True);return set(map(tuple,u[c==1])),set(map(tuple,u[c>2]))
def oriented(f):
 f=tuple(map(int,f));return min(f,f[1:]+f[:1],f[2:]+f[:2])
proof=[]
for e in manifest['rows']:
 m,p=e['mesh'],e['primitive'];q=j['meshes'][m]['primitives'][p];attrs={k:arr(q['attributes'][v]).astype('<f4')for k,v in [('positions','POSITION'),('normals','NORMAL'),('uv','TEXCOORD_0')]};F=arr(q['indices']).reshape(-1,3).astype('<u4');assert sha(F.tobytes())==e['sourceFacesSHA256']
 for k,v in attrs.items():assert sha(v.tobytes())==e['attributes'][k]
 raw=zlib.decompress(base64.b64decode(''.join((I/f).read_text()for f in e['parts'])));assert sha(raw)==e['indexSHA256'];G=np.frombuffer(raw,'<u4').reshape(-1,3);assert len(G)==e['triangles'] and G.max()<len(attrs['positions']);assert e['validatedNPZSHA256']==anchor['files'][f'gated-{m}-{p}.npz'];assert edges(F)==edges(G);locked=protected(attrs['positions'].astype(float),F,m);assert {oriented(f)for f in F if any(int(i)in locked for i in f)}<={oriented(f)for f in G};np.savez_compressed(O/f'input-{m}-{p}.npz',**attrs,faces=G);assert sha((O/f'input-{m}-{p}.npz').read_bytes())==e['validatedNPZSHA256'],'Reconstructed payload differs from independently validated density artifact';proof.append({'mesh':m,'primitive':p,'indexSHA256':e['indexSHA256'],'protectedInterfacesExact':True,'attributesExact':True,'boundaryNonmanifoldExact':True})
(O/'reconstruction-proof.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))

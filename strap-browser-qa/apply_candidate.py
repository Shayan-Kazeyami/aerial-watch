import numpy as np,json,hashlib
from pathlib import Path
src=Path('preview-b/releases/63600a544b71214dcbfceee96a3eac0dbfa48bca7d42d59425acd43bae131bfd/leather-assets/r14');g=json.load(open(src/'leather.gltf'));buf=(src/'geometry.bin').read_bytes();target=Path('strap-browser-qa/candidate');target.mkdir(exist_ok=True)
def read(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];return np.frombuffer(buf,dtype=dt,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n).copy()
assert hashlib.sha256(buf).hexdigest()=='97377092fcfc6f5a7e934e083f71a1d5e99c9d2007a1b5c3ba38a2b6a6dc61e3'
arrays={i:read(i) for i in range(len(g['accessors']))};report=[]
for mi in [0,2]:
 pr=g['meshes'][mi]['primitives'][0];a=pr['attributes'];p=arrays[a['POSITION']];n=arrays[a['NORMAL']];uv=arrays[a['TEXCOORD_0']];f=arrays[pr['indices']].reshape(-1,3);d=np.load(f'strap-browser-qa/patch-{mi}.npz');mask=np.ones(len(f),bool);mask[d['removedFaces']]=False;nf=np.r_[f[mask],d['ix']+len(p)];pp=np.r_[p,d['p']].astype('<f4');nn=np.r_[n,d['normal']].astype('<f4');uu=np.r_[uv,d['uv']].astype('<f4');vs=np.unique(nf);remap=np.full(len(pp),-1);remap[vs]=np.arange(len(vs));nf=remap[nf].astype('<u4');arrays[a['POSITION']]=pp[vs];arrays[a['NORMAL']]=nn[vs];arrays[a['TEXCOORD_0']]=uu[vs];arrays[pr['indices']]=nf.reshape(-1,1);g['accessors'][pr['indices']]['componentType']=5125 if len(vs)>65535 else 5123;arrays[pr['indices']]=arrays[pr['indices']].astype('<u4' if len(vs)>65535 else '<u2')
 # UV and geometry boundary signatures match per edited-chart edge exactly in source precision.
 sourcef=f[d['removedFaces']];srcp=p[sourcef];newp=d['p'].astype('f4')[d['ix']];
 def boundary(p,uv,ff):
  edges=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);ee,nn=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True);b=ee[nn==1];return sorted(tuple(sorted((tuple(np.r_[p[x],uv[x]].tolist()),tuple(np.r_[p[y],uv[y]].tolist())))) for x,y in b)
 # source index graph has all selected chart boundaries preserved, as does candidate
 assert boundary(p,uv,sourcef)==boundary(d['p'].astype('f4'),d['uv'].astype('f4'),d['ix'])
 area=np.linalg.norm(np.cross(pp[vs][nf[:,1]]-pp[vs][nf[:,0]],pp[vs][nf[:,2]]-pp[vs][nf[:,0]]),axis=1)
 report.append({'mesh':mi,'beforeTriangles':len(f),'afterTriangles':len(nf),'beforeVertices':len(p),'afterVertices':len(vs),'exactPositionUVBoundaryMatch':True,'zeroAreaFacesAfter':int(sum(area==0))})
newbuf=bytearray();views=[]
for i,a in enumerate(g['accessors']):
 ar=arrays[i];pad=(-len(newbuf))%4;newbuf.extend(b'\0'*pad);off=len(newbuf);raw=ar.tobytes();newbuf.extend(raw);views.append({'buffer':0,'byteOffset':off,'byteLength':len(raw)});a['bufferView']=i;a.pop('byteOffset',None);a['count']=len(ar)
 if a['type']=='VEC3' and ('min'in a or 'max'in a):a['min']=ar.min(0).tolist();a['max']=ar.max(0).tolist()
g['bufferViews']=views;g['buffers']=[{'uri':'geometry.bin','byteLength':len(newbuf)}];(target/'geometry.bin').write_bytes(newbuf);(target/'leather.gltf').write_text(json.dumps(g));
json.dump({'sourceSHA256':hashlib.sha256(buf).hexdigest(),'candidateSHA256':hashlib.sha256(newbuf).hexdigest(),'sourceBytes':len(buf),'candidateBytes':len(newbuf),'meshes':report},open('strap-browser-qa/export-report.json','w'),indent=2);print(report);print('bytes',len(buf),len(newbuf))

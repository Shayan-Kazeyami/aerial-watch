import pathlib,json,struct,hashlib,copy,os,zlib,base64,numpy as np
Q=pathlib.Path('case-topology-lane/caseback-integration');BASE=pathlib.Path(os.environ.get('WATCH_BASE','strap-combined-qa/resume/recovery-09e3e0ae/preview-b/releases/09e3e0ae0d5b40ddfefdbb3b3987b6dd74ec9a746f5e4f4e0731771b89230a29'));sha=lambda b:hashlib.sha256(b).hexdigest();b=(BASE/'rebuild/assembly.glb').read_bytes();assert sha(b)=='e471d63c55ce81bbc82257602341ae0ce98d96f98a7d078baa1aa4ca72d2d258';ln=struct.unpack_from('<I',b,12)[0];src=json.loads(b[20:20+ln]);buf=b[28+ln:];j=copy.deepcopy(src);assert len(j['accessors'])==len(j['bufferViews'])==903;package=json.load(open('case-topology-lane/recovery-remaining/caseback-package.json'));mi=[i for i,m in enumerate(j['meshes'])if m.get('name')==package['sourceMesh']];assert len(mi)==1;pr=j['meshes'][mi[0]]['primitives'][0];oldids=[];newids=[];raws={};changes=[]
def raw(ai):
 a=src['accessors'][ai];v=src['bufferViews'][a['bufferView']];assert not v.get('byteStride')and not a.get('byteOffset',0);return buf[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
for k in ['position','normal','uv','index']:
 name={'position':'POSITION','normal':'NORMAL','uv':'TEXCOORD_0','index':'indices'}[k];ai=pr['indices']if k=='index'else pr['attributes'][name];a=src['accessors'][ai];canonical=np.frombuffer(raw(ai),{5123:'u2',5125:'u4',5126:'f4'}[a['componentType']]).astype('u4').tobytes()if k=='index'else raw(ai);assert sha(canonical)==package['source'][k]['sha256'];data=zlib.decompress(base64.b64decode(package['candidate'][k]['base64z']));assert sha(data)==package['candidate'][k]['sha256'];dim=1 if k=='index'else(2 if k=='uv'else 3);arr=np.frombuffer(data,'u4'if k=='index'else'f4').reshape(-1,dim);assert np.isfinite(arr).all()
 if k=='index':assert arr.max()<8976;arr=arr.astype('u2')
 # Clone each edited accessor independently, then compact freed source slots.
 na=copy.deepcopy(a);nv=copy.deepcopy(src['bufferViews'][a['bufferView']]);nai=len(j['accessors']);nvi=len(j['bufferViews']);na.update(bufferView=nvi,count=len(arr));nv.update(buffer=0,byteLength=arr.nbytes);na.pop('byteOffset',None)
 if k=='index':na['componentType']=5123
 if k=='position':na.update(min=arr.min(0).tolist(),max=arr.max(0).tolist())
 j['accessors'].append(na);j['bufferViews'].append(nv);raws[nai]=arr.tobytes();oldids.append(ai);newids.append(nai);changes.append({'field':k,'sourceAccessor':ai,'clonedAccessor':nai,'candidateSHA256':sha(data),'sourceSHA256':sha(canonical)})
 if k=='index':pr['indices']=nai
 else:pr['attributes'][name]=nai
used=set()
for m in j['meshes']:
 for p in m['primitives']:
  used.update(p['attributes'].values());used.add(p['indices'])
assert not set(oldids)&used;assert not j.get('animations')and not j.get('skins')
# Fill only the four now-unused slots. Other accessor IDs and all other bytes remain stable.
remap={a:b for a,b in zip(newids,oldids)};finalA=copy.deepcopy(src['accessors']);finalV=copy.deepcopy(src['bufferViews']);rep={}
for old,new in zip(oldids,newids):finalA[old]=copy.deepcopy(j['accessors'][new]);finalA[old]['bufferView']=old;finalV[old]=copy.deepcopy(j['bufferViews'][j['accessors'][new]['bufferView']]);rep[old]=raws[new]
for m in j['meshes']:
 for p in m['primitives']:
  p['indices']=remap.get(p['indices'],p['indices']);p['attributes']={k:remap.get(v,v)for k,v in p['attributes'].items()}
assert j['meshes']==src['meshes'];j['accessors']=finalA;j['bufferViews']=finalV;parts=[];off=0;records=[]
for ai,a in enumerate(finalA):
 data=rep.get(ai,raw(ai));v=finalV[a['bufferView']];v.update(buffer=0,byteOffset=off,byteLength=len(data));parts.extend([data,bytes((-len(data))%4)]);off+=len(data)+(-len(data))%4;records.append({'accessor':ai,'changed':ai in rep,'byteExactToSource':data==raw(ai),'sha256':sha(data)})
for k in ['nodes','materials','scenes','scene','textures','images','samplers','asset']:assert j.get(k)==src.get(k)
j['buffers']=[{'byteLength':off}];jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);out=struct.pack('<IIIII',0x46546c67,2,28+len(jb)+off,len(jb),0x4e4f534a)+jb+struct.pack('<II',off,0x004e4942)+b''.join(parts);dest=Q/'work/rebuild/assembly.glb';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(out)
# Decode final serialized arrays independently and compare to intended package arrays.
n=struct.unpack_from('<I',out,12)[0];g=json.loads(out[20:20+n]);bb=out[28+n:];actual={}
for k,name in [('position','POSITION'),('normal','NORMAL'),('uv','TEXCOORD_0'),('index','indices')]:
 p=g['meshes'][mi[0]]['primitives'][0];ai=p['indices']if k=='index'else p['attributes'][name];a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']];data=bb[v['byteOffset']:v['byteOffset']+v['byteLength']];data=np.frombuffer(data,'u2').astype('u4').tobytes()if k=='index'else data;assert sha(data)==package['candidate'][k]['sha256'];actual[k]=sha(data)
r={'sourceSHA256':sha(b),'candidateSHA256':sha(out),'sourceBytes':len(b),'candidateBytes':len(out),'sourceTriangles':19032,'candidateTriangles':16728,'clonedAccessors':changes,'unusedOriginalsCompacted':oldids,'all899OtherAccessorBytesExact':all(v['byteExactToSource']for v in records if not v['changed']),'nodesMaterialsMeshReferencesExact':True,'serializedArraysMatchCandidate':actual,'accessors':records};(Q/'bake-report.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items()if k!='accessors'})
# Prepare private codec files from verified immutable ownership.
m=json.load(open(BASE/'deployment-manifest.json'));d=Q/'encoder-source'
for f in m['references']:
 if f['path'].startswith('vendor/meshopt/'):
  source=BASE.parent/f['ownerReleaseId']/f['path'];data=source.read_bytes();assert sha(data)==f['sha256'];p=d/f['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

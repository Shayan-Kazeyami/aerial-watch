import pathlib,json,struct,hashlib,numpy as np,copy,sys
R=pathlib.Path('case-topology-lane');out=R/'integration';source=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'metal-recovery/source/rebuild/assembly.glb');b=source.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();ln=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+ln]);original=copy.deepcopy(j);binary=b[28+ln:];reps={};changed={}
assert len(j['accessors'])==len(j['bufferViews'])
def raw(ai):
 a=j['accessors'][ai];v=j['bufferViews'][a['bufferView']];assert not a.get('byteOffset',0);assert not v.get('byteStride');return binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
for patchdir in [R/'crown/bake-patch',R/'hardware/139/bake-patch']:
 patch=json.loads((patchdir/'patch.json').read_text());matches=[m for m in j['meshes'] if m.get('name')==patch['meshName']];assert len(matches)==1;pr=matches[0]['primitives'][0];fields=['POSITION','NORMAL','TEXCOORD_0','indices']if 'fields'in patch else ['POSITION','NORMAL','indices']
 for key in fields:
  ai=pr['indices']if key=='indices'else pr['attributes'][key];a=j['accessors'][ai];src=raw(ai);canonical=np.frombuffer(src,{5123:'u2',5125:'u4'}[a['componentType']]).astype('u4').tobytes()if key=='indices'else src;candidate=(patchdir/(key+'.bin')).read_bytes()
  if 'fields'in patch:spec=patch['fields'][key];assert sha(canonical)==spec['sourceSha256'];assert sha(candidate)==spec['candidateSha256']
  else:
   k={'POSITION':'position','NORMAL':'normal','indices':'index'}[key];assert sha(canonical)==patch['source'][k]['sha256'];assert sha(candidate)==patch['candidate'][k]['sha256']
  arr=np.frombuffer(candidate,'u4'if key=='indices'else 'f4');dim=1 if key=='indices'else(2 if key=='TEXCOORD_0'else 3);arr=arr.reshape(-1,dim)
  if key=='indices':arr=arr.astype('u2')if arr.max()<65536 else arr;a['componentType']=5123 if arr.dtype==np.uint16 else 5125
  a['count']=len(arr)
  if key=='POSITION':a['min']=arr.min(0).tolist();a['max']=arr.max(0).tolist()
  assert ai not in reps;reps[ai]=arr.tobytes();changed[ai]=patch['meshName']
parts=[];offset=0;records=[]
for ai,a in enumerate(j['accessors']):
 v=j['bufferViews'][a['bufferView']];src=raw(ai);data=reps.get(ai,src);v.update(byteOffset=offset,byteLength=len(data),buffer=0);parts.extend([data,bytes((-len(data))%4)]);offset+=len(data)+(-len(data))%4;records.append({'accessor':ai,'changedMesh':changed.get(ai),'bytes':len(data),'sha256':sha(data),'byteIdenticalToSource':data==src})
for k in ['nodes','meshes','materials','scenes','scene','textures','images','samplers']:assert j.get(k)==original.get(k),k
j['buffers']=[{'byteLength':offset}];jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);glb=struct.pack('<IIIII',0x46546c67,2,28+len(jb)+offset,len(jb),0x4e4f534a)+jb+struct.pack('<II',offset,0x004e4942)+b''.join(parts);dest=out/'changes/structured-assembly-assets';dest.mkdir(parents=True,exist_ok=True);(dest/'assembly.glb').write_bytes(glb);rep={'sourceSHA256':sha(b),'candidateSHA256':sha(glb),'sourceBytes':len(b),'candidateBytes':len(glb),'changedAccessors':len(changed),'allOtherAccessorBytesUnchanged':True,'allNodesMeshesMaterialsExtrasUnchanged':True,'accessors':records};(out/'bake-report.json').write_text(json.dumps(rep,indent=2));print({k:v for k,v in rep.items() if k!='accessors'})

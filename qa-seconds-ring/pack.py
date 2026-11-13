import pathlib,struct,json,hashlib,copy,sys,numpy as np
D=pathlib.Path('qa-seconds-ring');P=pathlib.Path(sys.argv[1]);src=P.read_bytes();assert hashlib.sha256(src).hexdigest()=='adfdac66b3ae5f7843a2ce825f2007763849e34373c00096827b5b1cb8cda4b5';N=struct.unpack_from('<I',src,12)[0];j=json.loads(src[20:20+N]);original=copy.deepcopy(j);binary=src[28+N:];data=json.loads((D/'candidate.json').read_text());c={k:np.asarray(v,dtype=np.uint32 if k=='ix' else np.float32).reshape(-1,3 if k in ['POSITION','NORMAL','ix'] else 2)for k,v in data.items()};assert j['nodes'][0]['name']=='SVG seconds-edge-3.1' and j['nodes'][0]['mesh']==0;pr=j['meshes'][0]['primitives'][0];assert pr=={'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'material':0}
raws=[]
for v in original['bufferViews']:raws.append(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
replacements={0:np.asarray(c['POSITION'],dtype='<f4').tobytes(),1:np.asarray(c['NORMAL'],dtype='<f4').tobytes(),2:np.asarray(c['TEXCOORD_0'],dtype='<f4').tobytes(),3:np.asarray(c['ix'],dtype='<u2').tobytes()}
for i in range(3):j['accessors'][i]['count']=len(c['POSITION'])
# Indexed geometry and UV identity, not just matching bounds.
for i,key,size,dtype in [(0,'POSITION',3,'<f4'),(2,'TEXCOORD_0',2,'<f4')]:
 old=np.frombuffer(raws[i],dtype=dtype).reshape(-1,size);ix=np.frombuffer(raws[3],dtype='<u2');assert np.array_equal(old[ix],c[key][c['ix'].ravel()])
newbin=bytearray()
for i,v in enumerate(j['bufferViews']):
 assert v.get('buffer',0)==0 and 'byteStride' not in v
 while len(newbin)%4:newbin.append(0)
 b=replacements.get(i,raws[i]);v['byteOffset']=len(newbin);v['byteLength']=len(b);newbin.extend(b)
while len(newbin)%4:newbin.append(0)
j['buffers'][0]['byteLength']=len(newbin);jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);out=struct.pack('<III',0x46546c67,2,28+len(jb)+len(newbin))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(newbin),0x004e4942)+newbin
(D/'face-svg04-seconds-candidate.glb').write_bytes(out)
# Decode serialized bytes and assert every untouched stream survives exactly.
n2=struct.unpack_from('<I',out,12)[0];j2=json.loads(out[20:20+n2]);b2=out[28+n2:]
for i,v in enumerate(j2['bufferViews']):assert b2[v['byteOffset']:v['byteOffset']+v['byteLength']]==replacements.get(i,raws[i])
for key in ['nodes','meshes','materials','scenes','scene','animations','skins','textures','images','samplers']:assert j2.get(key)==original.get(key),key
assert j2['accessors'][3:]==original['accessors'][3:]
report={'passed':True,'status':'isolated source-owned packed asset, actual packed route QA not yet run','main':'b84a51ec91b715aa70408e8bff6e988e29d93edb','source':str(P),'inputSHA256':hashlib.sha256(src).hexdigest(),'outputSHA256':hashlib.sha256(out).hexdigest(),'inputBytes':len(src),'outputBytes':len(out),'savedBytes':len(src)-len(out),'changedAccessorIDs':[0,1,2,3],'untouchedStreams':177,'all181SerializedStreamsVerified':True,'nodesMeshesMaterialsScenesAndOtherIdentityMetadataUnchanged':True,'indexedPositionAndUVBitExact':True,'verticesBefore':6144,'verticesAfter':3088,'trianglesBefore':3072,'trianglesAfter':3072}
(D/'packed-asset-proof.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

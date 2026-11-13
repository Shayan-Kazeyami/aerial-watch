"""Serialize validated wheel97 arrays into a guarded current assembly.
Local candidate only. Never publish this without exact raw/meshopt viewer QA.
"""
import copy, hashlib, json, pathlib, struct, sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
SOURCE_HASHES = {
    'position': '7064ec190537d5e592edb5aba2bfe90ce9c1baf38293c019baec3cc4626e4000',
    'normal': '326649d3296f700a9eee3e85a024efe1178f14d2d5735325888ebfdda0ee93e3',
    'index': '07c684f9d2937617c4a5ad5062d5f4500df58545a295ea279d4b379f9a2c7b77',
}

def compose(source, destination):
    before = source.read_bytes()
    magic, version, total, n, kind = struct.unpack_from('<IIIII', before)
    assert (magic, version, total, kind) == (0x46546c67, 2, len(before), 0x4e4f534a)
    doc = json.loads(before[20:20+n]); original = copy.deepcopy(doc)
    bn, bk = struct.unpack_from('<II', before, 20+n)
    binary = before[28+n:]
    assert bk == 0x004e4942 and bn == len(binary)
    assert len(doc['accessors']) == len(doc['bufferViews']) == 903
    nodes = [x for x in doc['nodes'] if x.get('extras', {}).get('sourceIndex') == 97]
    assert len(nodes) == 1 and nodes[0]['name'] == 'OM10-00165 · 097'
    mesh_id = nodes[0]['mesh']; primitive = doc['meshes'][mesh_id]['primitives'][0]
    assert primitive == {'attributes': {'POSITION': 718, 'NORMAL': 719}, 'indices': 720, 'material': 4}
    def raw(ai):
        a = original['accessors'][ai]; v = original['bufferViews'][a['bufferView']]
        assert not a.get('byteOffset', 0) and not v.get('byteStride') and not a.get('sparse')
        return binary[v.get('byteOffset', 0):v.get('byteOffset', 0)+v['byteLength']]
    indices = np.frombuffer(raw(720), {5123:'<u2',5125:'<u4'}[doc['accessors'][720]['componentType']]).astype('<u4')
    assert sha(raw(718)) == SOURCE_HASHES['position']
    assert sha(raw(719)) == SOURCE_HASHES['normal']
    assert sha(indices.tobytes()) == SOURCE_HASHES['index'] and len(indices) == 21944*3
    # No unrelated primitive may reference a replaced accessor.
    for mi, mesh in enumerate(doc['meshes']):
        for p in mesh['primitives']:
            if mi != mesh_id:
                assert not ({718,719,720} & (set(p['attributes'].values()) | {p['indices']}))
    manifest = json.loads((ROOT/'runtime97/manifest.json').read_text())
    values = {}
    for key, ai in [('position',718),('normal',719),('index',720)]:
        data = (ROOT/'runtime97'/f'{key}.bin').read_bytes()
        assert len(data) == manifest['files'][key+'.bin']['bytes']
        assert sha(data) == manifest['files'][key+'.bin']['sha256']
        values[ai] = np.frombuffer(data, '<u4' if key=='index' else '<f4')
    p = values[718].reshape(-1,3); normal = values[719].reshape(-1,3); index = values[720]
    assert np.isfinite(p).all() and np.isfinite(normal).all()
    assert len(p) == len(normal) == 18757 and len(index) == 17812*3 and index.max() < len(p)
    assert np.max(np.abs(np.linalg.norm(normal,axis=1)-1)) < 2e-7
    oldp = np.frombuffer(raw(718),'<f4').reshape(-1,3)
    bounds_delta = float(np.max(np.abs(np.concatenate([p.min(0)-oldp.min(0),p.max(0)-oldp.max(0)]))))
    # The previously validated authored float32 contour differs by two ULPs
    # at its outer bound. Preserve that evidence, do not claim exact bounds.
    assert bounds_delta <= 1e-6 and np.array_equal(p[:,1].min(),oldp[:,1].min()) and np.array_equal(p[:,1].max(),oldp[:,1].max())
    replacements = {718:p.tobytes(),719:normal.tobytes(),720:index.astype('<u2').tobytes()}
    for ai in [718,719]: doc['accessors'][ai]['count'] = len(p)
    doc['accessors'][718].update(min=p.min(0).tolist(),max=p.max(0).tolist())
    doc['accessors'][720].update(count=len(index),componentType=5123)
    chunks=[]; offset=0; records=[]
    for ai,a in enumerate(doc['accessors']):
        v=doc['bufferViews'][a['bufferView']]; source_data=raw(ai); data=replacements.get(ai,source_data)
        v.update(byteOffset=offset,byteLength=len(data),buffer=0)
        chunks.extend([data,bytes((-len(data))%4)]); offset+=len(data)+(-len(data))%4
        records.append({'accessor':ai,'unchanged':data==source_data,'sha256':sha(data)})
    assert [x['accessor'] for x in records if not x['unchanged']] == [718,719,720]
    for key in original:
        if key not in ('accessors','bufferViews','buffers'): assert doc[key] == original[key], key
    doc['buffers']=[{'byteLength':offset}]
    jb=json.dumps(doc,separators=(',',':')).encode(); jb+=b' '*((-len(jb))%4)
    result=struct.pack('<IIIII',0x46546c67,2,28+len(jb)+offset,len(jb),0x4e4f534a)+jb+struct.pack('<II',offset,0x004e4942)+b''.join(chunks)
    destination.parent.mkdir(parents=True,exist_ok=True); destination.write_bytes(result)
    report={'sourceSHA256':sha(before),'candidateSHA256':sha(result),'sourceBytes':len(before),'candidateBytes':len(result),'mesh':mesh_id,'sourceIndex':97,'beforeTriangles':21944,'afterTriangles':17812,'maxBoundsDeltaMm':bounds_delta,'axialPlanesExact':True,'onlyChangedAccessors':[718,719,720],'allOtherAccessorBytesUnchanged':True,'allNodesMaterialsAndMeshIdentitiesUnchanged':True,'accessors':records,'status':'Local serialized candidate, exact-current raw/meshopt and mechanical/contact QA pending'}
    destination.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print({k:v for k,v in report.items() if k!='accessors'})

if __name__ == '__main__':
    compose(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))

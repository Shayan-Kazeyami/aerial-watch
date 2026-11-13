"""Blender Python: bounded surface-intersection regression, not solid/contact certification."""
import gzip,json,pathlib,sys
import numpy as np
from mathutils.bvhtree import BVHTree
O=pathlib.Path(sys.argv[-1]);results=[]
def load(path):
 data=json.loads(gzip.decompress(path.read_bytes()));rows={}
 for r in data['rows']:
  p=np.asarray(r['position'],dtype='f8').reshape(-1,3);p=(np.c_[p,np.ones(len(p))]@np.asarray(r['matrix']).reshape(4,4))[:,:3]
  f=np.asarray(r['index']if r['index']is not None else range(len(p)),dtype='i4').reshape(-1,3)
  r.update(p=p,f=f,bvh=BVHTree.FromPolygons(p.tolist(),f.tolist(),all_triangles=True));rows[r['id']]=r
 return rows
for path in sorted(O.glob('*-baseline-contacts.json.gz')):
 pose=path.name.removesuffix('-baseline-contacts.json.gz');old=load(path)
 for variant in ['candidate','bevel']:
  new=load(O/f'{pose}-{variant}-contacts.json.gz');parts=[]
  assert set(old)==set(new),(pose,'Broadphase neighbor set changed',set(old)^set(new))
  targets=[key for key,r in old.items()if r['target']]
  for key in targets:
   a=old[key];b=new[key];assert np.array_equal(a['matrix'],b['matrix'])
   for nkey,neighbor in old.items():
    if nkey==key:continue
    nnew=new[nkey]
    source_pairs=a['bvh'].overlap(neighbor['bvh']);candidate_pairs=b['bvh'].overlap(nnew['bvh'])
    if not source_pairs and not candidate_pairs:continue
    item={'target':key,'neighbor':nkey,'sourcePairs':len(source_pairs),'candidatePairs':len(candidate_pairs),'neighborIsChangedTarget':neighbor['target']}
    if not neighbor['target']:
     assert np.array_equal(neighbor['p'],nnew['p'])and np.array_equal(neighbor['f'],nnew['f']),(pose,nkey,'Unrelated neighbor changed')
     src={int(j)for i,j in source_pairs};dst={int(j)for i,j in candidate_pairs};item.update(sourceNeighborTriangles=len(src),candidateNeighborTriangles=len(dst),newlyIntersectedNeighborTriangles=sorted(dst-src),lostIntersectedNeighborTriangles=sorted(src-dst))
    parts.append(item)
  results.append({'pose':pose,'variant':variant,'visibleTargets':targets,'broadphaseObjects':len(old),'intersections':parts,'newlyIntersectedUnchangedNeighborTriangles':sum(len(x.get('newlyIntersectedNeighborTriangles',[]))for x in parts)})
report={'scope':'Exact runtime visible geometry, assembly poses and changed-source swaps. Blender BVHTree triangle surface-overlap regression. Existing overlaps retained as baseline; newly intersected neighbor faces are investigation flags, not proven penetration depth. No continuous swept-volume or manufacturing certification.','results':results,'noNewUnchangedNeighborTriangleFlags':not any(x['newlyIntersectedUnchangedNeighborTriangles']for x in results)}
(O/'contact-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps({'noNewUnchangedNeighborTriangleFlags':report['noNewUnchangedNeighborTriangleFlags'],'rows':[(x['pose'],x['variant'],x['broadphaseObjects'],x['newlyIntersectedUnchangedNeighborTriangles'])for x in results]},indent=2))

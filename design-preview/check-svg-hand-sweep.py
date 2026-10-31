import bpy,json,math
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'svg-face-r02.blend'));deps=bpy.context.evaluated_depsgraph_get()
verts=[];faces=[]
for obj in bpy.context.scene.objects:
 if not obj.get('premiumFacePart'):continue
 evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();offset=len(verts)
 verts.extend([obj.matrix_world@v.co for v in mesh.vertices]);faces.extend([tuple(offset+i for i in p.vertices) for p in mesh.polygons]);evaluated.to_mesh_clear()
face=BVHTree.FromPolygons(verts,faces,all_triangles=False,epsilon=0)
checks=[]
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or obj.get('assemblyId') not in ['HOUR','MINUTE','SECONDS']:continue
 hits=[];polys=[tuple(p.vertices) for p in obj.data.polygons]
 for angle in range(0,360,5):
  transform=obj.matrix_world@Matrix.Rotation(math.radians(angle),4,'Z')
  tree=BVHTree.FromPolygons([transform@v.co for v in obj.data.vertices],polys,all_triangles=False,epsilon=0)
  pairs=face.overlap(tree)
  if pairs:hits.append({'degrees':angle,'triangle_pairs':len(pairs)})
 checks.append({'hand':obj.get('assemblyId'),'local_axis':'Z (glTF Y-up equivalent)','samples':72,'colliding_samples':hits})
result={'step_degrees':5,'checks':checks,'scope':'Sampled triangle-surface overlap between each original hand and new authored face parts. Not continuous-time, tolerance, force or complete movement certification.'}
(ROOT/'svg-hand-sweep.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

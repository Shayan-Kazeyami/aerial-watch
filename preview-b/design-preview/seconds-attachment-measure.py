import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'rim04-asymmetric.blend'))
d=bpy.context.evaluated_depsgraph_get();trees=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and ('sourceIndex'in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS']) and not o.hide_render:
  e=o.evaluated_get(d);m=e.to_mesh();t=BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[tuple(p.vertices)for p in m.polygons]);e.to_mesh_clear();trees.append((o,t))
rays=[]
for i in range(72):
 a=i*math.tau/72
 for r in [3.15,3.6,4.05]:
  x=-7.998827934265137+r*math.cos(a);y=-.016291368752717972+r*math.sin(a);hits=[]
  for o,t in trees:
   p,n,idx,dist=t.ray_cast(Vector((x,y,3.42)),Vector((0,0,-1)),20)
   if p is not None:hits.append((3.43-p.z,o.name,p.z,o.get('assemblyId')))
  if hits:rays.append({'angle':i*5,'radius':r,'nearest':min(hits)})
report={'ring_underside_z':3.43,'ring_top_z':3.57,'nearest_surface_gap_range_mm':[min(v['nearest'][0]for v in rays),max(v['nearest'][0]for v in rays)],'rays':rays,'sources':[(o.name,o.get('assemblyId'))for o,t in trees]};(R/'seconds-attachment-measure.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items()if k not in ['rays','sources']}));print('nearest',sorted(rays,key=lambda x:x['nearest'][0])[:12]);print('hands',[(o.name,o.get('assemblyId'),list(o.location))for o,t in trees if o.get('assemblyId')in ['HOUR','MINUTE','SECONDS']])

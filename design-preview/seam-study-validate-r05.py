import bpy,bmesh,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r05.blend'))
res=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.get('designPart')!='SEAM-STUDY-STRAP':continue
 me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;zero=0
 for t in me.loop_triangles:
  a,b,c=[uv[i].uv for i in t.loops]
  if abs((b-a).cross(c-a))<1e-16 and t.area>1e-10:zero+=1
 bm=bmesh.new();bm.from_mesh(me);nonman=sum(not e.is_manifold for e in bm.edges);bm.free()
 old=next(x for x in bpy.context.scene.objects if x.get('designPart')=='QUALITY-STRAP' and ('Upper' in x.name)==('Upper' in o.name))
 tree=BVHTree.FromPolygons([v.co for v in old.data.vertices],[tuple(p.vertices) for p in old.data.polygons]);lug=[v.co for v in me.vertices if v.co.z>-5]
 maxdist=max((tree.find_nearest(v)[3] for v in lug),default=0)
 res.append({'name':o.name,'triangles':len(me.loop_triangles),'collapsed_uv_triangles_including_boolean_cuts':zero,'nonmanifold_edges':nonman,'lug_region_vertex_count':len(lug),'max_lug_region_distance_to_original_mm':maxdist})
verts=[];faces=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and not o.hide_render and ('sourceIndex' in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS'] or any(k in o.name.lower() for k in ['case ·','springbar','buckle','crown'])):
  start=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
tree=BVHTree.FromPolygons(verts,faces);col=[];nearest=10000
for o in bpy.context.scene.objects:
 if o.type=='MESH' and 'waxed three-ply stitches' in o.name:
  bvh=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]);overlap=tree.overlap(bvh)
  col.append({'name':o.name,'source_surface_triangle_intersections':len(overlap)})
  for v in list(o.data.vertices)[::21]:nearest=min(nearest,tree.find_nearest(o.matrix_world@v.co)[3])
report={'bands':res,'new_thread_source_collisions':col,'sampled_thread_to_source_minimum_mm':nearest,'limits':'Static mesh checks. New replacement bands are closed after welding split vertices. No dynamic, strength or manufacturing certification.'};(R/'seam-study-r05-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

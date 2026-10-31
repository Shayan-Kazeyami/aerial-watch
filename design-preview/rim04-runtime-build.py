"""Quality-first runtime tessellation; never modifies the full native master."""
import bpy,bmesh,json,math,hashlib,struct
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rim04-asymmetric.blend'))
def identity(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return (h.hexdigest(),tuple(tuple(r) for r in o.matrix_world))
source={o.name:identity(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex' in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS'])}
rim=bpy.data.objects['SVG broad sloped champagne wall'];old=rim.data
profile=json.loads((ROOT/'rim04-profile.json').read_text());layers=profile['depth_layers'];count=len(layers[0]);nv=len(layers)*count
rawverts=[(x,-y,3.47-.5*k/32-back*.08) for back in (0,1) for k,pts in enumerate(layers) for x,y in pts]
faces=[];face_tags=[]
def sparse(i):return 64<=i<=703 or 792<=i<=1191
for back in (0,1):
 for i in range(count):
  step=4 if sparse(i) else 1;j=(i+1)%count
  for k in range(0,32,step):
   left=[back*nv+r*count+i for r in range(k,k+step+1)] if step>1 and not sparse((i-1)%count) else [back*nv+k*count+i,back*nv+(k+step)*count+i]
   right=[back*nv+r*count+j for r in range(k,k+step+1)] if step>1 and not sparse(j) else [back*nv+k*count+j,back*nv+(k+step)*count+j]
   faces.append(tuple([left[0]]+right+list(reversed(left[1:]))));face_tags.append((back,i))
for k in (0,32):
 for i in range(count):
  a=k*count+i;b=k*count+(i+1)%count;faces.append((a,b,b+nv,a+nv));face_tags.append((-1,i))
used=sorted({v for f in faces for v in f});remap={v:i for i,v in enumerate(used)};verts=[rawverts[v] for v in used];faces=[tuple(remap[v] for v in f) for f in faces]
me=bpy.data.meshes.new('Rim04 runtime exact-profile adaptive-depth surface');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(me);bm.free()
for m in old.materials:me.materials.append(m)
for p in me.polygons:p.use_smooth=True
me.set_sharp_from_angle(angle=math.radians(35));rim.data=me;rim['runtimeTessellation']='9 main / 33 endpoint exact depth profiles; full XY sampling; no decimation'
curves=[]
for name in ['SVG champagne aperture rim','SVG lower champagne rim lip']:
 o=bpy.data.objects[name];before=o.data.bevel_resolution;o.data.bevel_resolution=2
 curves.append({'name':name,'old_bevel_resolution':before,'new_bevel_resolution':2,'radius_mm':o.data.bevel_depth,'max_crosssection_sagitta_mm':o.data.bevel_depth*(1-math.cos(math.pi/8))})
# Exact source and complete runtime rim collision checks.
deps=bpy.context.evaluated_depsgraph_get()
def tree(o):
 e=o.evaluated_get(deps);m=e.to_mesh();t=BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[tuple(p.vertices) for p in m.polygons],all_triangles=False);e.to_mesh_clear();return t
rt=tree(rim);hits=[]
for n in source:
 o=bpy.data.objects[n]
 if not o.hide_render and rt.overlap(tree(o)):hits.append(n)
assert all(identity(bpy.data.objects[n])==v for n,v in source.items())
me.calc_loop_triangles();tris=[tuple(t.vertices) for t in me.loop_triangles];t=BVHTree.FromPolygons([v.co for v in me.vertices],tris,all_triangles=True);selfhits=sum(1 for a,b in t.overlap(t) if a<b and not(set(tris[a])&set(tris[b])))
cone_errors=[];left=[];right=[]
for original_index,new_index in remap.items():
 if original_index>=nv:continue
 i=original_index%count
 if 768<=i<1216:
  v=me.vertices[new_index].co;cone_errors.append(abs(math.hypot(v.x,v.y)-(15.7-1.6*(3.47-v.z))))
for p,(back,i) in zip(me.polygons,face_tags):
 if back!=0:continue
 inclination=math.degrees(math.acos(min(1,abs(p.normal.z))))
 if 768<=i<1215:left.append(inclination)
 if 40<=i<727 and i not in [223,383,543]:right.append(inclination)
# Compare full-master sampled front vertices against runtime triangle surface.
nearest=[]
for v in list(old.vertices)[:33*count]:nearest.append(rt.find_nearest(v.co)[3])
audit={'depth_layers':{'main':9,'endpoints':33},'xy_profile_samples':count,'rim_triangles':len(tris),'rim_vertices':len(me.vertices),'nonmanifold_edges':nonmanifold,'self_intersection_pairs':selfhits,'source_meshes_unchanged':len(source),'visible_source_intersections':hits,'left_all_depth_cone_radial_error_max_mm':max(cone_errors),'left_inclination_range_degrees':[min(left),max(left)],'right_inclination_range_degrees':[min(right),max(right)],'full_master_front_vertex_to_runtime_surface_max_mm':max(nearest),'full_master_front_vertex_to_runtime_surface_mean_mm':sum(nearest)/len(nearest),'wire_crosssection_changes':curves,'limits':'Master-vertex to runtime surface comparison, not bidirectional Hausdorff; no XY profile decimation; no full manufacturing certification.'}
curve_triangles={}
for item in curves:
 o=bpy.data.objects[item['name']];e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();curve_triangles[o.name]=len(m.loop_triangles);e.to_mesh_clear()
audit['runtime_curve_triangles']=curve_triangles
(ROOT/'rim04-runtime-audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rim04-runtime.blend'),compress=True)

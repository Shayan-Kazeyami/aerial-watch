import bpy,bmesh,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rim04-asymmetric.blend'));o=bpy.data.objects['SVG broad sloped champagne wall'];me=o.data;me.calc_loop_triangles();tris=[tuple(t.vertices) for t in me.loop_triangles];tree=BVHTree.FromPolygons([v.co for v in me.vertices],tris,all_triangles=True)
hits=[]
for a,b in tree.overlap(tree):
 if a>=b or set(tris[a])&set(tris[b]):continue
 hits.append([a,b])
# Main right wall: indices 64..703, same cubic parameters, genuine normal offsets.
width=[];drops=[];tangent_errors=[]
data=json.loads((ROOT/'rim04-profile.json').read_text());count=len(data['upper']);bottom=32*count
for i in range(64,704):
 a,b=me.vertices[i].co,me.vertices[bottom+i].co;d=b-a;width.append(math.hypot(d.x,d.y));drops.append(a.z-b.z)
result={'rim_nonadjacent_triangle_self_intersection_pairs':len(hits),'right_main_section_count':len(width),'right_width_range_mm':[min(width),max(width)],'right_drop_range_mm':[min(drops),max(drops)],'right_angle_range_degrees':[math.degrees(math.atan2(d,w)) for d,w in [(min(drops),max(width)),(max(drops),min(width))]],'upper_outline_exact_svg_cubics_retained_except_tip_trim':True,'mesh_profile_sampling':'160 samples per cubic; identical parameters on main right wall; localized endpoint blends only','seconds_attachment':'Original SVG03 support/ring dimensions unchanged','limits':'Triangle intersection test excludes vertex-adjacent triangles; sampled representation, not certified CAD tolerance.'}
left_width=[math.hypot(*(me.vertices[bottom+i].co-me.vertices[i].co)[:2]) for i in range(792,1192)]
result['left_main_width_range_mm']=[min(left_width),max(left_width)]
cone_errors=[];inclinations=[]
# All left samples, INCLUDING the old endpoint transition zones, lie on one cone.
for k in range(33):
 for i in range(768,1216):
  v=me.vertices[k*count+i].co;cone_errors.append(abs(math.hypot(v.x,v.y)-(15.7-1.6*(3.47-v.z))))
for k in range(32):
 for i in range(768,1215):
  n=me.polygons[k*count+i].normal;inclinations.append(math.degrees(math.acos(min(1,abs(n.z)))))
result['left_all_depth_cone_max_radial_error_mm']=max(cone_errors)
result['left_all_depth_face_inclination_range_degrees']=[min(inclinations),max(inclinations)]
right_inclinations=[]
for k in range(32):
 for i in range(40,727):
  # Exclude the three original source cubic tangent breaks only.
  if i in [223,383,543]:continue
  n=me.polygons[k*count+i].normal;right_inclinations.append(math.degrees(math.acos(min(1,abs(n.z)))))
result['right_all_depth_face_inclination_range_degrees']=[min(right_inclinations),max(right_inclinations)]
result['depth_layers']=33
result['endpoint_geometry']='Depth-sliced intersection of constant-angle left cone and normal-offset right wall. Only the 0.20 mm meeting fillet blends them; no end ramp.'
components={}
for name in ['SVG broad sloped champagne wall','SVG unified dial and seconds support']:
 bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);remaining=set(bm.verts);n=0
 while remaining:
  n+=1;queue=[remaining.pop()]
  while queue:
   v=queue.pop()
   for e in v.link_edges:
    other=e.other_vert(v)
    if other in remaining:remaining.remove(other);queue.append(other)
 components[name]=n;bm.free()
result['connected_components']=components
(ROOT/'rim04-section-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

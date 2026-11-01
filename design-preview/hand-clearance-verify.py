"""Read actual runtime assets; verify derived premium-only depth correction. Never save assets/scenes."""
import bpy,json,math,hashlib,struct
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'rebuild/assembly.glb'));bpy.context.view_layer.update()
objects={o.get('assemblyId'):o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('assemblyId')}
def signature(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return h.hexdigest(),[list(r) for r in o.matrix_world]
source={o.name:signature(o) for o in bpy.context.scene.objects if o.type=='MESH'}
original_data={key:objects[key].data for key in ['SECONDS','SECONDS-STAFF']};lower_seat=[]
for key in original_data:
 o=objects[key];o.data=o.data.copy()
 for i,v in enumerate(o.data.vertices):
  if key=='SECONDS':v.co.z-=.32
  elif v.co.z>2.94:v.co.z=2.94+(v.co.z-2.94)*(3.68-2.94)/(4-2.94)
  else:lower_seat.append((i,tuple(v.co)))
 o.data.update()
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.get('assemblyId') not in original_data:assert signature(o)==source[o.name]
for key,me in original_data.items():
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<3d',*v.co))
 assert h.hexdigest()==source[objects[key].name][0]
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'premium-face/face-svg04.glb'));bpy.context.view_layer.update();parts=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
def coordinates(o):return [o.matrix_world@v.co for v in o.data.vertices]
def tree(o,deg=0):
 p=o.matrix_world.translation;m=Matrix.Translation(p)@Matrix.Rotation(math.radians(deg),4,'Z')@Matrix.Translation(-p)@o.matrix_world
 return BVHTree.FromPolygons([m@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
verts=[];polys=[]
for o in parts:
 offset=len(verts);verts+=coordinates(o);polys.extend(tuple(offset+i for i in p.vertices) for p in o.data.polygons)
face=BVHTree.FromPolygons(verts,polys);face_max=max(v.z for v in verts)
bounds={key:{'z':[min(v.z for v in coordinates(o)),max(v.z for v in coordinates(o))]} for key,o in objects.items() if key in ['HOUR','MINUTE','SECONDS','SECONDS-STAFF','FRONT-CRYSTAL']}
hand_face={}
for key in ['HOUR','MINUTE','SECONDS']:
 o=objects[key];hit=[];nearest=float('inf');base=coordinates(o);pivot=o.matrix_world.translation
 for deg in range(0,360,5):
  rot=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(deg),4,'Z')@Matrix.Translation(-pivot)
  if face.overlap(tree(o,deg)):hit.append(deg)
  nearest=min(nearest,min(face.find_nearest(rot@v)[3] for v in base))
 hand_face[key]={'samples':72,'collision_angles_degrees':hit,'sampled_vertex_face_distance_min_mm':nearest}
print('FACE_PASS '+json.dumps(hand_face),flush=True)
periods={'HOUR':43200,'MINUTE':3600,'SECONDS':60};pairs=[('HOUR','SECONDS'),('HOUR','SECONDS-STAFF'),('HOUR','MINUTE'),('MINUTE','SECONDS'),('MINUTE','SECONDS-STAFF')];hits={f'{a}/{b}':[] for a,b in pairs}
static_staff=tree(objects['SECONDS-STAFF']);second_trees={t:tree(objects['SECONDS'],-360*t/60) for t in [0,30]}
for t in range(0,43200,30):
 trees={key:tree(objects[key],-360*t/periods[key]) for key in ['HOUR','MINUTE']};trees['SECONDS']=second_trees[t%60];trees['SECONDS-STAFF']=static_staff
 for a,b in pairs:
  overlap=trees[a].overlap(trees[b])
  if overlap:hits[f'{a}/{b}'].append({'seconds':t,'triangle_pairs':len(overlap)})
 if t%10800==0:print('COUPLED_PROGRESS',t,flush=True)
# Continuous depth bounds: hour central hub cannot reach the seconds envelope.
hour=coordinates(objects['HOUR']);sec=coordinates(objects['SECONDS']);minute=coordinates(objects['MINUTE']);pivot=objects['SECONDS'].matrix_world.translation
sec_radius=max(math.hypot(v.x-pivot.x,v.y-pivot.y) for v in sec);seconds_inner_radial_from_main=math.hypot(pivot.x,pivot.y)-sec_radius
hour_blade_min=min(v.z for v in hour if math.hypot(v.x,v.y)>1.5);minute_blade_min=min(v.z for v in minute if math.hypot(v.x,v.y)>1.5)
sec_blade_min=min(v.z for v in sec if math.hypot(v.x-pivot.x,v.y-pivot.y)>.65)
report={'raw_asset_files_untouched':True,'raw_baseline_mesh_count':len(source),'all_non_seconds_staff_geometry_and_transforms_unchanged':True,'original_seconds_staff_buffers_unchanged':True,'correction':{'seconds_depth_translation_mm':-.32,'staff_lower_seat_fixed_to_mm':2.94,'staff_upper_height_mm':3.68,'seconds_shape_and_xy_unchanged':True},'actual_world_z_bounds_mm':bounds,'actual_face_max_z_mm':face_max,'hand_face_sweeps':hand_face,'coupled_12_hour_sweep':{'step_seconds':30,'samples':1440,'pair_collisions':hits},'continuous_separation_bounds_mm':{'hour_blade_to_seconds_top':hour_blade_min-max(v.z for v in sec),'hour_blade_to_staff_top':hour_blade_min-bounds['SECONDS-STAFF']['z'][1],'minute_entire_hand_to_seconds_top':bounds['MINUTE']['z'][0]-max(v.z for v in sec),'seconds_swept_envelope_min_radius_from_main_pivot':seconds_inner_radial_from_main,'main_hub_excluded_radius':1.5,'seconds_blade_to_highest_face':sec_blade_min-face_max,'hour_blade_to_highest_face':hour_blade_min-face_max,'minute_blade_to_highest_face':minute_blade_min-face_max,'highest_hand_to_crystal_underside':bounds['FRONT-CRYSTAL']['z'][0]-max(bounds[k]['z'][1] for k in periods)},'limits':['Hand/face distance is sampled vertex-to-triangle, not full continuous distance certification.','Positive z separation plus radial exclusion proves hour/seconds and hour/staff separation over arbitrary angles; hour/minute pair has a sampled 12-hour test only.','Intentional coaxial sleeve/hub seating retained; no manufacturing tolerance or complete gear-train certification.','Actual viewer appearance and controls require parent browser QA.']}
(R/'design-preview/hand-clearance-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('HAND_CLEARANCE_AUDIT '+json.dumps(report),flush=True)

assert all(not value['collision_angles_degrees'] for value in hand_face.values()), 'Hand/face collision'
assert all(not values for values in hits.values()), 'Coupled hand/staff collision'
assert report['continuous_separation_bounds_mm']['hour_blade_to_seconds_top'] > .029
assert report['continuous_separation_bounds_mm']['seconds_blade_to_highest_face'] > .019
assert report['continuous_separation_bounds_mm']['highest_hand_to_crystal_underside'] > .129

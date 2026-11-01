"""Derived native display variant. Retains untouched raw hand/staff objects hidden."""
import bpy,json,math,hashlib,struct,sys
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'visual-master-r01.blend'))
def sig(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return {'geometry_sha256':h.hexdigest(),'matrix':[list(r) for r in o.matrix_world],'data_name':o.data.name}
source={o.name:sig(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex'in o or o.get('assemblyId')in ['HOUR','MINUTE','SECONDS','SECONDS-STAFF'])}
originals={o.get('assemblyId'):o for o in bpy.context.scene.objects if o.get('assemblyId')in ['SECONDS','SECONDS-STAFF']};derived={};comparisons={}
for key,original in originals.items():
 o=original.copy();o.data=original.data.copy();o.name='Premium display clearance / '+original.name;bpy.context.scene.collection.objects.link(o)
 if 'assemblyId' in o:del o['assemblyId']
 o['displayAssemblyId']=key;o['derivedDisplayGeometry']=True;o['sourceObject']=original.name;o['displayCorrection']='seconds Z -0.32 mm' if key=='SECONDS' else 'staff above Z2.94 relieved to Z3.68'
 for v in o.data.vertices:
  if key=='SECONDS':v.co.z-=.32
  elif v.co.z>2.94:v.co.z=2.94+(v.co.z-2.94)*(3.68-2.94)/(4-2.94)
 o.data.update();o.hide_render=False;o.hide_set(False);original.hide_render=True;original.hide_set(True);derived[key]=o
 # Compare every vertex to exact runtime-module depth formula in native axis system.
 errors=[]
 for a,b in zip(original.data.vertices,o.data.vertices):
  expected=a.co.copy()
  if key=='SECONDS':expected.z-=.32
  elif expected.z>2.94:expected.z=2.94+(expected.z-2.94)*(3.68-2.94)/(4-2.94)
  errors.append((b.co-expected).length)
 coords=[o.matrix_world@v.co for v in o.data.vertices]
 comparisons[key]={'source':original.name,'derived':o.name,'vertices':len(o.data.vertices),'runtime_formula_max_vertex_error_mm':max(errors),'world_z_bounds_mm':[min(v.z for v in coords),max(v.z for v in coords)],'original_datablock_retained':original.data is not o.data,'material_slots_identical':[s.material for s in original.material_slots]==[s.material for s in o.material_slots]}
assert all(sig(bpy.data.objects[name])==s for name,s in source.items())
report={'source':'visual-master-r01.blend','derived':'visual-master-r02.blend','unchanged_raw_source_meshes':len(source),'original_vertices_transforms_datablocks_preserved':True,'original_seconds_and_staff_retained_hidden':True,'derived_display_comparisons':comparisons,'other_geometry_and_materials':'Unchanged; only two private mesh copies added. Raw source hand/staff hidden in render and viewport.','verification_reference':'hand-clearance-audit.json: actual runtime GLB coupled 12h, face sweeps and continuous depth bounds','limits':'Display interference correction, not manufacturing certification. Proof render uses temporary collision-example poses and isolated geometry only; saved native master retains initial poses.'}
(R/'hand-clearance-native-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('NATIVE_AUDIT '+json.dumps(report),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'visual-master-r02.blend'),compress=True)
if '--proof' not in sys.argv:raise SystemExit
# Lightweight orthographic stack proof, not a beauty render or saved pose change.
hour=next(o for o in bpy.context.scene.objects if o.get('assemblyId')=='HOUR');minute=next(o for o in bpy.context.scene.objects if o.get('assemblyId')=='MINUTE')
for o,key,period in [(hour,'HOUR',43200),(minute,'MINUTE',3600),(derived['SECONDS'],'SECONDS',60)]:o.matrix_world=o.matrix_world@Matrix.Rotation(-2*math.pi*37230/period,4,'Z')
keep=[hour,derived['SECONDS'],derived['SECONDS-STAFF']]
for o in bpy.context.scene.objects:
 if o.type in ['MESH','CURVE','FONT']:o.hide_render=o not in keep
# Proof-only solid contrasting materials make the 0.03 mm gap legible without lighting ambiguity.
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=.1;p.inputs['Roughness'].default_value=.42;return m
for o,color in [(hour,(.8,.52,.12)),(derived['SECONDS'],(.06,.3,.8)),(derived['SECONDS-STAFF'],(.35,.4,.46))]:
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat('Proof '+o.name,color))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=False;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=1000;s.render.resolution_y=380;s.render.resolution_percentage=100
s.world.color=(.12,.12,.12);s.camera.location=(-8,-16,4.1);target=Vector((-8,-1.6,3.86));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.type='ORTHO';s.camera.data.ortho_scale=6
s.render.film_transparent=False;s.render.filepath=str(R/'hand-clearance-stack-proof.png');bpy.ops.render.render(write_still=True)

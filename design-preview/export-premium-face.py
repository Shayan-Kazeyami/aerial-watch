import bpy,os,json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'design-preview/fixed-movement-cutaway-r01.blend'))
baseline=set(o.name for o in bpy.context.scene.objects)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'design-preview/approved-b-face-r02.blend'))
bpy.ops.object.select_all(action='DESELECT');parts=[]
for o in list(bpy.context.scene.objects):
 if o.name not in baseline and o.type in ['MESH','CURVE','FONT']:
  o.select_set(True);bpy.context.view_layer.objects.active=o
  if o.type!='MESH':bpy.ops.object.convert(target='MESH');o=bpy.context.object
  o['premiumFacePart']=True;o['designRevision']='B-02';parts.append(o)
# Export only authored face; underlying source mesh is never bundled or replaced.
for o in bpy.context.scene.objects:o.select_set(o in parts)
os.makedirs(os.path.join(ROOT,'premium-face'),exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'premium-face/face-b.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('EXPORTED_FACE',len(parts))

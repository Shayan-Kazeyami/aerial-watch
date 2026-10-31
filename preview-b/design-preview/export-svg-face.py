import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'svg-face-r03-materials.blend'))
bpy.ops.object.select_all(action='DESELECT');parts=[]
for o in list(bpy.context.scene.objects):
 if not o.get('premiumFacePart'):continue
 assert 'sourceIndex' not in o
 o.select_set(True);bpy.context.view_layer.objects.active=o
 if o.type!='MESH':bpy.ops.object.convert(target='MESH');o=bpy.context.object
 if any('Graphite' in m.name for m in o.data.materials if m):
  uv=o.data.uv_layers.active or o.data.uv_layers.new(name='DialPlanar')
  for loop in o.data.loops:
   world=o.matrix_world@o.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=((world.x+16.4)/32.8,(world.y+16.4)/32.8)
 parts.append(o)
for o in bpy.context.scene.objects:o.select_set(o in parts)
bpy.ops.export_scene.gltf(filepath=str(ROOT.parent/'premium-face/face-svg-b.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('SVG_FACE_EXPORTED',len(parts))

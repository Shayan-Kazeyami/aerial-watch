import bpy,json,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--scene',default='svg-face-r03-materials.blend');parser.add_argument('--output',default='premium-face/face-svg-b.glb');parser.add_argument('--revision');parser.add_argument('--studio-materials',action='store_true');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/args.scene))
if args.studio_materials:
 m=bpy.data.materials.get('Graphite dial')
 if m and m.use_nodes:
  p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.014,.016,.019,1);p.inputs['Roughness'].default_value=.48;p.inputs['Metallic'].default_value=.02
  for n in m.node_tree.nodes:
   if n.type=='BUMP':n.inputs['Strength'].default_value=.08;n.inputs['Distance'].default_value=.01
bpy.ops.object.select_all(action='DESELECT');parts=[]
for o in list(bpy.context.scene.objects):
 if not o.get('premiumFacePart'):continue
 assert 'sourceIndex' not in o
 if args.revision:o['designRevision']=args.revision
 o.select_set(True);bpy.context.view_layer.objects.active=o
 if o.type!='MESH':bpy.ops.object.convert(target='MESH');o=bpy.context.object
 if any('Graphite' in m.name for m in o.data.materials if m):
  uv=o.data.uv_layers.active or o.data.uv_layers.new(name='DialPlanar')
  for loop in o.data.loops:
   world=o.matrix_world@o.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=((world.x+16.4)/32.8,(world.y+16.4)/32.8)
 parts.append(o)
for o in bpy.context.scene.objects:o.select_set(o in parts)
bpy.ops.export_scene.gltf(filepath=str(ROOT.parent/args.output),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('SVG_FACE_EXPORTED',len(parts))

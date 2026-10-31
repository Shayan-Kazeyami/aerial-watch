import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'svg-face-r02.blend'))
graphite=bpy.data.materials['Graphite dial'];p=graphite.node_tree.nodes.get('Principled BSDF')
p.inputs['Base Color'].default_value=(.0018,.002,.0025,1);p.inputs['Metallic'].default_value=.03;p.inputs['Roughness'].default_value=.59
for n in graphite.node_tree.nodes:
 if n.type=='BUMP':n.inputs['Strength'].default_value=.46;n.inputs['Distance'].default_value=.035
# Separate the polished bezel from the satin movement finish, geometry unchanged.
bezelmat=bpy.data.materials['Satin steel'].copy();bezelmat.name='Polished bezel study';p=bezelmat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.58,.62,.67,1);p.inputs['Metallic'].default_value=1;p.inputs['Roughness'].default_value=.14
for o in bpy.context.scene.objects:
 if o.get('assemblyId')=='BEZEL':o.data.materials.clear();o.data.materials.append(bezelmat)
gold=bpy.data.materials['Muted champagne'];p=gold.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.68,.49,.28,1);p.inputs['Roughness'].default_value=.20
# Retain the same camera, scale, geometry and light placement for a fair comparison.
scene=bpy.context.scene;scene.cycles.samples=96;scene.render.resolution_x=1200;scene.render.resolution_y=1200
scene.render.filepath=str(ROOT/'svg-face-r03-materials.png');bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'svg-face-r03-materials.blend'),compress=True)
(ROOT/'svg-material-study.json').write_text(json.dumps({'revision':'B-SVG-02-material-study','changes':['Darker non-metallic charcoal and clearer micrograin','Separate polished bezel material, retaining satin movement plates','Slightly brighter champagne markers and trim'],'camera_and_geometry':'unchanged from svg-face-r01','status':'Visual candidate; not published runtime materials.'},indent=2)+'\n')
bpy.ops.render.render(write_still=True)

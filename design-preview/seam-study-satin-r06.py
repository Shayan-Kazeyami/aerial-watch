import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r05.blend'))
m=next(m for m in bpy.data.materials if m.name.startswith('Seam study / fine charcoal'))
for n in m.node_tree.nodes:
 if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.32
 if n.type=='MAP_RANGE' and abs(n.inputs['To Min'].default_value-.45)<.001:n.inputs['To Min'].default_value=.36;n.inputs['To Max'].default_value=.48
p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Specular IOR Level'].default_value=.30;p.inputs['Sheen Weight'].default_value=.13
bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r06.blend'),compress=True);s=bpy.context.scene;s.render.filepath=str(R/'seam-study-r06-macro.png');bpy.ops.render.render(write_still=True)

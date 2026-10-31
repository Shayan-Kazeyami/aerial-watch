import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-export-compatible.blend'))
for o in bpy.context.scene.objects:
 if o.get('leatherPbrRevision')=='R10':o.hide_render=True;o.hide_set(True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'seam-study-leather-r10.glb'));imported=[o for o in bpy.data.objects if o not in before]
for o in imported:o.hide_render=False;o.hide_set(False)
s=bpy.context.scene;s.cycles.samples=128;s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.filepath=str(R/'seam-study-r10-roundtrip-macro.png');bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r10-roundtrip.blend'),compress=True)
print('ROUNDTRIP_IMPORTED',[(o.name,o.type) for o in imported],flush=True)
# Render deliberately separate, so parent controls CPU scheduling.

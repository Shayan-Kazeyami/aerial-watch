import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
for scene,label in [('seam-study-r10-export-compatible.blend','compatible-reference'),('seam-study-r10-runtime-roundtrip.blend','runtime-roundtrip')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/scene));s=bpy.context.scene;s.camera.location=(18,47,7);s.camera.rotation_euler=(Vector((7.6,29,-9))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=10;s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.cycles.samples=96;s.render.threads_mode='FIXED';s.render.threads=4;s.render.filepath=str(R/('seam-study-r10-'+label+'-detail.png'));print('COMPARE_RENDER',label,flush=True);bpy.ops.render.render(write_still=True)

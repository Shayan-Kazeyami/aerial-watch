import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rim04-asymmetric.blend'));s=bpy.context.scene
s.cycles.samples=32;s.render.resolution_x=1100;s.render.resolution_y=1100
for name,target,loc,scale in [('front',(0,0,0),(0,0,80),54),('top-join',(-3.4,14.1,3.1),(2,23,35),8),('bottom-join',(-5.1,-13.6,3.1),(1,-23,35),8)]:
 if name=='front':pass
 else:s.camera.location=loc;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=scale
 s.render.filepath=str(ROOT/('rim04-'+name+'.png'));bpy.ops.render.render(write_still=True)

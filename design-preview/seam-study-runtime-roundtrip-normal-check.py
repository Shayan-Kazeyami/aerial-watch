import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
# Compare exported/imported corner-normal sets at identical local positions.
bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-runtime.blend'));native={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.get('leatherPbrRevision')!='R10':continue
 bucket={}
 for li,loop in enumerate(o.data.loops):
  pos=o.matrix_world@o.data.vertices[loop.vertex_index].co;normal=o.matrix_world.to_3x3()@o.data.corner_normals[li].vector;key=tuple(round(x,4) for x in pos);bucket.setdefault(key,[]).append(normal.normalized())
 native[(o['designPart'],o['replacesAssemblyId'])]=bucket
bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r10-runtime-roundtrip.blend'));report=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.hide_render or o.get('leatherPbrRevision')!='R10':continue
 bucket=native[(o['designPart'],o['replacesAssemblyId'])];maxangle=0;missing=0;count=0;angles=[]
 for li in range(0,len(o.data.loops),7):
  loop=o.data.loops[li];pos=o.matrix_world@o.data.vertices[loop.vertex_index].co;n=(o.matrix_world.to_3x3()@o.data.corner_normals[li].vector).normalized();key=tuple(round(x,4) for x in pos)
  if key not in bucket:missing+=1;continue
  angle=min(math.degrees(n.angle(v,0)) for v in bucket[key]);maxangle=max(maxangle,angle);angles.append(angle);count+=1
 report.append({'name':o.name,'matched_corner_samples':count,'unmatched_position_samples':missing,'maximum_matched_normal_angle_degrees':maxangle,'over_1_degree_samples':sum(a>1 for a in angles),'over_5_degree_samples':sum(a>5 for a in angles),'p99_degrees':sorted(angles)[int(len(angles)*.99)]})
(R/'seam-study-r10-roundtrip-normal-audit.json').write_text(json.dumps(report,indent=2));print(report,flush=True)

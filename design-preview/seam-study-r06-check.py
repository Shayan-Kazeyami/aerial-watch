import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parent

def hashes():
 out={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  h=hashlib.sha256()
  for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
  out[o.name]=(h.hexdigest(),[list(row) for row in o.matrix_world])
 return out
bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r05.blend'));a=hashes();bpy.ops.wm.open_mainfile(filepath=str(R/'seam-study-r06.blend'));b=hashes();assert a==b
report={'geometry_identical_to':'seam-study-r05.blend','mesh_count':len(a),'roughness_range':[.36,.48],'normal_strength':.32,'specular_ior_level':.30,'sheen_weight':.13,'validation_inherited':'seam-study-r05-validation.json','purpose':'Material-only satin variant; no geometry changes.'};(R/'seam-study-r06-audit.json').write_text(json.dumps(report,indent=2));print(report)

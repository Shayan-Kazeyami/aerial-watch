import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
for file in ['seam-study-r10-export-compatible.blend','seam-study-r10-runtime.blend','seam-study-r10-runtime-roundtrip.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(R/file));out=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or o.hide_render or not ('Seam study' in o.name):continue
  ms=[]
  for slot in o.material_slots:
   m=slot.material;p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if not p:continue
   attrs={k:list(p.inputs[k].default_value) if hasattr(p.inputs[k].default_value,'__len__') else p.inputs[k].default_value for k in ['Base Color','Metallic','Roughness','IOR','Specular IOR Level','Specular Tint','Sheen Weight','Sheen Roughness','Sheen Tint']}
   attrs['images']=[{'name':n.image.name,'cs':n.image.colorspace_settings.name,'size':list(n.image.size),'path':n.image.filepath} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image];attrs['normal_strength']=[n.inputs['Strength'].default_value for n in m.node_tree.nodes if n.type=='NORMAL_MAP'];ms.append({'name':m.name,'attrs':attrs})
  out.append({'name':o.name,'materials':ms,'vertices':len(o.data.vertices)})
 print('DIAG',file,json.dumps(out),flush=True)

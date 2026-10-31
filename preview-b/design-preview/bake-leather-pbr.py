import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;out=R.parent/'quality-study/leather-r09';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'rim-leather-r05.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.render.bake.use_clear=True;s.render.bake.margin=12
parts=[o for o in s.objects if o.type=='MESH' and o.get('designPart') in ['QUALITY-STRAP','QUALITY-STITCH']];report=[]
for o in parts:
 o['leatherPbrRevision']='R09'
 if o.get('designPart')!='QUALITY-STRAP':continue
 key=o.get('replacesAssemblyId').lower();bpy.ops.object.select_all(action='DESELECT');o.hide_render=False;o.select_set(True);bpy.context.view_layer.objects.active=o
 for slot in o.material_slots:slot.material=slot.material.copy()
 images={}
 for kind,typ in [('color','DIFFUSE'),('roughness','ROUGHNESS'),('normal','NORMAL')]:
  img=bpy.data.images.new(key+'-'+kind,1024,1024,alpha=False);img.colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color';targets=[]
  for slot in o.material_slots:
   n=slot.material.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;slot.material.node_tree.nodes.active=n;targets.append((slot.material,n))
  s.render.bake.use_pass_direct=False;s.render.bake.use_pass_indirect=False;s.render.bake.use_pass_color=True
  bpy.ops.object.bake(type=typ);img.filepath_raw=str(out/(key+'-'+kind+'.png'));img.file_format='PNG';img.save();images[kind]=img
  for m,n in targets:m.node_tree.nodes.remove(n)
 for slot in o.material_slots:
  if not slot.material.name.startswith('R09 fine photo-grain'):continue
  m=bpy.data.materials.new('fine pebble graphite calf / photo R09 / '+key);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Metallic'].default_value=0
  for kind,img in images.items():
   t=n.new('ShaderNodeTexImage');t.image=img
   if kind=='color':l.new(t.outputs['Color'],p.inputs['Base Color'])
   elif kind=='roughness':l.new(t.outputs['Color'],p.inputs['Roughness'])
   else:
    normal=n.new('ShaderNodeNormalMap');l.new(t.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],p.inputs['Normal'])
  slot.material=m
 report.append({'part':key,'maps':list(images),'resolution':1024})
for o in s.objects:o.select_set(o in parts)
bpy.ops.export_scene.gltf(filepath=str(out.parent/'leather-craft-r09.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
(out/'bake-audit.json').write_text(json.dumps({'revision':'R09','parts':report,'source':'Poly Haven Brown Leather by Rob Tuytel, CC0','status':'Native PBR baked candidate; runtime not yet integrated or verified.'},indent=2)+'\n')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'rim-leather-r06-baked.blend'),compress=True)

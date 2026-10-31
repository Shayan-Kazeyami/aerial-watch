import bpy,bmesh,math,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'svg-face-r03-materials.blend'))
svg=ET.parse(ROOT/'Aerial-Left-Crescent-B-Angled-Rim-v3.svg').getroot();wall=next(e for e in svg.iter() if e.get('id')=='angled-outer-wall')
def identity(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return (h.hexdigest(),tuple(tuple(row) for row in o.matrix_world))
source={o.name:identity(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex' in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS'])}
for o in bpy.context.scene.objects:
 if o.get('premiumFacePart'):o['designRevision']='B-SVG-03'
ro,ri,zt,zb,thickness,start,sweep=[float(wall.get('data-'+k)) for k in ['outer-radius','inner-radius','top-z','bottom-z','thickness','start-angle','sweep-angle']]
lower_element=next(e for e in svg.iter() if e.get('id')=='angled-wall-inner-edge')
lower_points=[tuple(map(float,p.split(','))) for p in lower_element.get('points').split()];widths=list(map(float,lower_element.get('data-widths').split()))
upper_curve=bpy.data.objects['SVG champagne aperture rim'];upper_points=[upper_curve.matrix_world@Vector(p.co[:3]) for p in upper_curve.data.splines[0].points]
count=len(upper_points);assert count==len(lower_points)==len(widths);taper=float(wall.get('data-taper-angle'));min_width=float(wall.get('data-min-width'));min_thickness=float(wall.get('data-min-thickness'));verts=[];profiles=[]
for i,upper in enumerate(upper_points):
 width=widths[i];blend=max(0,min(1,(width-min_width)/(ro-ri-min_width)));drop=width*(zt-zb)/(ro-ri);thick=min_thickness+(thickness-min_thickness)*blend;x,y=lower_points[i];low=(x,-y)
 verts.extend([(upper.x,upper.y,zt),(low[0],low[1],zt-drop),(low[0],low[1],zt-drop-thick),(upper.x,upper.y,zt-thick)]);profiles.append((low[0],low[1],zt-drop,blend))
faces=[]
for i in range(count):
 k=(i+1)%count
 for j in range(4):faces.append((4*i+j,4*i+(j+1)%4,4*k+(j+1)%4,4*k+j))
mesh=bpy.data.meshes.new('Sloped rim solid');mesh.from_pydata(verts,[],faces);mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
rim=bpy.data.objects.new('SVG broad sloped champagne wall',mesh);bpy.context.collection.objects.link(rim);rim['premiumFacePart']=True;rim['designRevision']='B-SVG-03';rim['rimRole']='sloped-wall'
gold=bpy.data.materials['Muted champagne'].copy();gold.name='Brushed champagne sloped wall';p=gold.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.25
if p.inputs.get('Anisotropic IOR Level'):p.inputs['Anisotropic IOR Level'].default_value=.3
rim.data.materials.append(gold)
uv=mesh.uv_layers.new(name='RimFlow')
for poly in mesh.polygons:
 poly.use_smooth=True
 for li in poly.loop_indices:
  vi=mesh.loops[li].vertex_index;uv.data[li].uv=(vi//4/(count-1),[0,1,1,0][vi%4])
if hasattr(mesh,'set_sharp_from_angle'):mesh.set_sharp_from_angle(angle=math.radians(30))
bpy.context.view_layer.objects.active=rim;bevel=rim.modifiers.new('Fine rim edge breaks','BEVEL');bevel.width=.015;bevel.segments=3;bpy.ops.object.modifier_apply(modifier=bevel.name)
curve=bpy.data.curves.new('Lower rim lip','CURVE');curve.dimensions='3D';curve.bevel_depth=.025;curve.bevel_resolution=3;curve.use_fill_caps=True;sp=curve.splines.new('POLY');sp.points.add(count-1)
for i,knot in enumerate(sp.points):
 x,y,z,blend=profiles[i];knot.co=(x,y,z,1);knot.radius=.45+.55*blend
sp.use_cyclic_u=True
lip=bpy.data.objects.new('SVG lower champagne rim lip',curve);bpy.context.collection.objects.link(lip);lip.data.materials.append(gold);lip['premiumFacePart']=True;lip['designRevision']='B-SVG-03'
# Reuse the already-authored, fitted stitch/lining/edge geometry from the viewer.
old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT.parent/'quality-study/leather-craft-r05.glb'));imported=[o for o in bpy.data.objects if o not in old]
for o in bpy.context.scene.objects:
 if o.get('assemblyId') in ['STRAP-UPPER','STRAP-LOWER']:o.hide_render=True

def leather_material(name,base,roughness,grain=True):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*base,1);p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=roughness
 if p.inputs.get('Sheen Weight'):p.inputs['Sheen Weight'].default_value=.14 if grain else .04
 if not grain:return m
 pos=n.new('ShaderNodeNewGeometry');warp=n.new('ShaderNodeTexNoise');warp.inputs['Scale'].default_value=5;warp.inputs['Detail'].default_value=2;l.new(pos.outputs['Position'],warp.inputs['Vector'])
 sub=n.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=(.5,.5,.5);l.new(warp.outputs['Color'],sub.inputs[0])
 scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=.12;l.new(sub.outputs[0],scale.inputs[0])
 add=n.new('ShaderNodeVectorMath');add.operation='ADD';l.new(pos.outputs['Position'],add.inputs[0]);l.new(scale.outputs[0],add.inputs[1])
 cell=n.new('ShaderNodeTexVoronoi');cell.feature='DISTANCE_TO_EDGE';cell.inputs['Scale'].default_value=4.5;l.new(add.outputs[0],cell.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.012;ramp.color_ramp.elements[0].color=(.25,.25,.25,1);ramp.color_ramp.elements[1].position=.10;ramp.color_ramp.elements[1].color=(.66,.66,.66,1);l.new(cell.outputs['Distance'],ramp.inputs[0])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.65;bump.inputs['Distance'].default_value=.018;l.new(ramp.outputs[0],bump.inputs['Height'])
 fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=45;fine.inputs['Detail'].default_value=2;l.new(pos.outputs['Position'],fine.inputs['Vector'])
 micro=n.new('ShaderNodeBump');micro.inputs['Strength'].default_value=.12;micro.inputs['Distance'].default_value=.006;l.new(fine.outputs['Fac'],micro.inputs['Height']);l.new(bump.outputs['Normal'],micro.inputs['Normal']);l.new(micro.outputs['Normal'],p.inputs['Normal'])
 variation=n.new('ShaderNodeMapRange');variation.inputs['From Min'].default_value=0;variation.inputs['From Max'].default_value=1;variation.inputs['To Min'].default_value=.53;variation.inputs['To Max'].default_value=.73;l.new(warp.outputs['Fac'],variation.inputs['Value']);l.new(variation.outputs['Result'],p.inputs['Roughness'])
 return m
def scanned_leather():
 m=bpy.data.materials.new('R07 scanned charcoal leather');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Metallic'].default_value=0
 pos=n.new('ShaderNodeNewGeometry');mapping=n.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=1/30;l.new(pos.outputs['Position'],mapping.inputs[0])
 if p.inputs.get('Specular IOR Level'):p.inputs['Specular IOR Level'].default_value=.27
 if p.inputs.get('Sheen Weight'):p.inputs['Sheen Weight'].default_value=.08
 def image_node(name,noncolor=False):
  node=n.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ROOT/'material-reference'/name),check_existing=True)
  if noncolor:node.image.colorspace_settings.name='Non-Color'
  node.extension='REPEAT';node.projection='BOX';node.projection_blend=.25;l.new(mapping.outputs[0],node.inputs['Vector']);return node
 color=image_node('brown_leather_albedo_1k.jpg');gray=n.new('ShaderNodeRGBToBW');l.new(color.outputs['Color'],gray.inputs[0]);tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(.16,.18,.20,1);l.new(gray.outputs[0],tint.inputs[1]);l.new(tint.outputs[0],p.inputs['Base Color'])
 rough=image_node('brown_leather_rough_1k.png',True);remap=n.new('ShaderNodeMath');remap.operation='MULTIPLY_ADD';remap.inputs[1].default_value=.7;remap.inputs[2].default_value=.15;l.new(rough.outputs['Color'],remap.inputs[0]);l.new(remap.outputs[0],p.inputs['Roughness'])
 height=image_node('brown_leather_disp_1k.png',True);nm=n.new('ShaderNodeBump');nm.inputs['Strength'].default_value=.45;nm.inputs['Distance'].default_value=.025;l.new(height.outputs['Color'],nm.inputs['Height']);l.new(nm.outputs['Normal'],p.inputs['Normal'])
 return m
materials={'leather':scanned_leather(),'lining':leather_material('R06 warm leather lining',(.12,.061,.031),.79,False),'edgepaint':leather_material('R06 burnished edge paint',(.008,.010,.012),.32,False),'thread':leather_material('R06 charcoal stitching',(.04,.035,.028),.83,False)}
roles=[]
for o in imported:
 if o.type!='MESH':continue
 o['leatherStudyRevision']='R06';roles.append({'name':o.name,'dimensions_mm':list(o.dimensions)})
 for slot in o.material_slots:
  name=slot.material.name.lower();role='lining' if 'lining' in name else 'edgepaint' if 'edge paint' in name else 'thread' if 'thread' in name else 'leather';slot.material=materials[role]
# Validate the rim as a closed solid and against visible, unchanged mechanism parts.
deps=bpy.context.evaluated_depsgraph_get()
def tree(o):
 e=o.evaluated_get(deps);me=e.to_mesh();result=BVHTree.FromPolygons([o.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons],all_triangles=False,epsilon=0);e.to_mesh_clear();return result
bm=bmesh.new();bm.from_mesh(rim.data);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free();assert nonmanifold==0
rimtree=tree(rim);collisions=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.name in source and not o.hide_render and rimtree.overlap(tree(o)):collisions.append(o.name)
assert all(identity(bpy.data.objects[name])==v for name,v in source.items());assert not collisions,collisions
report={'revision':'B-SVG-03','rim':{'outer_radius_mm':ro,'inner_radius_mm':ri,'radial_width_mm':ro-ri,'vertical_drop_mm':zt-zb,'slope_degrees':math.degrees(math.atan2(zt-zb,ro-ri)),'end_taper_degrees':math.degrees(taper),'inner_trim_width_mm':min_width,'continuous_closed_band':True,'nonmanifold_edges':nonmanifold,'visible_source_static_intersections':collisions},'source_meshes_unchanged':len(source),'leather_material_source':{'asset':'Brown Leather','author':'Rob Tuytel','url':'https://polyhaven.com/a/brown_leather','license':'CC0','adaptation':'Charcoal material tint and 30 mm triplanar repeat; source image files unchanged'},'leather_geometry':'Existing fitted R05 stitch/lining/edge geometry reused; original straps retained hidden.','imported_leather_parts':roles,'limits':'Static rim/source surface-overlap test, not dynamic clearance certification or manufacturing tolerance/strength analysis.'}
(ROOT/'rim-leather-study-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('RIM_LEATHER_AUDIT',json.dumps(report),flush=True)
scene=bpy.context.scene;scene.cycles.samples=96;scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.filepath=str(ROOT/'rim-leather-r03-front.png');bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rim-leather-r03.blend'),compress=True);bpy.ops.render.render(write_still=True)
scene.camera.location=(24,48,36);target=Vector((0,27,-2));scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=31;scene.render.filepath=str(ROOT/'rim-leather-r03-macro.png');bpy.ops.render.render(write_still=True)

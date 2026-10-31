import bpy, math, json, hashlib, struct, bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'rim-leather-r05.blend'))
def identity(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
 return [h.hexdigest(),[list(row) for row in o.matrix_world]]
source={o.name:identity(o) for o in bpy.context.scene.objects if o.type=='MESH' and ('sourceIndex' in o or o.get('assemblyId') in ['HOUR','MINUTE','SECONDS'])}
def mat(name,col,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;return m
leather=mat('Seam study / fine charcoal calf 300 mm scan',(.012,.014,.016),.54)
n=leather.node_tree.nodes;l=leather.node_tree.links;p=n.get('Principled BSDF');p.inputs['Specular IOR Level'].default_value=.28;p.inputs['Sheen Weight'].default_value=.10
uv=n.new('ShaderNodeTexCoord')
def tex(file,nc=False):
 x=n.new('ShaderNodeTexImage');x.image=bpy.data.images.load(str(R/'material-reference'/file),check_existing=True)
 if nc:x.image.colorspace_settings.name='Non-Color'
 l.new(uv.outputs['UV'],x.inputs['Vector']);return x
al=tex('leather_white_diff_4k.jpg');bw=n.new('ShaderNodeRGBToBW');l.new(al.outputs['Color'],bw.inputs[0]);mr=n.new('ShaderNodeMapRange');mr.clamp=True;mr.inputs['From Min'].default_value=.15;mr.inputs['From Max'].default_value=.8;mr.inputs['To Min'].default_value=.008;mr.inputs['To Max'].default_value=.022;l.new(bw.outputs[0],mr.inputs[0]);l.new(mr.outputs[0],p.inputs['Base Color'])
ro=tex('leather_white_rough_4k.jpg',True);rr=n.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=.43;rr.inputs['To Max'].default_value=.64;l.new(ro.outputs['Color'],rr.inputs[0]);l.new(rr.outputs[0],p.inputs['Roughness'])
no=tex('leather_white_nor_gl_4k.png',True);nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.42;l.new(no.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs[0],p.inputs['Normal'])
thread=mat('Seam study / waxed graphite three ply',(.10,.087,.067),.70);thread.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.25
edge=mat('Seam study / satin burnished edge',(.007,.008,.009),.40)
def meshob(name,verts,faces,material=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 if material:me.materials.append(material)
 for f in me.polygons:f.use_smooth=True
 o['designPart']='SEAM-STUDY';return o
# Independent UV islands each normalized to 300 mm per tile, not arbitrary packed-island size.
def scale_uv(o):
 me=o.data;uv=me.uv_layers.active.data;parent=list(range(len(me.polygons)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 edges={}
 for p in me.polygons:
  for li in p.loop_indices:
   lj=p.loop_start+(li-p.loop_start+1)%p.loop_total;a=me.loops[li].vertex_index;b=me.loops[lj].vertex_index
   key=tuple(sorted((a,b)));coords={a:tuple(uv[li].uv),b:tuple(uv[lj].uv)}
   if key in edges:
    j,co=edges[key]
    if all((Vector(coords[k])-Vector(co[k])).length<1e-5 for k in key):parent[root(p.index)]=root(j)
   else:edges[key]=(p.index,coords)
 me.calc_loop_triangles();areas={}
 for t in me.loop_triangles:
  key=root(t.polygon_index);a,b,c=[uv[i].uv for i in t.loops];area=abs((b-a).cross(c-a))*.5
  x=areas.setdefault(key,[0,0]);x[0]+=t.area;x[1]+=area
 for p in me.polygons:
  ar=areas[root(p.index)];s=math.sqrt(ar[0]/max(ar[1],1e-12))/300
  for li in p.loop_indices:uv[li].uv*=s
 return len(areas)
def tube(v,f,points,radius,sides=12):
 start=len(v)
 for i,p in enumerate(points):
  tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();a=tangent.cross(Vector((1,0,0))).normalized()
  if a.length<.1:a=tangent.cross(Vector((0,1,0))).normalized()
  b=tangent.cross(a).normalized()
  for j in range(sides):v.append(p+radius*(a*math.cos(j*math.tau/sides)+b*math.sin(j*math.tau/sides)))
 for i in range(len(points)-1):
  for j in range(sides):f.append((start+i*sides+j,start+i*sides+(j+1)%sides,start+(i+1)*sides+(j+1)%sides,start+(i+1)*sides+j))
 f.append(tuple(start+j for j in reversed(range(sides))));f.append(tuple(start+(len(points)-1)*sides+j for j in range(sides)))
def ellipsoid(v,f,c,t,n):
 start=len(v);x=t.cross(n).normalized();rings=8;sides=12
 for i in range(rings+1):
  lat=math.pi*i/rings
  for j in range(sides):
   a=j*math.tau/sides;v.append(c+x*(.14*math.sin(lat)*math.cos(a))+t*(.19*math.sin(lat)*math.sin(a))+n*(.23*math.cos(lat)))
 for i in range(rings):
  for j in range(sides):f.append((start+i*sides+j,start+i*sides+(j+1)%sides,start+(i+1)*sides+(j+1)%sides,start+(i+1)*sides+j))
reports=[]
for old in list(bpy.context.scene.objects):
 if old.type!='MESH' or old.get('designPart')!='QUALITY-STRAP':continue
 old.hide_render=True;old.hide_set(True);o=old.copy();o.data=old.data.copy();bpy.context.collection.objects.link(o);o.name='Seam study / '+old.name;o.hide_render=False;o.hide_set(False);o['designPart']='SEAM-STUDY-STRAP';isupper='Upper' in old.name
 for slot in o.material_slots:
  if 'photo-grain' in slot.material.name:slot.material=leather
  elif 'edge' in slot.material.name.lower():slot.material=edge
 islands=scale_uv(o)
 tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])
 def surf(c):
  loc,n,idx,dist=tree.find_nearest(c);return loc,n
 raw=json.loads(Path('/tmp/stitch-'+('88' if isupper else '44')+'.json').read_text());cv=[];cf=[];tv=[];tf=[];holes=0
 for sign in [-1,1]:
  centers=[Vector(a['center']) for a in raw if a['center'][0]*sign>0]
  # component order follows existing fitted path
  points=[surf(c)[0] for c in centers];norms=[surf(c)[1] for c in centers]
  dense=[]
  for i in range(len(points)-1):
   for j in range(5):
    c=points[i].lerp(points[i+1],j/5);loc,n=surf(c);dense.append(loc+n*.135)
  dense.append(points[-1]+norms[-1]*.135);tube(cv,cf,dense,.18)
  bounds=[points[0]-(points[1]-points[0])*.5]+[(a+b)*.5 for a,b in zip(points[:-1],points[1:])]+[points[-1]+(points[-1]-points[-2])*.5]
  for i,c in enumerate(bounds):
   loc,n=surf(c);t=(points[min(i,len(points)-1)]-points[max(0,i-1)]).normalized()
   if t.length<.1:t=(points[1]-points[0]).normalized()
   ellipsoid(cv,cf,loc+n*.035,t,n);holes+=1
  for i in range(len(points)):
   a,b=bounds[i],bounds[i+1];t=(b-a).normalized();side=Vector((1,0,0));a+=t*.10+side*.075;b-=t*.10+side*.075
   for strand in range(3):
    seq=[]
    for k in range(41):
     u=k/40;loc,n=surf(a.lerp(b,u));height=-.115+.205*math.sin(math.pi*u)**.50
     phase=math.tau*(3*u+strand/3);cross=t.cross(n).normalized();seq.append(loc+n*height+(cross*math.cos(phase)+n*math.sin(phase))*.043)
    tube(tv,tf,seq,.038,7)
 cutter=meshob('Seam study / recess cutters',cv,cf)
 bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter.data);bm.free()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Physical recessed seam and puncture seats','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.use_self=True;mod.object=cutter
 try:bpy.ops.object.modifier_apply(modifier=mod.name);boolean=True
 except Exception as e:print('BOOLEAN ERROR',e);boolean=False
 assert len(o.data.vertices)>1000, 'Boolean destroyed band'
 cutter.hide_render=True;cutter.hide_set(True)
 stitches=meshob('Seam study / '+('upper' if isupper else 'lower')+' waxed three-ply stitches',tv,tf,thread)
 # Fine rounding on newly cut puncture/channel edges only; no silhouette movement.
 be=o.modifiers.new('Soft leather cut edges','BEVEL');be.width=.025;be.segments=2;be.limit_method='ANGLE';be.angle_limit=.6
 reports.append({'name':o.name,'physical_uv_islands':islands,'scan_tile_mm':300,'puncture_count':holes,'thread_ply_count':3,'thread_envelope_diameter_mm':.162,'channel_depth_mm':.045,'boolean_applied':boolean,'vertices':len(o.data.vertices)})
for o in bpy.context.scene.objects:
 if o.get('designPart')=='QUALITY-STITCH':o.hide_render=True;o.hide_set(True)
assert all(identity(bpy.data.objects[k])==v for k,v in source.items())
s=bpy.context.scene;s.cycles.samples=128;s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.camera.location=(24,48,36);target=Vector((0,27,-2));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=31
(R/'seam-study-audit.json').write_text(json.dumps({'straps':reports,'source_meshes_unchanged':len(source),'limits':'Decorative static sewn anatomy. No manufacturing or dynamic clearance certification.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'seam-study-r02.blend'),compress=True);s.render.filepath=str(R/'seam-study-r02-macro.png');bpy.ops.render.render(write_still=True)
